import os
import sys
import pathlib
import json

# Use the package we installed
from slack_bolt import App

import dotenv

if getattr(sys, "frozen", False):
    ABS_PATH = pathlib.Path(sys._MEIPASS).parent
    DOTENV_PATH = ABS_PATH / ".env"
    dotenv.load_dotenv(DOTENV_PATH)
else:
    ABS_PATH = pathlib.Path(__file__).parent.absolute()
    ABS_PATH = ABS_PATH.parent.parent
    dotenv.load_dotenv(dotenv.find_dotenv())

env_file = ABS_PATH / ".env"

SLACK_REACTION_EMOJI = os.environ.get("SLACK_REACTION_EMOJI")

# Initialize your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.event("message")
def handle_message_event(body, logger):
    # get message information from event body
    timestamp = body["event"]["ts"]
    channel = body["event"]["channel"]
    # post reaction of the message
    app.client.reactions_add(
        channel=channel, name=SLACK_REACTION_EMOJI, timestamp=timestamp
    )


@app.event("reaction_added")
def handle_reaction_added(body, logger):
    # get message information from event body
    timestamp = body["event"]["item"]["ts"]
    channel = body["event"]["item"]["channel"]

    try:
        # Call the conversations.history method using the WebClient
        # The client passes the token you included in initialization
        result = app.client.conversations_history(
            channel=channel, inclusive=True, oldest=timestamp, limit=1
        )

        message = result["messages"][0]
        for reaction in message["reactions"]:
            if reaction["count"] >= 10:
                app.client.chat_postMessage(
                    channel=channel,
                    text=(
                        f":{SLACK_REACTION_EMOJI}: :{SLACK_REACTION_EMOJI}: :{SLACK_REACTION_EMOJI}:"
                        " A TEN DOGGER HAS ARRIVED "
                        f":{SLACK_REACTION_EMOJI}: :{SLACK_REACTION_EMOJI}: :{SLACK_REACTION_EMOJI}:"
                    ),
                )

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
