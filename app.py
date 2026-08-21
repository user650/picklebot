import os

import requests
from flask import Flask, request

app = Flask(__name__)

BOT_ID = os.environ.get("GROUPME_BOT_ID")


def send_groupme_message(text):
    """Post a message back to GroupMe as our bot."""
    if not BOT_ID:
        print("ERROR: GROUPME_BOT_ID is not configured.")
        return

    response = requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={
            "bot_id": BOT_ID,
            "text": text,
        },
        timeout=10,
    )

    print("GroupMe response:", response.status_code)


@app.route("/", methods=["GET"])
def home():
    return "PickleBot is running! 🏓", 200


@app.route("/callback", methods=["POST"])
def callback():
    message = request.get_json(silent=True) or {}

    print("Received from GroupMe:", message)

    text = str(message.get("text") or "").strip().lower()
    sender_type = message.get("sender_type")

    # Don't respond to bot messages.
    # Otherwise our bot could respond to its own responses.
    if sender_type == "bot":
        return "OK", 200

    if text == "ping":
        send_groupme_message("Pong! 🏓")

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
