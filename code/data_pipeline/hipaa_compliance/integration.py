"""
Integration module for HIPAA compliance in the clinical data pipeline.

This module provides utilities for integrating HIPAA-compliant
de-identification into the existing clinical data pipeline.
"""

import logging
from typing import Any, Dict, List, Optional

import apache_beam as beam
from data_pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig,
    PHIDeidentifier,
)
from data_pipeline.hipaa_compliance.phi_detector import PHIDetector

logger = logging.getLogger(__name__)


class DeidentifyFHIRDoFn(beam.DoFn):
    """
    Apache Beam DoFn for de-identifying FHIR bundles.
    """

    def __init__(self, config: Optional[DeidentificationConfig] = None) -> None:
        self.config = config if config else DeidentificationConfig()

    def setup(self) -> None:
        """Set up the DoFn."""
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element: Any):
        """
        Process a FHIR bundle.

        Args:
            element: FHIR bundle to de-identify

        Yields:
            De-identified FHIR bundle
        """
        try:
            deidentified = self.deidentifier.deidentify_fhir_bundle(element)
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying FHIR bundle: {e}")
            yield element


class DeidentifyDataFrameDoFn(beam.DoFn):
    """
    Apache Beam DoFn for de-identifying pandas DataFrames.
    """

    def __init__(
        self,
        config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ) -> None:
        self.config = config if config else DeidentificationConfig()
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def setup(self) -> None:
        """Set up the DoFn."""
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element: Any):
        """
        Process a pandas DataFrame.

        Args:
            element: DataFrame to de-identify

        Yields:
            De-identified DataFrame
        """
        try:
            deidentified = self.deidentifier.deidentify_dataframe(
                element, patient_id_col=self.patient_id_col, phi_cols=self.phi_cols
            )
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying DataFrame: {e}")
            yield element


class HIPAACompliantHealthcareETL(beam.PTransform):
    """
    HIPAA-compliant version of the HealthcareETL PTransform.

    This transform adds de-identification steps to the original ETL pipeline.
    """

    def __init__(
        self,
        pipeline_config: Dict[str, Any],
        deidentification_config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.pipeline_config = pipeline_config
        self.deidentification_config = (
            deidentification_config
            if deidentification_config
            else DeidentificationConfig()
        )
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def expand(self, pcoll: Any) -> Any:
        return (
            pcoll
            | "DeidentifyFHIR"
            >> beam.ParDo(DeidentifyFHIRDoFn(self.deidentification_config))
            | "DeidentifyFeatures"
            >> beam.ParDo(
                DeidentifyDataFrameDoFn(
                    self.deidentification_config, self.patient_id_col, self.phi_cols
                )
            )
        )


def create_hipaa_compliant_etl(
    pipeline_config: Optional[Dict[str, Any]] = None,
    deidentification_config: Optional[DeidentificationConfig] = None,
    patient_id_col: Optional[str] = None,
    phi_cols: Optional[List[str]] = None,
) -> HIPAACompliantHealthcareETL:
    """
    Create a HIPAA-compliant ETL pipeline.

    Args:
        pipeline_config: Pipeline configuration dictionary
        deidentification_config: Configuration for de-identification
        patient_id_col: Column name for patient ID
        phi_cols: List of column names containing PHI

    Returns:
        HIPAA-compliant ETL pipeline
    """
    cfg = pipeline_config or {
        "coding_systems": ["ICD10", "SNOMED-CT", "LOINC"],
        "feature_store": "nexora_feature_store",
        "entity_map": {"patient_id": "patient"},
    }
    return HIPAACompliantHealthcareETL(
        pipeline_config=cfg,
        deidentification_config=deidentification_config,
        patient_id_col=patient_id_col,
        phi_cols=phi_cols,
    )


def detect_phi_in_pipeline_data(data_sample: Any) -> Dict[str, Any]:
    """
    Detect PHI in pipeline data.

    Args:
        data_sample: Sample data to analyze

    Returns:
        PHI detection report
    """
    detector = PHIDetector()
    return detector.generate_phi_report(data_sample)
