import os
import json

import requests
from flask import Flask, request

app = Flask(__name__)

BOT_ID = os.environ.get("GROUPME_BOT_ID")
ACCESS_TOKEN = os.environ.get("GROUPME_ACCESS_TOKEN")


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

    print("GroupMe bot-post response:", response.status_code)


def get_rsvp_status(event):
    """
    Calculate the current RSVP status from the GroupMe event.

    IMPORTANT:
    Do not use GroupMe's going_count field.
    Testing showed that it does not reliably match going[].
    """

    going = event.get("going") or []
    maybe = event.get("maybe_going") or []
    not_going = event.get("not_going") or []

    return {
        "going": going,
        "maybe": maybe,
        "not_going": not_going,
        "going_count": len(going),
        "maybe_count": len(maybe),
        "not_going_count": len(not_going),
    }

def get_pickleball_status(confirmed_count):
    # Temporary test target.
    # Later we can make this configurable per session.
    TARGET_PLAYERS = 4

    if confirmed_count < TARGET_PLAYERS:
        players_needed = TARGET_PLAYERS - confirmed_count
        status_message = f"{players_needed} more player(s) needed."

    elif confirmed_count == TARGET_PLAYERS:
        status_message = f"We have {confirmed_count} players. Game on! 🏓"

    else:
        extra_players = confirmed_count - TARGET_PLAYERS
        status_message = (
            f"We have {confirmed_count} players — "
            f"{extra_players} over the target."
        )

    return status_message

def get_event_details(group_id, event_id):
    """Retrieve current GroupMe event information."""

    if not ACCESS_TOKEN:
        print("ERROR: GROUPME_ACCESS_TOKEN is not configured.")
        return

    url = (
        f"https://api.groupme.com/v3/conversations/"
        f"{group_id}/events/show"
    )

    try:
        response = requests.get(
            url,
            params={"event_id": event_id},
            headers={"X-Access-Token": ACCESS_TOKEN},
            timeout=10,
        )

        print("EVENT API STATUS:", response.status_code)

        try:
            data = response.json()

            # Pretty-print the complete response.
            print(
                "EVENT API RESPONSE:",
                json.dumps(data, indent=2)
            )

            # Extract the actual event object.
            event = (
                data.get("response", {})
                .get("event")
            )

            if not event:
                print("ERROR: Event data was not found in API response.")
                return

            # Calculate RSVP status from the arrays.
            rsvp = get_rsvp_status(event)

            print("")
            print("========== PICKLEBOT RSVP STATUS ==========")
            print("EVENT:", event.get("name"))
            print("GOING:", rsvp["going"])
            print("MAYBE:", rsvp["maybe"])
            print("NOT GOING:", rsvp["not_going"])
            print("CONFIRMED PLAYER COUNT:", rsvp["going_count"])
            print("MAYBE PLAYER COUNT:", rsvp["maybe_count"])
            print("NOT GOING COUNT:", rsvp["not_going_count"])
            print("===========================================")
            print("")

            return event

        except ValueError:
            print("EVENT API NON-JSON RESPONSE:", response.text)

    except requests.RequestException as exc:
        print("EVENT API REQUEST ERROR:", repr(exc))


@app.route("/", methods=["GET"])
def home():
    return "PickleBot TEST is running! 🏓", 200


@app.route("/callback", methods=["POST"])
def callback():
    message = request.get_json(silent=True) or {}

    print("Received from GroupMe:", message)

    # Ignore messages sent by our bot.
    if message.get("sender_type") == "bot":
        return "OK", 200

    text = str(message.get("text") or "").strip().lower()

    # Preserve our original connectivity test.
    if text == "ping":
        send_groupme_message("Pong! 🏓")

    # Look through the attachments for an Event.
    for attachment in message.get("attachments", []):
        if attachment.get("type") == "event":

            event_id = attachment.get("event_id")
            group_id = message.get("group_id")

            print("EVENT DETECTED")
            print("GROUP ID:", group_id)
            print("EVENT ID:", event_id)

            if group_id and event_id:
                get_event_details(group_id, event_id)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)