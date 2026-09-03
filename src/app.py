import os
import pathlib
import random
import sys
import time

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
EMOJI_CACHE_TTL = int(os.environ.get("EMOJI_CACHE_TTL", 3600))
SLACK_TARGET_USER_ID = os.environ.get("SLACK_TARGET_USER_ID")
SLACK_TARGET_USER_EMOJI = os.environ.get("SLACK_TARGET_USER_EMOJI")

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
_emoji_cache = None
_emoji_cache_time = 0


def _fetch_random_emoji():
    global _emoji_cache, _emoji_cache_time
    if (
        _emoji_cache is None
        or (time.time() - _emoji_cache_time) > EMOJI_CACHE_TTL
    ):
        result = app.client.emoji_list()
        if result["ok"]:
            # Filter out aliases (url starts with "alias:") to avoid duplicates
            _emoji_cache = [
                name
                for name, url in result["emoji"].items()
                if not url.startswith("alias:")
            ]
            _emoji_cache_time = time.time()
    if _emoji_cache:
        return random.choice(_emoji_cache)
    return "thumbsup"


def get_emoji():
    if SLACK_REACTION_EMOJI == "RANDOM":
        return _fetch_random_emoji()
    return SLACK_REACTION_EMOJI


@app.event("message")
def handle_message_event(body, logger):
    timestamp = body["event"]["ts"]
    channel = body["event"]["channel"]
    user = body["event"].get("user")

    # If target user is configured, only react to their messages
    if SLACK_TARGET_USER_ID and user != SLACK_TARGET_USER_ID:
        return

    # Use target user emoji if configured and the user matches, otherwise use default
    emoji = (
        SLACK_TARGET_USER_EMOJI
        if (
            SLACK_TARGET_USER_ID
            and user == SLACK_TARGET_USER_ID
            and SLACK_TARGET_USER_EMOJI
        )
        else get_emoji()
    )

    app.client.reactions_add(channel=channel, name=emoji, timestamp=timestamp)


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
                emoji = f":{get_emoji()}:"
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
