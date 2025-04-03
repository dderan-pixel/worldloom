from fastapi import FastAPI, Request, HTTPException, Depends, Header
from pydantic import BaseModel
import requests
import uuid
import time
import pandas as pd
import yfinance as yf
import openai
import sqlite3
import jwt
import hmac
import hashlib
import os
import pandas_ta as ta

app = FastAPI()

NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
openai.api_key = CHATGPT_API_KEY

conn = sqlite3.connect("subscriptions.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id TEXT PRIMARY KEY,
    expiry INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    coin TEXT,
    user_id TEXT,
    vote TEXT,
    PRIMARY KEY (coin, user_id)
)
""")
conn.commit()

class ChatRequest(BaseModel):
    message: str

class LoginRequest(BaseModel):
    user_id: str

class PaymentRequest(BaseModel):
    user_id: str
    plan: str

class VoteRequest(BaseModel):
    coin: str
    vote: str

class SimulateRequest(BaseModel):
    coin: str
    strategy: str

class PortfolioRequest(BaseModel):
    holdings: dict

class TriggerRequest(BaseModel):
    coin: str
    condition: str

def get_language(accept_language: str = Header(default="en")):
    return accept_language.split(',')[0][:2]

@app.get("/")
def root():
    return {"message": "🚀 Worldloom backend is running!"}

@app.post("/chat")
def chat(data: ChatRequest):
    prompt = f"Analyze this trading message: {data.message}"
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a crypto trading assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return {"response": completion.choices[0].message.content.strip()}

@app.post("/simulate")
def simulate(data: SimulateRequest):
    try:
        df = yf.download(f"{data.coin}-USD", period="1mo", interval="1h")
        df.dropna(inplace=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        trades = []
        in_position = False
        entry_price = 0
        pnl = 0
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]
            if not in_position and row["RSI_14"] < 30 and row["MACD_12_26_9"] > row["MACDs_12_26_9"]:
                in_position = True
                entry_price = row["Close"]
                trades.append((row.name, "BUY", entry_price))
            elif in_position and row["RSI_14"] > 70:
                in_position = False
                exit_price = row["Close"]
                profit = (exit_price - entry_price) / entry_price * 100
                pnl += profit
                trades.append((row.name, "SELL", exit_price))
        return {
            "trades": trades,
            "total_pnl_%": round(pnl, 2),
            "strategy": data.strategy,
            "coin": data.coin
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/portfolio-advice")
def portfolio_advice(data: PortfolioRequest, lang: str = Depends(get_language)):
    holdings = ", ".join([f"{k}: {v}%" for k, v in data.holdings.items()])
    prompt = f"Mevcut portföy: {holdings}\n\nBu dağılımı değerlendir ve {lang} dilinde profesyonel bir tavsiye ver. Daha iyi bir risk-yatırım dengesi öner."
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sen bir portföy yöneticisi ve yatırım danışmanısın."},
            {"role": "user", "content": prompt}
        ]
    )
    return {"advice": completion.choices[0].message.content.strip()}

@app.post("/ai-score/{symbol}")
def ai_coin_score(symbol: str, lang: str = Depends(get_language)):
    prompt = f"Coin: {symbol.upper()}\n\nEvaluate this crypto asset and rate its current investment potential from 0 to 100. Use {lang} language."
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional crypto trading assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return {"symbol": symbol.upper(), "ai_score": completion.choices[0].message.content.strip()}
