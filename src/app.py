import os
import sys
import pathlib

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
    print(f"{SLACK_REACTION_EMOJI}")
    # post reaction of the message
    app.client.reactions_add(
        channel=channel, name=SLACK_REACTION_EMOJI, timestamp=timestamp
    )


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
