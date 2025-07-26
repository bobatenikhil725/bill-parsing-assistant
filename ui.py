import streamlit as st
from PIL import Image
from prompts import BILL_PARSE_PROMPT, CHAT_PROMPT
from utils.ocr_utils import extract_ocr_text, extract_json_from_llm_response
import json
import requests

ollama_url = "http://localhost:11434/api/generate"
llm_model = "llama3.1:8b"

st.title("Image Upload UI")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    ocr_text = extract_ocr_text(image)
    st.subheader("OCR Result (Raw)")
    st.text_area("OCR Text", ocr_text, height=150, key="ocr_text_area")

    # Only parse if this is a new upload or OCR text has changed
    if 'last_ocr_text' not in st.session_state or st.session_state['last_ocr_text'] != ocr_text:
        with st.spinner("Contacting FastAPI backend and parsing bill..."):
            resp = requests.post(
                "http://localhost:8000/parse-bill",
                json={"ocr_text": ocr_text}
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state['parsed_json'] = data.get('parsed_json')
                st.session_state['llm_response'] = data.get('llm_response')
            else:
                st.error(f"FastAPI backend error: {resp.status_code}")
        st.session_state['last_ocr_text'] = ocr_text

# Initialize session state for parsed JSON
if 'parsed_json' not in st.session_state:
    st.session_state['parsed_json'] = None
if 'llm_response' not in st.session_state:
    st.session_state['llm_response'] = None
if st.session_state['llm_response']:
    st.subheader("LLM Raw Response")
    st.code(st.session_state['llm_response'], language="markdown")
if st.session_state['parsed_json'] is not None:
    st.subheader("Extracted Structured Bill (from LLM)")
    st.json(st.session_state['parsed_json'])
    st.download_button(
        label="Export JSON",
        data=json.dumps(st.session_state['parsed_json'], indent=2),
        file_name="extracted_bill.json",
        mime="application/json"
    )

st.subheader("Query the Extracted Bill")
if st.session_state['parsed_json'] is not None:
    if 'bill_chat_history' not in st.session_state:
        st.session_state['bill_chat_history'] = []
    user_query = st.text_input("Ask a question about this bill:", "")
    if st.button("Ask about Bill") and user_query:
        st.session_state['bill_chat_history'].append(("You", user_query))
        with st.spinner("Contacting FastAPI backend for answer..."):
            resp = requests.post(
                "http://localhost:8000/chat-bill",
                json={
                    "bill_json": st.session_state['parsed_json'],
                    "user_query": user_query
                }
            )
            if resp.status_code == 200:
                llm_answer = resp.json().get('llm_answer', '')
                st.session_state['bill_chat_history'].append(("Bot", llm_answer.strip()))
            else:
                st.session_state['bill_chat_history'].append(("Bot", f"FastAPI backend error: {resp.status_code}"))
    for sender, message in st.session_state['bill_chat_history']:
        st.write(f"**{sender}:** {message}")

