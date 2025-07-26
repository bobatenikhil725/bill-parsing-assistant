from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from prompts import BILL_PARSE_PROMPT, CHAT_PROMPT
import json
from utils.ocr_utils import extract_json_from_llm_response
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ollama_url = "http://localhost:11434"
llm_model = "llama3.1:8b"
ollama_llm = Ollama(model=llm_model, base_url=ollama_url)

class ParseBillRequest(BaseModel):
    ocr_text: str

class ChatBillRequest(BaseModel):
    bill_json: dict
    user_query: str

@app.post("/parse-bill")
async def parse_bill(req: ParseBillRequest):
    prompt_template = PromptTemplate.from_template(BILL_PARSE_PROMPT)
    prompt = prompt_template.format(ocr_text=req.ocr_text)
    print("Prompt sent to LLM:\n", prompt)  # Debug print
    chain = prompt_template | ollama_llm | StrOutputParser()
    llm_response = chain.invoke({"ocr_text": req.ocr_text})
    parsed_json = extract_json_from_llm_response(llm_response)
    return JSONResponse({"llm_response": llm_response, "parsed_json": parsed_json})

@app.post("/chat-bill")
async def chat_bill(req: ChatBillRequest):
    prompt_template = PromptTemplate.from_template(CHAT_PROMPT)
    chain = prompt_template | ollama_llm | StrOutputParser()
    llm_answer = chain.invoke({"bill_json": json.dumps(req.bill_json, indent=2), "user_query": req.user_query})
    return JSONResponse({"llm_answer": llm_answer})
