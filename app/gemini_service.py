import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-flash")

def generate_medical_insight(
    radiology_text: str,
    labs_summary: str,
    clinical_notes: str = ""
):
    try:
        prompt = f"""
You are a clinical decision support AI.

Radiology Findings:
{radiology_text}

Laboratory Results:
{labs_summary}

Clinical Notes:
{clinical_notes}

Explain any possible discrepancy in simple clinical terms.
"""
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        # 🔒 NEVER crash analysis
        return (
            "AI explanation unavailable at the moment. "
            "Clinical correlation is advised."
        )
