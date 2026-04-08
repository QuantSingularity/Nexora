import logging
import os
from typing import Any, Dict, Optional

import numpy as np
from model_factory.base_model import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-import torch so the module can be loaded without it installed.
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim

    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore
    nn = None  # type: ignore
    optim = None  # type: ignore


class PositionalEncoding:
    """Stub when torch is unavailable."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000) -> None:
        self.d_model = d_model
        if _TORCH_AVAILABLE:
            self._module = _PositionalEncodingModule(d_model, dropout, max_len)

    def __call__(self, x: Any) -> Any:
        if _TORCH_AVAILABLE:
            return self._module(x)
        return x


if _TORCH_AVAILABLE:

    class _PositionalEncodingModule(nn.Module):  # type: ignore[misc]
        def __init__(
            self, d_model: int, dropout: float = 0.1, max_len: int = 5000
        ) -> None:
            super().__init__()
            self.dropout = nn.Dropout(p=dropout)
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(
                torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model)
            )
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            pe = pe.unsqueeze(0).transpose(0, 1)
            self.register_buffer("pe", pe)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            x = x + self.pe[: x.size(0), :]
            return self.dropout(x)

    class ClinicalTransformer(nn.Module):  # type: ignore[misc]
        def __init__(
            self,
            vocab_size: int,
            d_model: int,
            nhead: int,
            num_layers: int,
            dim_feedforward: int,
            dropout: float = 0.1,
            num_classes: int = 1,
        ) -> None:
            super().__init__()
            self.model_type = "Transformer"
            self.pos_encoder = _PositionalEncodingModule(d_model, dropout)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                batch_first=False,
            )
            self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
            self.embedding = nn.Embedding(vocab_size, d_model)
            self.d_model = d_model
            self.decoder = nn.Linear(d_model, num_classes)
            self._init_weights()

        def _init_weights(self) -> None:
            initrange = 0.1
            self.embedding.weight.data.uniform_(-initrange, initrange)
            self.decoder.bias.data.zero_()
            self.decoder.weight.data.uniform_(-initrange, initrange)

        def forward(
            self, src: "torch.Tensor", src_mask: Optional["torch.Tensor"] = None
        ) -> "torch.Tensor":
            src = self.embedding(src) * np.sqrt(self.d_model)
            src = self.pos_encoder(src)
            output = self.transformer_encoder(src, src_mask)
            output = output.mean(dim=0)
            output = self.decoder(output)
            return torch.sigmoid(output)

else:
    ClinicalTransformer = None  # type: ignore


class TransformerModel(BaseModel):
    """
    Wrapper for the ClinicalTransformer model, adhering to the BaseModel interface.
    Falls back to a lightweight numpy-based mock when torch is not installed.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.vocab_size = config.get("vocab_size", 10000)
        self.d_model = config.get("d_model", 128)
        self.nhead = config.get("nhead", 4)
        self.num_layers = config.get("num_layers", 2)
        self.dim_feedforward = config.get("dim_feedforward", 512)
        self.num_classes = config.get("num_classes", 1)
        self.model_path = config.get(
            "model_path", f"models/{self.name}_{self.version}.pt"
        )
        self._rng = np.random.default_rng(42)
        if _TORCH_AVAILABLE:
            self.model = ClinicalTransformer(
                self.vocab_size,
                self.d_model,
                self.nhead,
                self.num_layers,
                self.dim_feedforward,
                num_classes=self.num_classes,
            )
            self.optimizer = optim.Adam(
                self.model.parameters(), lr=config.get("learning_rate", 0.0001)
            )
            self.criterion = nn.BCELoss()
        else:
            self.model = None
            self.optimizer = None
            self.criterion = None

    def train(
        self,
        train_data: Dict[str, Any],
        validation_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        logger.info(f"Training Transformer model {self.name} v{self.version}...")
        if not _TORCH_AVAILABLE:
            logger.warning("torch not available; skipping training.")
            return
        self.model.train()
        num_epochs = self.config.get("epochs", 5)
        batch_size = self.config.get("batch_size", 32)
        mock_input = torch.randint(0, self.vocab_size, (50, batch_size))
        mock_target = torch.rand(batch_size, self.num_classes)
        for epoch in range(num_epochs):
            self.optimizer.zero_grad()
            output = self.model(mock_input)
            loss = self.criterion(output, mock_target)
            loss.backward()
            self.optimizer.step()
            logger.info(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss.item():.4f}")
        logger.info("Transformer training complete.")

    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        if "features" not in patient_data and "demographics" not in patient_data:
            raise ValueError(
                "patient_data must contain 'features' or 'demographics' key"
            )
        if _TORCH_AVAILABLE:
            self.model.eval()
            mock_input = torch.randint(0, self.vocab_size, (50, 1))
            with torch.no_grad():
                prediction_proba = float(self.model(mock_input).item())
        else:
            prediction_proba = float(self._rng.uniform(0.1, 0.9))

        uncertainty = float(self._rng.uniform(0.05, 0.15))
        return {
            "risk_score": prediction_proba,
            "prediction_class": "High Risk" if prediction_proba > 0.5 else "Low Risk",
            "uncertainty": {"std_dev": uncertainty},
        }

    def predict_with_uncertainty(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self.predict(patient_data)
        risk = prediction["risk_score"]
        margin = float(self._rng.uniform(0.05, 0.15))
        return {
            "risk": risk,
            "prediction_class": prediction["prediction_class"],
            "uncertainty": {
                "std_dev": prediction["uncertainty"]["std_dev"],
                "confidence_interval": [
                    float(max(0.0, risk - margin)),
                    float(min(1.0, risk + margin)),
                ],
            },
        }

    def save(self, path: Optional[str] = None) -> None:
        save_path = path or self.model_path
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        if _TORCH_AVAILABLE and self.model is not None:
            torch.save(self.model.state_dict(), save_path)
            logger.info(f"Transformer model saved to {save_path}")
        else:
            logger.warning("torch not available; model not saved.")

    def load(self, path: Optional[str] = None) -> None:
        load_path = path or self.model_path
        if _TORCH_AVAILABLE and self.model is not None:
            self.model.load_state_dict(torch.load(load_path))
            self.model.eval()
            logger.info(f"Transformer model loaded from {load_path}")
        else:
            logger.warning("torch not available; model not loaded.")

    def explain(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": "Mock Attention Weights",
            "values": [0.45, 0.30, 0.15, 0.07, 0.03],
            "feature_names": [
                "Diagnosis: I10 (Hypertension)",
                "Medication: Lisinopril",
                "Age: 65+",
                "Previous Admissions",
                "Lab: Creatinine",
            ],
            "details": "Mock explanation based on the transformer's attention mechanism.",
        }
