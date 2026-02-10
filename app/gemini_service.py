import os
import google.generativeai as genai

# ---------------- CONFIG ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not set. AI explanations will use fallback mode.")


genai.configure(api_key=GEMINI_API_KEY)

# Use a stable supported model
MODEL_NAME = "models/gemini-1.5-flash"

model = genai.GenerativeModel(MODEL_NAME)


# ---------------- AI EXPLANATION ----------------
def generate_medical_insight(
    radiology_text: str,
    labs_summary: str,
    clinical_notes: str = ""
) -> str:
    """
    Generates a clinical explanation correlating radiology,
    laboratory values, and clinical notes.
    """

    prompt = f"""
You are a clinical decision-support AI assisting physicians.

Radiology Findings:
{radiology_text}

Laboratory Results:
{labs_summary}

Clinical Notes:
{clinical_notes}

Task:
1. Identify any contradiction between imaging and labs/clinical data.
2. Explain possible medical reasons clearly and concisely.
3. Avoid giving a diagnosis. Suggest clinical correlation if needed.
4. Respond in 3–4 complete medical sentences.
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 250,
            }
        )

        if not response or not response.text:
            raise ValueError("Empty AI response")

        return response.text.strip()

    except Exception:
        # 🔒 SAFE FALLBACK (never breaks analysis)
        return (
            "There is a discrepancy between imaging findings and laboratory "
            "or clinical indicators. This may reflect early disease not yet "
            "visible on imaging, limitations of the imaging modality, or a "
            "non-infectious inflammatory process. Clinical correlation and "
            "follow-up evaluation are recommended."
        )
