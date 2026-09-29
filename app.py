from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import time
import razorpay
import requests

# ==============================
# LOAD ENVIRONMENT VARIABLES
# ==============================
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# ==============================
# FLASK APP
# ==============================
app = Flask(__name__)

# Razorpay client
client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


# =========================================================
# HOME PAGE
# =========================================================
@app.route("/")
def home():
    return render_template("payment.html")


# =========================================================
# CREATE NORMAL RAZORPAY ORDER
# =========================================================
@app.route("/create-order", methods=["POST"])
def create_order():
    try:
        data = request.get_json()

        if not data or "amount" not in data:
            return jsonify({
                "status": "failed",
                "error": "Amount is required"
            }), 400

        amount = int(data["amount"])

        order_data = {
            "amount": amount * 100,
            "currency": "INR",
            "payment_capture": 1
        }

        order = client.order.create(data=order_data)

        return jsonify({
            "status": "success",
            "order_id": order["id"],
            "amount": amount
        })

    except Exception as e:
        print("ORDER CREATION ERROR:", str(e))

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# =========================================================
# VERIFY NORMAL RAZORPAY PAYMENT
# =========================================================
@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    try:
        data = request.get_json()

        print()
        print("================================")
        print("VERIFY PAYMENT")
        print("================================")
        print("Received:", data)

        params_dict = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        }

        client.utility.verify_payment_signature(params_dict)

        print("PAYMENT SIGNATURE VERIFIED")
        print("================================")

        return jsonify({
            "status": "success",
            "message": "Payment Successful and Verified!"
        })

    except Exception as e:
        print()
        print("================================")
        print("PAYMENT VERIFICATION ERROR")
        print("================================")
        print(str(e))
        print("================================")

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 400


# =========================================================
# CREATE REAL RAZORPAY UPI QR
# =========================================================
@app.route("/create-qr", methods=["POST"])
def create_qr():
    try:
        data = request.get_json()

        print()
        print("================================")
        print("CREATE REAL RAZORPAY QR")
        print("================================")
        print("Received data:", data)

        # -----------------------------
        # CHECK AMOUNT
        # -----------------------------
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

        # Convert rupees to paise
        amount_paise = amount_rupees * 100

        # QR valid for 15 minutes
        close_by = int(time.time()) + (15 * 60)

        # -----------------------------
        # RAZORPAY QR DATA
        # -----------------------------
        qr_data = {
            "type": "upi_qr",
            "name": "Coffee Vending Machine",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": "Coffee payment",
            "close_by": close_by,
            "notes": {
                "source": "coffee_vending_machine"
            }
        }

        print("--------------------------------")
        print("QR DATA")
        print("--------------------------------")
        print("Amount (rupees):", amount_rupees)
        print("Amount (paise):", amount_paise)
        print("QR data:", qr_data)

        # =================================================
        # IMPORTANT:
        # DIRECT RAZORPAY API REQUEST
        # =================================================
        razorpay_url = (
            "https://api.razorpay.com/v1/payments/qr_codes"
        )

        print("--------------------------------")
        print("RAZORPAY URL:")
        print(razorpay_url)
        print("--------------------------------")
        print("Sending request to Razorpay...")

        response = requests.post(
            razorpay_url,
            auth=(
                RAZORPAY_KEY_ID,
                RAZORPAY_KEY_SECRET
            ),
            json=qr_data,
            timeout=30
        )

        print("--------------------------------")
        print("RAZORPAY RESPONSE")
        print("--------------------------------")
        print("HTTP Status:", response.status_code)
        print("Response:", response.text)
        print("--------------------------------")

        # -----------------------------
        # CHECK RESPONSE
        # -----------------------------
        if response.status_code not in [200, 201]:

            return jsonify({
                "status": "failed",
                "error": response.text,
                "razorpay_status": response.status_code
            }), 500

        # -----------------------------
        # READ QR RESPONSE
        # -----------------------------
        qr = response.json()

        print()
        print("================================")
        print("RAZORPAY QR CREATED SUCCESSFULLY")
        print("================================")
        print("QR ID:", qr.get("id"))
        print("QR Status:", qr.get("status"))
        print("QR Image URL:", qr.get("image_url"))
        print("QR Image Content:", qr.get("image_content"))
        print("================================")

        # -----------------------------
        # SEND QR DATA TO ESP32
        # -----------------------------
        return jsonify({
            "status": "success",
            "qr_id": qr.get("id"),
            "image_content": qr.get("image_content"),
            "image_url": qr.get("image_url"),
            "amount": amount_rupees,
            "amount_paise": amount_paise
        })

    except Exception as e:

        print()
        print("================================")
        print("RAZORPAY QR CREATION ERROR")
        print("================================")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("================================")

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# =========================================================
# CHECK QR PAYMENT STATUS
# =========================================================
@app.route("/check-qr-payment", methods=["POST"])
def check_qr_payment():
    try:
        data = request.get_json()

        print()
        print("================================")
        print("CHECK QR PAYMENT")
        print("================================")
        print("Received:", data)

        if not data or "qr_id" not in data:
            return jsonify({
                "status": "failed",
                "error": "QR ID is required"
            }), 400

        qr_id = data["qr_id"]

        # Razorpay API
        url = (
            "https://api.razorpay.com/v1/payments/qr_codes/"
            + qr_id
            + "/payments"
        )

        response = requests.get(
            url,
            auth=(
                RAZORPAY_KEY_ID,
                RAZORPAY_KEY_SECRET
            ),
            timeout=30
        )

        print("--------------------------------")
        print("RAZORPAY PAYMENT RESPONSE")
        print("--------------------------------")
        print("HTTP Status:", response.status_code)
        print("Response:", response.text)
        print("--------------------------------")

        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "error": response.text
            }), 500

        payment_data = response.json()

        items = payment_data.get("items", [])

        # ---------------------------------
        # PAYMENT FOUND
        # ---------------------------------
        if len(items) > 0:

            payment = items[0]

            payment_status = payment.get("status")

            print("Payment status:", payment_status)

            if payment_status == "captured":

                print()
                print("================================")
                print("PAYMENT SUCCESSFUL")
                print("================================")
                print("Payment ID:", payment.get("id"))
                print("Amount:", payment.get("amount"))
                print("================================")

                return jsonify({
                    "status": "success",
                    "payment_status": "captured",
                    "payment_id": payment.get("id"),
                    "amount": payment.get("amount")
                })

        # ---------------------------------
        # PAYMENT NOT FOUND YET
        # ---------------------------------
        return jsonify({
            "status": "pending",
            "payment_status": "pending"
        })

    except Exception as e:

        print()
        print("================================")
        print("QR PAYMENT CHECK ERROR")
        print("================================")
        print("ERROR:", str(e))
        print("================================")

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# =========================================================
# ESP32 TEST ROUTE
# =========================================================
@app.route("/esp32-test")
def esp32_test():

    return jsonify({
        "status": "success",
        "message": "ESP32 connected to Flask server"
    })


# =========================================================
# RUN FLASK
# =========================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )