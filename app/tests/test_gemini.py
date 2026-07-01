from app.services.gemini_service import classify_transactions


def test_gemini():

    data = [
        {
            "txn_id": "TXN001",
            "merchant": "Amazon",
            "amount": 500,
            "currency": "INR",
            "status": "SUCCESS"
        }
    ]

    result = classify_transactions(data)

    assert isinstance(result, list)
    assert "category" in result[0]