from flask import Flask, jsonify, render_template
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


@app.route("/payment-status")
def payment_status():
    return jsonify({
        "status": "waiting_for_payment"
    })


@app.route("/create-order")
def create_order():

    order_data = {
        "amount": 1000,  # ₹10 = 1000 paise
        "currency": "INR",
        "payment_capture": 1
    }

    order = client.order.create(data=order_data)

    return jsonify({
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": RAZORPAY_KEY_ID
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)