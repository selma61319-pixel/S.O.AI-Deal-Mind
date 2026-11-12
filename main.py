
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import json
from openai import OpenAI

app = FastAPI(
    title="S.O.AI.Deal Mind - Autonomous Lifestyle & Commerce Orchestrator",
    description="Voice-first AI agent merging authentic retail deals and local services into a single PayPal checkout."
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"

class UserPreferences(BaseModel):
    authentic_only: bool = True
    pricing_strategy: str = "lowest_price"
    trusted_sellers_only: bool = True
    urgency_shipping: str = "fast_split"
    sunday_service_rescue: bool = True

class VoiceOrderRequest(BaseModel):
    transcribed_voice_prompt: str
    user_location: str
    preferences: UserPreferences

def create_unified_paypal_invoice(total_amount: float, description: str, currency: str = "USD"):
    auth_response = requests.post(f"{PAYPAL_BASE_URL}/v1/oauth2/token", auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET), data={"grant_type": "client_credentials"})
    access_token = auth_response.json().get("access_token")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    order_payload = {"intent": "CAPTURE", "purchase_units": [{"amount": {"currency_code": currency, "value": f"{total_amount:.2f}"}, "description": description}]}
    response = requests.post(f"{PAYPAL_BASE_URL}/v2/checkout/orders", json=order_payload, headers=headers)
    return response.json()

@app.post("/api/v1/orchestrate-lifestyle")
async def orchestrate_dealmind(request: VoiceOrderRequest):
    try:
        system_prompt = f"You are 'S.O.AI.Deal Mind'. Analyze: {request.transcribed_voice_prompt} in {request.user_location}. Constraints: Authentic Only {request.preferences.authentic_only}, Pricing {request.preferences.pricing_strategy}, Trusted Sellers {request.preferences.trusted_sellers_only}, Shipping {request.preferences.urgency_shipping}, Sunday Rescue {request.preferences.sunday_service_rescue}. Tasks: 1. Find retail items 2. Find open service within 5km 3. Apply 40% cross-merchant reward 4. Calculate total. Return STRICT JSON with keys: retail_items, service_booking, cross_merchant_reward_applied, total_usd, summary_message."
        ai_response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": system_prompt}], response_format={"type": "json_object"})
        plan = json.loads(ai_response.choices[0].message.content)
        paypal_order = create_unified_paypal_invoice(total_amount=plan["total_usd"], description="S.O.AI.Deal Mind - Unified Retail & Local Service Bundle")
        return {"status": "ready_for_approval", "agent_plan": plan, "paypal_checkout": paypal_order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
