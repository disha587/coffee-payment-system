from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import time
import razorpay


# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================

load_dotenv()


# ============================================
# CREATE FLASK APP
# ============================================

app = Flask(__name__)


# ============================================
# RAZORPAY CONFIGURATION
# ============================================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("WARNING: Razorpay keys are missing!")


client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


# ============================================
# HOME PAGE
# ============================================

@app.route("/")
def home():
    return render_template("payment.html")


# ============================================
# CREATE NORMAL RAZORPAY ORDER
# ============================================

@app.route("/create-order", methods=["POST"])
def create_order():

    try:

        data = request.get_json()

        print("================================")
        print("CREATE ORDER REQUEST")
        print("Received:", data)
        print("================================")

        if not data or "amount" not in data:
            return jsonify({
                "status": "failed",
                "error": "Amount is required"
            }), 400

        amount = int(data["amount"])

        if amount <= 0:
            return jsonify({
                "status": "failed",
                "error": "Invalid amount"
            }), 400

        amount_paise = amount * 100

        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": "coffee_" + str(int(time.time())),
            "payment_capture": 1
        }

        print("Creating Razorpay order...")
        print("Amount:", amount)
        print("Amount in paise:", amount_paise)

        order = client.order.create(data=order_data)

        print("================================")
        print("RAZORPAY ORDER CREATED")
        print("Order ID:", order["id"])
        print("================================")

        return jsonify({
            "status": "success",
            "order_id": order["id"],
            "amount": amount,
            "amount_paise": amount_paise,
            "key_id": RAZORPAY_KEY_ID
        })

    except Exception as e:

        print("================================")
        print("ORDER CREATION ERROR")
        print(str(e))
        print("================================")

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


# ============================================
# VERIFY NORMAL RAZORPAY PAYMENT
# ============================================

@app.route("/verify-payment", methods=["POST"])
def verify_payment():

    try:

        data = request.get_json()

        print("================================")
        print("PAYMENT VERIFICATION")
        print("Received:", data)
        print("================================")

        if not data:
            return jsonify({
                "status": "failed",
                "error": "No payment data received"
            }), 400

        required_fields = [
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature"
        ]

        for field in required_fields:

            if field not in data:
                return jsonify({
                    "status": "failed",
                    "error": f"Missing field: {field}"
                }), 400

        verification_data = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        }

        client.utility.verify_payment_signature(
            verification_data
        )

        print("================================")
        print("PAYMENT VERIFIED SUCCESSFULLY")
        print("Payment ID:", data["razorpay_payment_id"])
        print("================================")

        return jsonify({
            "status": "success",
            "message": "Payment Successful and Verified!",
            "payment_id": data["razorpay_payment_id"]
        })

    except Exception as e:

        print("================================")
        print("PAYMENT VERIFICATION ERROR")
        print(str(e))
        print("================================")

        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 400


# ============================================
# CREATE REAL RAZORPAY UPI QR
# ============================================

@app.route("/create-qr", methods=["POST"])
def create_qr():

    try:

        data = request.get_json()

        print()
        print("================================")
        print("CREATE REAL RAZORPAY QR")
        print("================================")
        print("Received data:", data)

        # ----------------------------------------
        # CHECK AMOUNT
        # ----------------------------------------

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

        # ----------------------------------------
        # CONVERT RUPEES TO PAISE
        # ----------------------------------------

        amount_paise = amount_rupees * 100

        # QR expiry = 15 minutes
        close_by = int(time.time()) + (15 * 60)

        # ----------------------------------------
        # RAZORPAY QR DATA
        # ----------------------------------------

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

        # ----------------------------------------
        # CREATE QR USING RAZORPAY
        # ----------------------------------------

        print("--------------------------------")
        print("Sending request to Razorpay...")
        print("--------------------------------")

        qr = client.qrcode.create(qr_data)

        # ----------------------------------------
        # PRINT RESPONSE
        # ----------------------------------------

        print()
        print("================================")
        print("RAZORPAY QR CREATED SUCCESSFULLY")
        print("================================")

        print("QR ID:", qr.get("id"))
        print("QR Status:", qr.get("status"))
        print("QR Image URL:", qr.get("image_url"))
        print("QR Image Content:", qr.get("image_content"))
        print("Payment Amount:", qr.get("payment_amount"))

        print("================================")

        # ----------------------------------------
        # SEND RESPONSE TO ESP32
        # ----------------------------------------

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


# ============================================
# CHECK QR PAYMENT STATUS
# ============================================

@app.route("/check-qr-payment", methods=["POST"])
def check_qr_payment():

    try:

        data = request.get_json()

        print()
        print("================================")
        print("CHECK QR PAYMENT")
        print("================================")

        if not data or "qr_id" not in data:

            return jsonify({
                "status": "failed",
                "error": "QR ID is required"
            }), 400

        qr_id = data["qr_id"]

        print("QR ID:", qr_id)

        # ----------------------------------------
        # FETCH PAYMENTS FOR THIS QR
        # ----------------------------------------

        payments = client.qrcode.fetch_all_payments(qr_id)

        print("Payments response:")
        print(payments)

        items = payments.get("items", [])

        # ----------------------------------------
        # NO PAYMENT YET
        # ----------------------------------------

        if len(items) == 0:

            print("Payment not received yet.")

            return jsonify({

                "status": "pending",

                "paid": False,

                "qr_id": qr_id

            })


        # ----------------------------------------
        # CHECK PAYMENTS
        # ----------------------------------------

        for payment in items:

            payment_status = payment.get("status")

            print("Payment ID:", payment.get("id"))
            print("Payment Status:", payment_status)
            print(
                "Payment Amount:",
                payment.get("amount")
            )

            if payment_status == "captured":

                print()
                print("================================")
                print("PAYMENT SUCCESSFUL")
                print("================================")

                return jsonify({

                    "status": "success",

                    "paid": True,

                    "qr_id": qr_id,

                    "payment_id": payment.get("id"),

                    "amount": payment.get("amount"),

                    "payment_status": payment_status

                })


        # ----------------------------------------
        # PAYMENT EXISTS BUT NOT CAPTURED
        # ----------------------------------------

        return jsonify({

            "status": "pending",

            "paid": False,

            "qr_id": qr_id

        })


    except Exception as e:

        print()
        print("================================")
        print("QR PAYMENT CHECK ERROR")
        print("================================")

        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))

        print("================================")

        return jsonify({

            "status": "failed",

            "paid": False,

            "error": str(e)

        }), 500


# ============================================
# ESP32 TEST ROUTE
# ============================================

@app.route("/esp32-test")
def esp32_test():

    return jsonify({

        "status": "success",

        "message": "ESP32 can connect to Flask server",

        "server": "coffee-payment-system",

        "razorpay": "configured"

    })


# ============================================
# RUN FLASK
# ============================================

if __name__ == "__main__":

    print()
    print("================================")
    print("COFFEE PAYMENT SYSTEM")
    print("================================")
    print("Flask server starting...")
    print("================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )