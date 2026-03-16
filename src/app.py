import os
import pathlib
import random
import sys

import dotenv
import inflect
from slack_bolt import App

# Handle PyInstaller bundled executable
if getattr(sys, "frozen", False):
    ABS_PATH = pathlib.Path(sys._MEIPASS).parent
    DOTENV_PATH = ABS_PATH / ".env"
    dotenv.load_dotenv(DOTENV_PATH)
else:
    ABS_PATH = pathlib.Path(__file__).parent.absolute()
    ABS_PATH = ABS_PATH.parent.parent
    dotenv.load_dotenv(dotenv.find_dotenv())

SLACK_REACTION_EMOJI = os.environ.get("SLACK_REACTION_EMOJI")

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

_emoji_cache = None


def get_random_emoji():
    global _emoji_cache
    if _emoji_cache is None:
        result = app.client.emoji_list()
        if result["ok"]:
            # Filter out aliases (url starts with "alias:") to avoid duplicates
            _emoji_cache = [
                name
                for name, url in result["emoji"].items()
                if not url.startswith("alias:")
            ]
    if _emoji_cache:
        return random.choice(_emoji_cache)
    return SLACK_REACTION_EMOJI


@app.event("message")
def handle_message_event(body, logger):
    timestamp = body["event"]["ts"]
    channel = body["event"]["channel"]
    app.client.reactions_add(
        channel=channel, name=get_random_emoji(), timestamp=timestamp
    )


@app.event("reaction_added")
def handle_reaction_added(body, logger):
    timestamp = body["event"]["item"]["ts"]
    channel = body["event"]["item"]["channel"]

    try:
        result = app.client.conversations_history(
            channel=channel, inclusive=True, oldest=timestamp, limit=1
        )
        message = result["messages"][0]
        team = message["team"]

        for reaction in message["reactions"]:
            if reaction["count"] >= 10:
                number_word = (
                    inflect.engine().number_to_words(reaction["count"]).upper()
                )
                timestamp_url = timestamp.replace(".", "")
                reference_url = f"https://{team}.slack.com/archives/{channel}/p{timestamp_url}"
                emoji = f":{SLACK_REACTION_EMOJI}:"
                app.client.chat_postMessage(
                    channel=channel,
                    text=(
                        f"{emoji} {emoji} {emoji}"
                        f" A {number_word} DOGGER HAS ARRIVED "
                        f"{emoji} {emoji} {emoji}"
                        f"\n\n<{reference_url}|.>"
                    ),
                )
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
