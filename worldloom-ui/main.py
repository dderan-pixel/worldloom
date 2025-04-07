from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key (make sure to use os.getenv in real usage)
openai.api_key = os.getenv("CHATGPT_API_KEY") or "sk-xxx"

# Schemas
class ChatRequest(BaseModel):
    message: str

# Root test
@app.get("/")
def root():
    return {"message": "✅ Worldloom backend is alive"}

# Chat endpoint
@app.post("/chat")
def chat(data: ChatRequest):
    try:
        prompt = f"User message: {data.message}\nGive a professional crypto trading analysis based on current market behavior."
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a crypto trading assistant that replies concisely and clearly."},
                {"role": "user", "content": prompt},
            ]
        )
        return {"response": completion.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
