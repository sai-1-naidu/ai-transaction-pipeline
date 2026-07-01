import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

def classify_transactions(transactions):

    prompt = f"""
You are a finance expert.

For each transaction return ONLY JSON.

Transactions:
{json.dumps(transactions, indent=2)}

Return:

[
  {{
    "txn_id":"...",
    "category":"..."
  }}
]
"""

    retries = 3

    for attempt in range(retries):

        try:

            response = model.generate_content(prompt)

            text = response.text

            print("Gemini Response:")
            print(text)

            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

            text = text.strip()

            return json.loads(text)

        except Exception as e:

            print(f"Attempt {attempt+1} failed:", e)

            if attempt < retries - 1:
                time.sleep(2 ** attempt)

    raise Exception("Gemini failed after 3 retries")

def generate_summary(summary_data):

    prompt = f"""
You are a financial analyst.

Based on this transaction summary:

{json.dumps(summary_data, indent=2)}

Write ONLY JSON.

Return:

{{
    "risk_level":"LOW/MEDIUM/HIGH",
    "narrative":"2-3 sentence executive summary"
}}
"""

    response = model.generate_content(prompt)

    text = response.text

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    text = text.strip()

    return json.loads(text)