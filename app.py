import streamlit as st
from google import genai
# Configure Gemini client (API key stored in Streamlit secrets)
GEMINI_API_KEY = st.secrets.get("AIzaSyDVl40ikBBx9ZWJJmvRXGiVYyzsUOBjp90")

gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# -------------------------
# Simple rule-based knowledge
# -------------------------

SYMPTOM_RULES = {
    "fever": {
        "keywords": ["fever", "temperature", "high temperature", "hot body"],
        "issue": "Possible Fever / Infection",
        "risk": "Medium",
        "advice": [
            "Drink plenty of clean water and ORS if feeling weak.",
            "Take rest and avoid heavy work.",
            "You may take paracetamol as per dosage on the strip (if not allergic)."
        ],
        "doctor_when": [
            "Fever continues for more than 3 days.",
            "Very high fever with confusion or fits.",
            "Difficulty in breathing or chest pain with fever."
        ]
    },
    "diarrhea": {
        "keywords": ["loose motion", "diarrhea", "watery stool", "loose stools"],
        "issue": "Possible Diarrhea",
        "risk": "Medium",
        "advice": [
            "Drink ORS frequently to prevent dehydration.",
            "Avoid street food, oily food and milk products.",
            "Eat light food like rice, banana and curd."
        ],
        "doctor_when": [
            "Blood in stool.",
            "No urine for more than 6 hours.",
            "Very weak, dizzy or fainting."
        ]
    },
    "cough_cold": {
        "keywords": ["cough", "cold", "running nose", "runny nose", "sneezing"],
        "issue": "Common Cold / Cough",
        "risk": "Low to Medium",
        "advice": [
            "Drink warm water and avoid chilled drinks.",
            "Steam inhalation can reduce nose block and cough.",
            "Avoid dust and smoking area."
        ],
        "doctor_when": [
            "Cough for more than 2 weeks.",
            "Cough with blood.",
            "Severe breathing difficulty or chest pain."
        ]
    },
    "headache": {
        "keywords": ["headache", "head pain", "head is paining"],
        "issue": "Headache",
        "risk": "Low to Medium",
        "advice": [
            "Take rest in a quiet, dark room.",
            "Drink water; dehydration can cause headache.",
            "Avoid looking at mobile / screen for long time."
        ],
        "doctor_when": [
            "Very severe sudden headache.",
            "Headache with vomiting, weakness, or confusion.",
            "Headache after head injury."
        ]
    },
    "stomach_pain": {
        "keywords": ["stomach pain", "abdominal pain", "tummy pain", "belly pain"],
        "issue": "Stomach Pain",
        "risk": "Depends on cause",
        "advice": [
            "Avoid spicy, oily and street food.",
            "Drink clean water; avoid drinking unboiled water.",
            "Eat small, light meals."
        ],
        "doctor_when": [
            "Severe pain that does not improve.",
            "Pain with vomiting, blood in stool or black stool.",
            "Pain with high fever or unable to stand straight."
        ]
    }
}


def analyze_symptoms(text: str):
    """
    Very simple keyword-based matching.
    Returns list of matched conditions and overall risk.
    """
    text_lower = text.lower()
    matched = []

    risk_order = {"Low": 1, "Low to Medium": 2, "Medium": 3, "High": 4}

    overall_risk_value = 0

    for key, info in SYMPTOM_RULES.items():
        for kw in info["keywords"]:
            if kw in text_lower:
                matched.append(info)
                risk_val = risk_order.get(info["risk"], 1)
                overall_risk_value = max(overall_risk_value, risk_val)
                break  # avoid duplicate match for same condition

    inv_risk_order = {1: "Low", 2: "Low to Medium", 3: "Medium", 4: "High"}
    overall_risk = inv_risk_order.get(overall_risk_value, "Unknown")

    return matched, overall_risk


def build_structured_summary(user_text, matched_conditions, overall_risk):
    lines = []
    lines.append(f"User description: {user_text}")
    lines.append(f"Overall concern level: {overall_risk}")
    for cond in matched_conditions:
        lines.append(f"- Possible issue: {cond['issue']} (risk: {cond['risk']})")
        lines.append("  Self-care steps:")
        for a in cond["advice"]:
            lines.append(f"    * {a}")
        lines.append("  See a doctor if:")
        for w in cond["doctor_when"]:
            lines.append(f"    * {w}")
    return "\n".join(lines)


def gemini_explanation(user_text, matched_conditions, overall_risk):
    """
    Use Gemini to explain the situation in simple, friendly language.
    We keep it SAFE: no diagnosis, no prescriptions.
    """
    if gemini_client is None or not matched_conditions:
        return None

    summary = build_structured_summary(user_text, matched_conditions, overall_risk)

    prompt = f"""
You are a helpful health information assistant for people in rural India.
You are NOT a doctor and must NOT give a medical diagnosis or prescribe medicines.

I will give you:
1) What the user typed
2) A structured summary with possible common issues, self-care steps, and warning signs.

Your job:
- Explain this in very simple Indian English.
- Keep it short and calm.
- Mention only general self-care like rest, hydration, light food, cleanliness, etc.
- Do NOT guess disease names beyond very common words like 'fever', 'cold', 'loose motion'.
- Do NOT invent new medicines. You may mention 'paracetamol' only if it is already in the summary.
- Always end with: "Please visit a nearby doctor or hospital if you are worried or if symptoms get worse."

Here is the structured summary:

{summary}
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        # In case of any API error, fail silently and just not show extra explanation
        return None
# -------------------------
# Streamlit UI
# -------------------------
st.title("🩺 RuralCare AI")
st.write(
    "A simple health guidance helper for basic symptoms.\n\n"
    "<span style='color:red; font-weight:bold;'>Important:</span> "
    "<b>This is not a doctor. In an emergency, go to the nearest hospital immediately.</b>",
    unsafe_allow_html=True,
)
st.set_page_config(page_title="RuralCare AI", page_icon="🩺", layout="centered")

st.title("RuralCare AI 🩺")
st.write(
    "A simple health guidance helper for basic symptoms.\n\n"
    "**⚠️ Important:** This is *not* a doctor. "
    "In case of emergency, go to the nearest hospital immediately."
)

st.markdown("---")

st.subheader("Describe your problem")

st.write("Example: `I have fever and loose motion from yesterday`")

user_input = st.text_area("Type your symptoms in simple words:", height=150)

if st.button("Get Guidance"):
    if not user_input.strip():
        st.warning("Please type your symptoms first.")
    else:
        matched_conditions, overall_risk = analyze_symptoms(user_input)

        if not matched_conditions:
            st.error(
                "Sorry, I could not clearly understand the problem from your words.\n\n"
                "Try using simple words like **fever, loose motion, cough, cold, headache, stomach pain**."
            )
        else:
            # Color based on risk
            if overall_risk in ["Low", "Low to Medium"]:
                st.success(f"Overall concern level: **{overall_risk}**")
            elif overall_risk == "Medium":
                st.warning(f"Overall concern level: **{overall_risk}**")
            else:
                st.error(f"Overall concern level: **{overall_risk}**")

            for cond in matched_conditions:
                st.markdown(f"### Possible Issue: {cond['issue']}")
                st.write(f"**Risk level:** {cond['risk']}")

                st.write("**Self-care advice:**")
                for a in cond["advice"]:
                    st.write(f"- {a}")

                st.write("**You should see a doctor / hospital if:**")
                for w in cond["doctor_when"]:
                    st.write(f"- {w}")

                st.markdown("---")

            # 🔹 Extra AI explanation from Gemini
            ai_text = gemini_explanation(user_input, matched_conditions, overall_risk)
            if ai_text:
                st.markdown("### 🤖 AI Explanation (Gemini)")
                st.write(ai_text)

            st.info(
                "This is only general information, not a medical diagnosis.\n"
                "Always consult a qualified doctor for proper treatment."
            )

st.markdown("---")
st.caption("Prototype for educational and hackathon use only.")
