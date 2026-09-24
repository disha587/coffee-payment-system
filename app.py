from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import razorpay
import requests   # ← ADD THIS

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

app = Flask(__name__)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("payment.html")


# ==========================================
# CREATE RAZORPAY ORDER
# ==========================================

@app.route("/create-order", methods=["GET", "POST"])
def create_order():

    try:

        if request.method == "GET":
            amount_rupees = 20

        else:
            data = request.get_json()

            if not data or "amount" not in data:
                return jsonify({
                    "error": "Amount is required"
                }), 400

            amount_rupees = int(data["amount"])

        if amount_rupees <= 0:
            return jsonify({
                "error": "Invalid amount"
            }), 400

        amount_paise = amount_rupees * 100

        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "source": "coffee_vending_machine"
            }
        }

        order = client.order.create(
            data=order_data
        )

        return jsonify({
            "status": "success",
            "order_id": order["id"],
            "amount": order["amount"],
            "amount_rupees": amount_rupees,
            "currency": order["currency"],
            "key_id": RAZORPAY_KEY_ID
        })

    except Exception as e:

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# ==========================================
# CREATE REAL RAZORPAY QR
# ==========================================

@app.route("/create-qr", methods=["POST"])
def create_qr():

    try:

        data = request.get_json()

        if not data or "amount" not in data:
            return jsonify({
                "status": "failed",
                "error": "Amount is required"
            }), 400

        amount_rupees = int(data["amount"])

        if amount_rupees <= 0:
            return jsonify({
                "status": "failed",
                "error": "Invalid amount"
            }), 400

        amount_paise = amount_rupees * 100

        qr_data = {
            "type": "upi_qr",
            "name": "Coffee Vending Machine",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": "Coffee payment"
        }

        response = requests.post(
            "https://api.razorpay.com/v1/payments/qr_codes",
            auth=(
                RAZORPAY_KEY_ID,
                RAZORPAY_KEY_SECRET
            ),
            json=qr_data
        )

        print(
            "Razorpay QR response:",
            response.status_code
        )

        print(response.text)

        if response.status_code not in [200, 201]:

            return jsonify({
                "status": "failed",
                "error": response.text
            }), response.status_code

        qr = response.json()

        return jsonify({
            "status": "success",
            "qr_id": qr["id"],
            "image_content": qr.get("image_content"),
            "image_url": qr.get("image_url")
        })

    except Exception as e:

        print("QR ERROR:", str(e))

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# ==========================================
# VERIFY PAYMENT
# ==========================================

@app.route("/verify-payment", methods=["POST"])
def verify_payment():

    data = request.get_json()

    try:

        client.utility.verify_payment_signature({
            "razorpay_order_id":
                data["razorpay_order_id"],

            "razorpay_payment_id":
                data["razorpay_payment_id"],

            "razorpay_signature":
                data["razorpay_signature"]
        })

        return jsonify({
            "status": "success",
            "message":
                "Payment verified successfully"
        })

    except Exception:

        return jsonify({
            "status": "failed",
            "message":
                "Payment verification failed"
        }), 400


# ==========================================
# ESP32 TEST
# ==========================================

@app.route("/esp32-test", methods=["GET"])
def esp32_test():

    return jsonify({
        "status": "success",
        "message": "ESP32 connected to Flask",
        "device": "coffee_vending_machine"
    })


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )