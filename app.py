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


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return render_template("payment.html")


# =====================================================
# CREATE RAZORPAY ORDER
# =====================================================

@app.route("/create-order", methods=["GET", "POST"])
def create_order():

    try:

        # -------------------------------------------------
        # TEST / WEBSITE
        # If no amount is sent, use ₹20
        # -------------------------------------------------

        if request.method == "GET":
            amount_rupees = 20

        # -------------------------------------------------
        # ESP32
        # ESP32 will send the actual amount
        # -------------------------------------------------

        else:

            data = request.get_json()

            if not data or "amount" not in data:
                return jsonify({
                    "error": "Amount is required"
                }), 400

            amount_rupees = int(data["amount"])

        # -------------------------------------------------
        # Validate amount
        # -------------------------------------------------

        if amount_rupees <= 0:
            return jsonify({
                "error": "Invalid amount"
            }), 400

        # Convert rupees → paise
        amount_paise = amount_rupees * 100

        # -------------------------------------------------
        # Create Razorpay order
        # -------------------------------------------------

        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "source": "coffee_vending_machine"
            }
        }

        order = client.order.create(data=order_data)

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


# =====================================================
# VERIFY RAZORPAY PAYMENT
# =====================================================

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

@app.route("/esp32-test", methods=["GET"])
def esp32_test():
    return jsonify({
        "status": "success",
        "message": "ESP32 connected to Flask",
        "device": "coffee_vending_machine"
    })
# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )