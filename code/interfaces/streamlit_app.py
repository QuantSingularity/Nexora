"""
Nexora Clinician Dashboard - Streamlit Application

Provides a web-based interface for clinicians to review patient summaries,
run predictions, and view monitoring metrics.
"""

import os

import requests
import streamlit as st

NEXORA_API_URL = os.environ.get("NEXORA_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Nexora Clinical Decision Support",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Nexora Clinical Decision Support")
st.caption("AI-powered clinical prediction and decision support platform")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    api_url = st.text_input("API URL", value=NEXORA_API_URL)

    st.subheader("API Status")
    try:
        resp = requests.get(f"{api_url}/health", timeout=5)
        if resp.ok:
            st.success("API Online ✅")
        else:
            st.error(f"API Error: {resp.status_code}")
    except Exception:
        st.error("API Unreachable ❌")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_predict, tab_models, tab_about = st.tabs(["🔮 Predict", "📋 Models", "ℹ️ About"])

# ── Prediction Tab ────────────────────────────────────────────────────────────
with tab_predict:
    st.header("Patient Risk Prediction")
    col1, col2 = st.columns(2)

    with col1:
        patient_id = st.text_input("Patient ID", value="patient_001")
        model_name = st.selectbox(
            "Model", ["deep_fm", "transformer_model", "survival_analysis"]
        )
        model_version = st.text_input(
            "Model Version (leave blank for latest)", value=""
        )

    with col2:
        st.subheader("Demographics")
        age = st.number_input("Age", min_value=0, max_value=120, value=65)
        gender = st.selectbox("Gender", ["male", "female", "other"])

    icd_code = st.text_input("Primary ICD-10 Code", value="I10")

    if st.button("Run Prediction", type="primary"):
        payload = {
            "model_name": model_name,
            "model_version": model_version or None,
            "patient_data": {
                "patient_id": patient_id,
                "demographics": {"age": age, "gender": gender},
                "clinical_events": [
                    {
                        "type": "diagnosis",
                        "date": "2024-01-01",
                        "code": icd_code,
                        "description": f"Diagnosis {icd_code}",
                    }
                ],
            },
        }
        with st.spinner("Running prediction…"):
            try:
                resp = requests.post(f"{api_url}/predict", json=payload, timeout=30)
                if resp.ok:
                    result = resp.json()
                    st.success("Prediction complete")
                    predictions = result.get("predictions", {})
                    risk = predictions.get("risk_score", None)
                    pred_class = predictions.get("prediction_class", "Unknown")

                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric(
                        "Risk Score", f"{risk:.2f}" if risk is not None else "N/A"
                    )
                    metric_col2.metric("Classification", pred_class)
                    metric_col3.metric(
                        "Model Version", result.get("model_version", "-")
                    )

                    with st.expander("Full Response"):
                        st.json(result)
                else:
                    st.error(f"Prediction failed: {resp.status_code} – {resp.text}")
            except Exception as e:
                st.error(f"Request error: {e}")

# ── Models Tab ────────────────────────────────────────────────────────────────
with tab_models:
    st.header("Registered Models")
    if st.button("Refresh Model List"):
        try:
            resp = requests.get(f"{api_url}/models", timeout=10)
            if resp.ok:
                models = resp.json().get("models", {})
                if models:
                    for name, versions in models.items():
                        with st.expander(f"📦 {name}"):
                            st.json(versions)
                else:
                    st.info("No models registered.")
            else:
                st.error(f"Failed to fetch models: {resp.status_code}")
        except Exception as e:
            st.error(f"Request error: {e}")

# ── About Tab ─────────────────────────────────────────────────────────────────
with tab_about:
    st.header("About Nexora")
    st.markdown(
        """
        **Nexora** is a HIPAA-compliant clinical AI platform providing:

        - 🤖 **Multi-model inference** — DeepFM, Transformer, Cox Survival
        - 🔒 **HIPAA compliance** — PHI de-identification and audit logging
        - 📊 **Fairness monitoring** — Demographic parity and equal opportunity metrics
        - 🔄 **Concept drift detection** — Real-time distribution monitoring
        - 🏥 **FHIR integration** — Native HL7 FHIR R4 support

        ### Architecture
        | Component | Technology |
        |-----------|-----------|
        | REST API | FastAPI + Uvicorn |
        | gRPC Server | gRPC + Python |
        | UI | Streamlit |
        | Audit Logging | SQLite |
        | Data Pipeline | Apache Beam |
        | Models | TensorFlow, PyTorch, Lifelines |
        """
    )
