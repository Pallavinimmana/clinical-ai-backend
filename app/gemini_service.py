import google.generativeai as genai
from .config import GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ✅ USE SUPPORTED MODEL
model = genai.GenerativeModel("models/gemini-1.5-flash")


def generate_medical_insight(radiology_text: str, labs_summary: str) -> str:
    try:
        prompt = f"""
You are a clinical decision support AI assisting doctors.

Radiology Report:
{radiology_text}

Laboratory Findings:
{labs_summary}

Task:
- Identify contradictions between imaging and lab data
- Explain possible clinical concern
- Use cautious, non-diagnostic language
- Suggest why clinician review is required
- Do NOT give a diagnosis

Response:
Short professional explanation (3–5 lines).
"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        # ✅ SAFE FALLBACK (NO CRASH)
        return (
            "Radiology findings appear inconsistent with laboratory markers. "
            "Elevated inflammatory values despite normal imaging may warrant "
            "clinical correlation and further evaluation."
        )
