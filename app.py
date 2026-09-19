from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import razorpay

# Load environment variables
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Create Razorpay client
client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("payment.html")


# Create Razorpay order
@app.route("/create-order")
def create_order():

    order_data = {
        "amount": 2000,          # ₹20 = 2000 paise
        "currency": "INR",
        "payment_capture": 1
    }

    try:
        order = client.order.create(data=order_data)

        return jsonify({
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": RAZORPAY_KEY_ID
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# Verify Razorpay payment
@app.route("/verify-payment", methods=["POST"])
def verify_payment():

    data = request.get_json()

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        return jsonify({
            "status": "success",
            "message": "Payment verified successfully"
        })

    except Exception:
        return jsonify({
            "status": "failed",
            "message": "Payment verification failed"
        }), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)