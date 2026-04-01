"""
Test suite for the HIPAA-compliant readmission prediction pipeline.

This module contains tests for both functionality and compliance
of the readmission prediction pipeline.
"""

import os
import sys
import unittest
from typing import Any

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from data_pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig,
    PHIDeidentifier,
)
from data_pipeline.hipaa_compliance.phi_detector import PHIDetector


class MockHIPAACompliantHealthcareETL:
    """A mock ETL class that simulates the de-identification step."""

    def __init__(self, deidentifier: Any) -> None:
        self.deidentifier = deidentifier

    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Simulates the ETL process, focusing on de-identification."""
        deidentified_data = self.deidentifier.deidentify_dataframe(
            data,
            patient_id_col="patient_id",
            phi_cols=[
                "name",
                "dob",
                "ssn",
                "address",
                "phone",
                "email",
                "admission_date",
                "discharge_date",
            ],
        )
        return deidentified_data


class TestHIPAACompliance(unittest.TestCase):
    """Test HIPAA compliance of the de-identification module."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_data = pd.DataFrame(
            {
                "patient_id": ["P001", "P002", "P003", "P004", "P005"],
                "name": [
                    "John Smith",
                    "Jane Doe",
                    "Robert Johnson",
                    "Emily Wilson",
                    "Michael Brown",
                ],
                "dob": [
                    "1980-05-15",
                    "1975-10-22",
                    "1990-03-08",
                    "1988-12-30",
                    "1965-07-17",
                ],
                "ssn": [
                    "123-45-6789",
                    "234-56-7890",
                    "345-67-8901",
                    "456-78-9012",
                    "567-89-0123",
                ],
                "address": [
                    "123 Main St, Boston, MA 02108",
                    "456 Oak Ave, Chicago, IL 60601",
                    "789 Pine Rd, Houston, TX 77001",
                    "321 Elm St, Phoenix, AZ 85001",
                    "654 Maple Dr, Philadelphia, PA 19101",
                ],
                "phone": [
                    "617-555-0101",
                    "312-555-0102",
                    "713-555-0103",
                    "602-555-0104",
                    "215-555-0105",
                ],
                "email": [
                    "john.smith@email.com",
                    "jane.doe@email.com",
                    "robert.j@email.com",
                    "emily.w@email.com",
                    "michael.b@email.com",
                ],
                "admission_date": [
                    "2024-01-15",
                    "2024-02-20",
                    "2024-03-10",
                    "2024-04-05",
                    "2024-05-12",
                ],
                "discharge_date": [
                    "2024-01-20",
                    "2024-02-25",
                    "2024-03-15",
                    "2024-04-10",
                    "2024-05-17",
                ],
                "diagnosis": ["I10", "E11", "J44", "I50", "N18"],
                "readmission_risk": [0.3, 0.7, 0.5, 0.8, 0.2],
            }
        )
        self.config = DeidentificationConfig()
        self.deidentifier = PHIDeidentifier(config=self.config)

    def test_deidentification_removes_phi(self) -> None:
        """Test that de-identification removes PHI columns."""
        deidentified = self.deidentifier.deidentify_dataframe(
            self.sample_data,
            patient_id_col="patient_id",
            phi_cols=["name", "dob", "ssn", "address", "phone", "email"],
        )
        self.assertNotIn("name", deidentified.columns)
        self.assertNotIn("ssn", deidentified.columns)
        self.assertIn("patient_id", deidentified.columns)

    def test_phi_detector_finds_phi(self) -> None:
        """Test that PHI detector identifies PHI fields."""
        detector = PHIDetector()
        report = detector.generate_phi_report(self.sample_data)
        self.assertIn("summary", report)
        self.assertGreater(report["summary"]["phi_columns"], 0)

    def test_mock_etl_deidentifies(self) -> None:
        """Test MockHIPAACompliantHealthcareETL de-identifies correctly."""
        etl = MockHIPAACompliantHealthcareETL(self.deidentifier)
        result = etl.process_data(self.sample_data)
        self.assertNotIn("name", result.columns)
        self.assertIn("diagnosis", result.columns)


if __name__ == "__main__":
    unittest.main()
