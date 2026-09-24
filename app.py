from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import requests
import time

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

RAZORPAY_API = "https://api.razorpay.com/v1"

app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("payment.html")


# =========================================================
# CREATE REAL RAZORPAY QR
# =========================================================

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

        # QR expires after 10 minutes
        close_by = int(time.time()) + 600

        qr_data = {
            "type": "upi_qr",
            "name": "Coffee Vending Machine",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": "Coffee Vending Machine Payment",
            "close_by": close_by,
            "notes": {
                "source": "coffee_vending_machine",
                "amount_rupees": str(amount_rupees)
            }
        }

        print("\n==============================")
        print("CREATING REAL RAZORPAY QR")
        print("==============================")
        print("Amount:", amount_rupees)
        print("Amount paise:", amount_paise)

        response = requests.post(
            f"{RAZORPAY_API}/payments/qr_codes",
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json=qr_data,
            timeout=20
        )

        print("Razorpay HTTP:", response.status_code)
        print("Razorpay response:", response.text)

        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "error": response.text
            }), response.status_code

        qr = response.json()

        return jsonify({
            "status": "success",
            "qr_id": qr["id"],
            "amount": qr["payment_amount"],
            "amount_rupees": amount_rupees,
            "image_url": qr.get("image_url"),
            "image_content": qr.get("image_content", ""),
            "close_by": qr.get("close_by")
        })

    except Exception as e:

        print("CREATE QR ERROR:", str(e))

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# =========================================================
# CHECK RAZORPAY QR PAYMENT
# =========================================================

@app.route("/check-qr-payment", methods=["POST"])
def check_qr_payment():

    try:

        data = request.get_json()

        if not data or "qr_id" not in data:
            return jsonify({
                "status": "failed",
                "error": "qr_id is required"
            }), 400

        qr_id = data["qr_id"]

        print("\n==============================")
        print("CHECKING RAZORPAY PAYMENT")
        print("==============================")
        print("QR ID:", qr_id)

        response = requests.get(
            f"{RAZORPAY_API}/payments/qr_codes/{qr_id}/payments",
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            params={
                "count": 10
            },
            timeout=20
        )

        print("Razorpay HTTP:", response.status_code)
        print("Response:", response.text)

        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "error": response.text
            }), response.status_code

        result = response.json()

        payments = result.get("items", [])

        if len(payments) == 0:

            return jsonify({
                "status": "pending",
                "message": "Waiting for payment"
            })

        for payment in payments:

            payment_status = payment.get("status")
            payment_amount = payment.get("amount")

            print(
                "Payment:",
                payment.get("id"),
                "Status:",
                payment_status,
                "Amount:",
                payment_amount
            )

            if payment_status == "captured":

                return jsonify({
                    "status": "success",
                    "message": "Payment received",
                    "payment_id": payment.get("id"),
                    "amount": payment_amount,
                    "method": payment.get("method")
                })

        return jsonify({
            "status": "pending",
            "message": "Payment not captured yet"
        })

    except Exception as e:

        print("CHECK PAYMENT ERROR:", str(e))

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# =========================================================
# OLD CREATE ORDER - KEEPING IT
# =========================================================

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

        import razorpay

        client = razorpay.Client(
            auth=(
                RAZORPAY_KEY_ID,
                RAZORPAY_KEY_SECRET
            )
        )

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


# =========================================================
# OLD PAYMENT VERIFICATION
# =========================================================

@app.route("/verify-payment", methods=["POST"])
def verify_payment():

    import razorpay

    data = request.get_json()

    try:

        client = razorpay.Client(
            auth=(
                RAZORPAY_KEY_ID,
                RAZORPAY_KEY_SECRET
            )
        )

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
            "message": "Payment verified successfully"
        })

    except Exception:

        return jsonify({
            "status": "failed",
            "message": "Payment verification failed"
        }), 400


# =========================================================
# ESP32 CONNECTION TEST
# =========================================================

@app.route("/esp32-test", methods=["GET"])
def esp32_test():

    return jsonify({
        "status": "success",
        "message": "ESP32 connected to Flask",
        "device": "coffee_vending_machine"
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )