import requests
import json

# Update this to your actual backend URL
BACKEND_URL = "http://localhost:8000/wallet/fund"

# Test data for Stripe (using Stripe test PaymentMethod ID)
payload = {
    "parent_id": 1,  # Use a valid parent ID from your DB
    "amount_pesos": 100.0,
    "payment_method": "stripe_card",
    "stripe_payment_method_id": "pm_card_visa"  # Stripe test PaymentMethod
}

headers = {"Content-Type": "application/json"}

response = requests.post(BACKEND_URL, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response:", response.text)
