import streamlit as st
import google.generativeai as genai
import requests
import json
import re

# ----------------------------
# 1. Configure Gemini
# ----------------------------

import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
CERT_PATH = os.path.join(os.path.dirname(__file__), "zscaler.crt")

prompt_template = """
Extract structured parameters for a Dialogflow webhook.

Return ONLY valid JSON like this:

{{
  "version": "",
  "month": "",
  "measure": "",
  "value": ""
}}

Rules:
- version: Plan Year 1 , Plan Year 2
- month: Jan–Dec or full month names
- measure: Headcount
- value: Numeric only
- If missing info, infer from context or leave empty.

User: "{user_message}"
"""

def extract_params_from_gemini(text):
    model = genai.GenerativeModel("gemini-2.5-flash")
    final_prompt = prompt_template.format(user_message=text)
    response = model.generate_content(final_prompt)
    raw_text = response.text.strip()

    # Extract JSON safely
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    else:
        return {"version": "", "month": "", "measure": "", "value": ""}

def send_to_webhook(json_params):
    payload = {
        "queryResult": {
            "intent": {"displayName": "Create Data"},
            "parameters": json_params
        }
    }
    r = requests.post(
        "https://chatbot-lpd7.onrender.com/webhook",
        json=payload,
        verify= CERT_PATH  # ✅ Custom cert
    )
    return r.json()

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Gemini + TM1 Chatbot", layout="centered")
st.title("🤖TM1 Chatbot for IBM PA")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    role = "You" if msg["role"] == "user" else "Bot"
    st.markdown(f"**{role}:** {msg['text']}")

st.markdown("---")

user_input = st.text_input("Enter your message:")
if st.button("Send") and user_input:
    st.session_state["messages"].append({"role": "user", "text": user_input})

    with st.spinner("Extracting parameters from Gemini..."):
        params = extract_params_from_gemini(user_input)

    st.write("📦 Extracted JSON:", params)

    with st.spinner("Sending to webhook..."):
        response = send_to_webhook(params)

    bot_reply = json.dumps(response, indent=2)
    st.session_state["messages"].append({"role": "bot", "text": bot_reply})

    st.rerun()




