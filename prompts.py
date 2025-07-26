# Prompt templates for bill parsing and chat

BILL_PARSE_PROMPT = """
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

CHAT_PROMPT = """
You are an expert bill assistant. Use ONLY the following JSON bill data to answer the user's question. If the answer is not present in the data, say 'Not found in bill.'

Bill JSON:
{bill_json}

User question: {user_query}

Answer concisely:
"""
