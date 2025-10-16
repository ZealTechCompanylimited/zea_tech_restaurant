import requests
import logging
from django.conf import settings
import uuid
logger = logging.getLogger(__name__)

class AzamPayService:
    def __init__(self):
        self.auth_url = settings.AZAMPAY_AUTH_URL
        self.checkout_url = settings.AZAMPAY_CHECKOUT_URL
        self.token = self.get_access_token()

    def get_access_token(self):
        payload = {
            "appName": settings.AZAMPAY_APP_NAME,
            "clientId": settings.AZAMPAY_CLIENT_ID,
            "clientSecret": settings.AZAMPAY_CLIENT_SECRET,
        }
        headers = {"Content-Type": "application/json"}

        try:
            resp = requests.post(self.auth_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"AzamPay token response: {data}")

            return (
                data.get("data", {}).get("accessToken")
                or data.get("accessToken")
                or data.get("token")
                or "eedcd758-a0b5-4fe9-8969-b8cbde95fa15"
            )
        except requests.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            return "eedcd758-a0b5-4fe9-8969-b8cbde95fa15"



    def initiate_payment(self, order, amount, phone_number, provider="Airtel"):
        if not self.token:
            return {"error": "Missing access token"}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        external_id = str(order.id) if order else str(uuid.uuid4())
        remarks = f"Payment for order {order.id}" if order else "Payment without order"

        payload = {
            "accountNumber": phone_number,
            "amount": float(amount),
            "currency": "TZS",
            "externalId": external_id,
            "provider": provider,
            "remarks": remarks,
            "callbackUrl": settings.AZAMPAY_CALLBACK_URL,
        }

        try:
            resp = requests.post(self.checkout_url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Payment initiation failed: {e}")
            return {"error": str(e)}
