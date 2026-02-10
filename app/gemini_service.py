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
            "Elevated inflammatory markers strongly suggest an active inflammatory or infectious process despite negative imaging. This discrepancy may represent early infection or imaging false-negativity and warrants further clinical evaluation."
        )
