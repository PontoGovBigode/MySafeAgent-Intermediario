from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
AUTHORIZED_KEYS = {}

@app.route("/register_qrcode", methods=["POST"])
def register_qrcode():
    data = request.json
    qrcode_id = data.get("qrcode_id")
    if not qrcode_id:
        return jsonify({"error": "Missing qrcode_id"}), 400
    AUTHORIZED_KEYS[qrcode_id] = {"authorized": False, "timestamp": str(datetime.datetime.utcnow())}
    return jsonify({"status": "QRCode registered"}), 200

@app.route("/authorize_qrcode", methods=["POST"])
def authorize_qrcode():
    data = request.json
    qrcode_id = data.get("qrcode_id")
    if qrcode_id not in AUTHORIZED_KEYS:
        return jsonify({"error": "Invalid QR Code"}), 404
    AUTHORIZED_KEYS[qrcode_id]["authorized"] = True
    return jsonify({"status": "QRCode authorized"}), 200

@app.route("/check_status/<qrcode_id>", methods=["GET"])
def check_status(qrcode_id):
    data = AUTHORIZED_KEYS.get(qrcode_id)
    if not data:
        return jsonify({"authorized": False}), 404
    return jsonify({"authorized": data["authorized"]}), 200

@app.route("/")
def home():
    return "MySafeAgent Intermediary Server is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
