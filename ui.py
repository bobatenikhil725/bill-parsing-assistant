import streamlit as st
from PIL import Image
import easyocr
import numpy as np
import re
import json
import requests

st.title("Image Upload UI")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Bill parsing using easyocr
    img_array = np.array(image)
    reader = easyocr.Reader(['en'], gpu=False)
    ocr_result = reader.readtext(img_array)
    st.subheader("OCR Result (Raw)")
    if ocr_result:
        ocr_text = "\n".join([item[1] for item in ocr_result])
        st.text_area("OCR Text", ocr_text, height=150, key="ocr_text_area")
        # Only parse if this is a new upload or OCR text has changed
        if 'last_ocr_text' not in st.session_state or st.session_state['last_ocr_text'] != ocr_text:
            ollama_url = "http://localhost:11434/api/generate"
            llm_model = "llama3.1:8b"
            prompt = f"""
You are an expert bill parsing AI. Extract structured information from the provided OCR text of a bill/invoice/receipt. 

**Input**: Raw OCR text from EasyOCR extraction
**Task**: Parse and extract key information into structured JSON format

**Extract the following information when available:**

## Required Fields:
- Document type (invoice/receipt/bill)
- Invoice/Receipt number
- Date
- Vendor/Business name
- Customer name (if present)
- Total amount
- Currency

## Items Information:
For each product/service:
- Description/Name
- Quantity
- Unit price
- Total price

## Financial Details:
- Subtotal
- Tax amount(s)
- Discounts
- Final total
- Payment method (if mentioned)

## Additional Fields (if available):
- Order ID
- GSTIN/Tax registration numbers
- Addresses (billing/shipping)
- Phone numbers
- Serial numbers/SKUs
- Warranty information

**Output Format:**
```json
{{
  "document_type": "",
  "invoice_number": "",
  "date": "",
  "vendor": {{
    "name": "",
    "address": "",
    "phone": "",
    "gstin": ""
  }},
  "customer": {{
    "name": "",
    "address": ""
  }},
  "items": [
    {{
      "description": "",
      "quantity": 0,
      "unit_price": 0,
      "total": 0
    }}
  ],
  "summary": {{
    "subtotal": 0,
    "tax": 0,
    "discount": 0,
    "grand_total": 0,
    "currency": ""
  }},
  "additional_info": {{}}
}}
```

**Instructions:**
1. Extract information exactly as it appears in the OCR text
2. Use null for missing information
3. Preserve original formatting for numbers and dates
4. If text is unclear, mark with \"UNCLEAR\" and provide best guess
5. Group related items together logically

Now parse the following OCR text:
{ocr_text}
"""
            with st.spinner("Contacting LLM and parsing bill..."):
                response = requests.post(
                    ollama_url,
                    json={
                        "model": llm_model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    llm_response = response.json().get("response", "")
                    json_match = re.search(r'```json\\s*(.*?)\\s*```', llm_response, re.DOTALL)
                    if not json_match:
                        json_match = re.search(r'({[\s\S]*})', llm_response)
                    if json_match:
                        extracted_json = json_match.group(1)
                        try:
                            parsed_json = json.loads(extracted_json)
                            st.session_state['parsed_json'] = parsed_json
                            st.session_state['llm_response'] = llm_response
                        except Exception as e:
                            st.error(f"Failed to parse JSON: {e}")
                            st.subheader("Raw Extracted JSON String")
                            st.code(extracted_json, language="json")
                            st.info("Check for missing commas, quotes, or other JSON formatting issues in the LLM output.")
                    else:
                        st.error("No JSON found in LLM response.")
                else:
                    st.error(f"LLM request failed: {response.status_code}")
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
        chat_prompt = f"""
You are an expert bill assistant. Use ONLY the following JSON bill data to answer the user's question. If the answer is not present in the data, say 'Not found in bill.'

Bill JSON:
{json.dumps(st.session_state['parsed_json'], indent=2)}

User question: {user_query}

Answer concisely:
"""
        with st.spinner("Contacting LLM for answer..."):
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": chat_prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                llm_answer = response.json().get("response", "")
                st.session_state['bill_chat_history'].append(("Bot", llm_answer.strip()))
            else:
                st.session_state['bill_chat_history'].append(("Bot", f"LLM request failed: {response.status_code}"))
    for sender, message in st.session_state['bill_chat_history']:
        st.write(f"**{sender}:** {message}")

