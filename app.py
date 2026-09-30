from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import os
import time
import razorpay
import requests
import cv2
import numpy as np


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# CHECK RAZORPAY CREDENTIALS
# =========================================================

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("WARNING: Razorpay credentials are missing!")


# =========================================================
# RAZORPAY CLIENT
# =========================================================

client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
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


        if amount <= 0:

            return jsonify({
                "status": "failed",
                "error": "Invalid amount"
            }), 400


        # Amount in paise

        order_data = {

            "amount": amount * 100,

            "currency": "INR",

            "payment_capture": 1
        }


        # Create Razorpay order

        order = client.order.create(
            data=order_data
        )


        return jsonify({

            "status": "success",

            "order_id": order["id"],

            "amount": amount
        })


    except Exception as e:

        print()
        print("================================")
        print("ORDER CREATION ERROR")
        print("================================")
        print(str(e))
        print("================================")


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
        print("================================")


        if not data:

            return jsonify({

                "status": "failed",

                "error": "Payment data is required"

            }), 400


        params_dict = {

            "razorpay_order_id":
                data["razorpay_order_id"],

            "razorpay_payment_id":
                data["razorpay_payment_id"],

            "razorpay_signature":
                data["razorpay_signature"]
        }


        # Verify Razorpay signature

        client.utility.verify_payment_signature(
            params_dict
        )


        print("PAYMENT SIGNATURE VERIFIED")


        return jsonify({

            "status": "success",

            "message":
                "Payment Successful and Verified!"

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
# DOWNLOAD AND DECODE RAZORPAY QR IMAGE
# =========================================================

def decode_qr_from_url(image_url):

    try:

        print()
        print("================================")
        print("DOWNLOAD RAZORPAY QR IMAGE")
        print("================================")

        print("Image URL:")
        print(image_url)


        # -------------------------------------------------
        # DOWNLOAD IMAGE
        # -------------------------------------------------

        response = requests.get(

            image_url,

            timeout=30,

            allow_redirects=True
        )


        print(
            "Image download status:",
            response.status_code
        )


        print(
            "Downloaded bytes:",
            len(response.content)
        )


        if response.status_code != 200:

            print(
                "ERROR: Could not download QR image"
            )

            return None


        # -------------------------------------------------
        # CONVERT IMAGE BYTES TO NUMPY ARRAY
        # -------------------------------------------------

        image_array = np.frombuffer(

            response.content,

            dtype=np.uint8
        )


        # -------------------------------------------------
        # CONVERT TO OPENCV IMAGE
        # -------------------------------------------------

        image = cv2.imdecode(

            image_array,

            cv2.IMREAD_COLOR
        )


        if image is None:

            print(
                "ERROR: OpenCV could not decode image"
            )

            return None


        print(
            "QR image successfully loaded"
        )


        # -------------------------------------------------
        # QR CODE DETECTOR
        # -------------------------------------------------

        detector = cv2.QRCodeDetector()


        # -------------------------------------------------
        # FIRST ATTEMPT
        # -------------------------------------------------

        qr_text, points, _ = detector.detectAndDecode(
            image
        )


        if qr_text:

            print()
            print("================================")
            print("QR CONTENT FOUND")
            print("================================")
            print(qr_text)
            print("================================")


            return qr_text


        # -------------------------------------------------
        # SECOND ATTEMPT
        # RESIZE IMAGE
        # -------------------------------------------------

        height, width = image.shape[:2]

        print(
            "Original image size:",
            width,
            "x",
            height
        )


        # Make image larger

        resized = cv2.resize(

            image,

            None,

            fx=2,

            fy=2,

            interpolation=cv2.INTER_CUBIC
        )


        qr_text, points, _ = detector.detectAndDecode(
            resized
        )


        if qr_text:

            print()
            print("================================")
            print("QR CONTENT FOUND AFTER RESIZE")
            print("================================")
            print(qr_text)
            print("================================")


            return qr_text


        # -------------------------------------------------
        # THIRD ATTEMPT
        # GRAYSCALE
        # -------------------------------------------------

        gray = cv2.cvtColor(

            resized,

            cv2.COLOR_BGR2GRAY
        )


        qr_text, points, _ = detector.detectAndDecode(
            gray
        )


        if qr_text:

            print()
            print("================================")
            print("QR CONTENT FOUND IN GRAYSCALE")
            print("================================")
            print(qr_text)
            print("================================")


            return qr_text


        # -------------------------------------------------
        # QR NOT FOUND
        # -------------------------------------------------

        print()
        print("================================")
        print("QR CONTENT NOT FOUND")
        print("================================")


        return None


    except Exception as e:

        print()
        print("================================")
        print("QR DECODING ERROR")
        print("================================")
        print(
            "ERROR TYPE:",
            type(e).__name__
        )
        print(
            "ERROR:",
            str(e)
        )
        print("================================")


        return None


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

        print(
            "Received data:",
            data
        )


        # =================================================
        # CHECK AMOUNT
        # =================================================

        if not data or "amount" not in data:

            return jsonify({

                "status": "failed",

                "error": "Amount is required"

            }), 400


        try:

            amount_rupees = int(
                data["amount"]
            )

        except Exception:

            return jsonify({

                "status": "failed",

                "error": "Amount must be a number"

            }), 400


        if amount_rupees <= 0:

            return jsonify({

                "status": "failed",

                "error": "Invalid amount"

            }), 400


        # =================================================
        # CONVERT RUPEES TO PAISE
        # =================================================

        amount_paise = (
            amount_rupees * 100
        )


        # =================================================
        # QR VALID FOR 15 MINUTES
        # =================================================

        close_by = (
            int(time.time())
            + (15 * 60)
        )


        # =================================================
        # RAZORPAY QR DATA
        # =================================================

        qr_data = {

            "type": "upi_qr",

            "name":
                "Coffee Vending Machine",

            "usage":
                "single_use",

            "fixed_amount":
                True,

            "payment_amount":
                amount_paise,

            "description":
                "Coffee payment",

            "close_by":
                close_by,

            "notes": {

                "source":
                    "coffee_vending_machine"
            }
        }


        print()
        print("--------------------------------")
        print("QR DATA")
        print("--------------------------------")

        print(
            "Amount (rupees):",
            amount_rupees
        )

        print(
            "Amount (paise):",
            amount_paise
        )

        print(
            "QR data:",
            qr_data
        )


        # =================================================
        # RAZORPAY QR API
        # =================================================

        razorpay_url = (

            "https://api.razorpay.com"
            "/v1/payments/qr_codes"
        )


        print()
        print("--------------------------------")
        print("RAZORPAY QR API")
        print("--------------------------------")

        print(
            "Sending request to Razorpay..."
        )


        response = requests.post(

            razorpay_url,

            auth=(

                RAZORPAY_KEY_ID,

                RAZORPAY_KEY_SECRET
            ),

            json=qr_data,

            timeout=30
        )


        # =================================================
        # RAZORPAY RESPONSE
        # =================================================

        print()
        print("--------------------------------")
        print("RAZORPAY RESPONSE")
        print("--------------------------------")

        print(
            "HTTP Status:",
            response.status_code
        )

        print(
            "Response:",
            response.text
        )


        # =================================================
        # CHECK RESPONSE
        # =================================================

        if response.status_code not in [200, 201]:

            return jsonify({

                "status": "failed",

                "error":
                    response.text,

                "razorpay_status":
                    response.status_code

            }), 500


        # =================================================
        # READ QR RESPONSE
        # =================================================

        qr = response.json()


        qr_id = qr.get("id")

        qr_status = qr.get("status")

        image_url = qr.get("image_url")

        image_content = qr.get(
            "image_content"
        )


        print()
        print("================================")
        print("RAZORPAY QR CREATED")
        print("================================")

        print(
            "QR ID:",
            qr_id
        )

        print(
            "QR Status:",
            qr_status
        )

        print(
            "QR Image URL:",
            image_url
        )

        print(
            "QR Image Content:",
            image_content
        )

        print("================================")


        # =================================================
        # CHECK QR ID
        # =================================================

        if not qr_id:

            return jsonify({

                "status": "failed",

                "error":
                    "Razorpay did not return QR ID"

            }), 500


        # =================================================
        # CHECK IMAGE URL
        # =================================================

        if not image_url:

            return jsonify({

                "status": "failed",

                "error":
                    "Razorpay did not return QR image URL",

                "qr_id":
                    qr_id

            }), 500


        # =================================================
        # DECODE THE REAL RAZORPAY QR IMAGE
        # =================================================

        print()
        print("================================")
        print("DECODING RAZORPAY QR")
        print("================================")


        upi_content = decode_qr_from_url(
            image_url
        )


        # =================================================
        # QR DECODING FAILED
        # =================================================

        if not upi_content:

            print()
            print(
                "ERROR: Could not decode Razorpay QR"
            )


            return jsonify({

                "status": "failed",

                "error":
                    "Could not decode Razorpay QR image",

                "qr_id":
                    qr_id,

                "image_url":
                    image_url

            }), 500


        # =================================================
        # SUCCESS
        # SEND DATA TO ESP32
        # =================================================

        print()
        print("================================")
        print("QR READY FOR ESP32")
        print("================================")

        print(
            "QR ID:",
            qr_id
        )

        print(
            "UPI content obtained successfully"
        )

        print("================================")


        return jsonify({

    "status": "success",

    "qr_id": qr_id,

    # Decoded Razorpay UPI QR content
    "upi_content": upi_content,

    # ESP32-compatible field
    "image_content": upi_content,

    "image_url": image_url,

    "amount": amount_rupees,

    "amount_paise": amount_paise

})


    except Exception as e:

        print()
        print("================================")
        print("RAZORPAY QR CREATION ERROR")
        print("================================")

        print(
            "ERROR TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            str(e)
        )

        print("================================")


        return jsonify({

            "status":
                "failed",

            "error":
                str(e)

        }), 500


# =========================================================
# CHECK QR PAYMENT STATUS
# =========================================================

@app.route(
    "/check-qr-payment",
    methods=["POST"]
)
def check_qr_payment():

    try:

        data = request.get_json()


        print()
        print("================================")
        print("CHECK QR PAYMENT")
        print("================================")

        print(
            "Received:",
            data
        )


        # =================================================
        # CHECK QR ID
        # =================================================

        if not data or "qr_id" not in data:

            return jsonify({

                "status":
                    "failed",

                "error":
                    "QR ID is required"

            }), 400


        qr_id = data["qr_id"]


        # =================================================
        # RAZORPAY PAYMENT API
        # =================================================

        url = (

            "https://api.razorpay.com"
            "/v1/payments/qr_codes/"
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


        print()
        print("--------------------------------")
        print("RAZORPAY PAYMENT RESPONSE")
        print("--------------------------------")

        print(
            "HTTP Status:",
            response.status_code
        )

        print(
            "Response:",
            response.text
        )


        # =================================================
        # CHECK RESPONSE
        # =================================================

        if response.status_code != 200:

            return jsonify({

                "status":
                    "failed",

                "error":
                    response.text

            }), 500


        payment_data = response.json()


        items = payment_data.get(
            "items",
            []
        )


        # =================================================
        # PAYMENT FOUND
        # =================================================

        if len(items) > 0:

            # Check all returned payments
            for payment in items:

                payment_status = payment.get(
                    "status"
                )


                print(
                    "Payment status:",
                    payment_status
                )


                # =================================================
                # PAYMENT CAPTURED
                # =================================================

                if payment_status == "captured":

                    print()
                    print("================================")
                    print("PAYMENT SUCCESSFUL")
                    print("================================")

                    print(
                        "Payment ID:",
                        payment.get("id")
                    )

                    print(
                        "Amount:",
                        payment.get("amount")
                    )

                    print("================================")


                    return jsonify({

                        "status":
                            "success",

                        "payment_status":
                            "captured",

                        "payment_id":
                            payment.get("id"),

                        "amount":
                            payment.get("amount")
                    })


        # =================================================
        # PAYMENT NOT FOUND YET
        # =================================================

        return jsonify({

            "status":
                "pending",

            "payment_status":
                "pending"

        })


    except Exception as e:

        print()
        print("================================")
        print("QR PAYMENT CHECK ERROR")
        print("================================")

        print(
            "ERROR TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            str(e)
        )

        print("================================")


        return jsonify({

            "status":
                "failed",

            "error":
                str(e)

        }), 500


# =========================================================
# ESP32 TEST ROUTE
# =========================================================

@app.route("/esp32-test")
def esp32_test():

    return jsonify({

        "status":
            "success",

        "message":
            "ESP32 connected to Flask server"

    })


# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )