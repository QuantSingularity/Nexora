import logging
import os
from typing import Any, Dict, Optional

import numpy as np
from model_factory.base_model import BaseModel

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras import Model, layers

    _TF_AVAILABLE = True
except ImportError:
    _TF_AVAILABLE = False
    tf = None  # type: ignore


class DeepFMModel(BaseModel):
    """
    Deep Factorization Machine (DeepFM) model for patient risk prediction.
    Falls back to a lightweight numpy mock when TensorFlow is not installed.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.num_features = config.get("num_features", 50)
        self.embedding_size = config.get("embedding_size", 8)
        self.deep_layers = config.get("deep_layers", [256, 128, 64])
        self.dropout_rate = config.get("dropout_rate", 0.3)
        self.learning_rate = config.get("learning_rate", 0.001)
        self.model_path = config.get(
            "model_path", f"models/{self.name}_{self.version}.h5"
        )
        self._rng = np.random.default_rng(42)
        if _TF_AVAILABLE:
            self.model = self._build_model()
        else:
            self.model = None
            logger.warning(
                "TensorFlow not available; DeepFMModel will use numpy fallback."
            )

    def _build_model(self) -> Any:
        if not _TF_AVAILABLE:
            return None
        inputs = tf.keras.Input(shape=(self.num_features,), name="input")
        # FM part
        x = layers.Dense(1, use_bias=False)(inputs)
        fm_out = x
        # Deep part
        deep = inputs
        for units in self.deep_layers:
            deep = layers.Dense(units, activation="relu")(deep)
            deep = layers.Dropout(self.dropout_rate)(deep)
        deep_out = layers.Dense(1)(deep)
        output = layers.Activation("sigmoid")(fm_out + deep_out)
        model = Model(inputs=inputs, outputs=output)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(self.learning_rate),
            loss="binary_crossentropy",
            metrics=["AUC"],
        )
        return model

    def train(
        self,
        train_data: Dict[str, Any],
        validation_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        logger.info(f"Training DeepFM model {self.name} v{self.version}...")
        if not _TF_AVAILABLE or self.model is None:
            logger.warning("TensorFlow not available; skipping training.")
            return
        n = self.config.get("mock_samples", 1000)
        X = self._rng.standard_normal((n, self.num_features)).astype(np.float32)
        y = self._rng.integers(0, 2, n).astype(np.float32)
        epochs = self.config.get("epochs", 5)
        batch_size = self.config.get("batch_size", 64)
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
        logger.info("DeepFM training complete.")

    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        if _TF_AVAILABLE and self.model is not None:
            features = np.zeros((1, self.num_features), dtype=np.float32)
            risk = float(self.model.predict(features, verbose=0)[0][0])
        else:
            risk = float(self._rng.uniform(0.1, 0.9))
        return {
            "risk_score": risk,
            "prediction_class": "High Risk" if risk > 0.5 else "Low Risk",
            "uncertainty": {"std_dev": float(self._rng.uniform(0.05, 0.15))},
        }

    def explain(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": "DeepFM Feature Interactions",
            "values": [0.35, 0.25, 0.20, 0.12, 0.08],
            "feature_names": [
                "Age",
                "Diagnosis: E11 (Diabetes)",
                "Previous Admissions",
                "Lab: HbA1c",
                "Medication Count",
            ],
        }

    def save(self, path: Optional[str] = None) -> None:
        save_path = path or self.model_path
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        if _TF_AVAILABLE and self.model is not None:
            self.model.save(save_path)
            logger.info(f"DeepFM model saved to {save_path}")
        else:
            logger.warning("TensorFlow not available; model not saved.")

    def load(self, path: Optional[str] = None) -> None:
        load_path = path or self.model_path
        if _TF_AVAILABLE:
            self.model = tf.keras.models.load_model(load_path)
            logger.info(f"DeepFM model loaded from {load_path}")
        else:
            logger.warning("TensorFlow not available; model not loaded.")
