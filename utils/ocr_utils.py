# OCR and JSON extraction utilities
import easyocr
import numpy as np
import re
import json
from PIL import Image
import streamlit as st

def extract_ocr_text(image: Image.Image) -> str:
    """Extract text from an image using EasyOCR and return as a single string."""
    img_array = np.array(image)
    reader = easyocr.Reader(['en'], gpu=False)
    ocr_result = reader.readtext(img_array)
    ocr_text = "\n".join([item[1] for item in ocr_result])
    return ocr_text

def extract_json_from_llm_response(llm_response: str) -> dict:
    """Extract JSON object from LLM response string."""
    json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
    if not json_match:
        json_match = re.search(r'({[\s\S]*})', llm_response)
    if json_match:
        extracted_json = json_match.group(1)
        try:
            return json.loads(extracted_json)
        except Exception as e:
            st.error(f"Failed to parse JSON: {e}")
            st.subheader("Raw Extracted JSON String")
            st.code(extracted_json, language="json")
            st.info("Check for missing commas, quotes, or other JSON formatting issues in the LLM output.")
    else:
        st.error("No JSON found in LLM response.")
    return None
