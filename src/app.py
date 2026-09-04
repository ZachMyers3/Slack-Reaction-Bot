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
_raw_interval = os.environ.get("SLACK_TARGET_RANDOM_INTERVAL")
SLACK_TARGET_RANDOM_INTERVAL = int(_raw_interval) if _raw_interval else None

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
_emoji_cache = None
_emoji_cache_time = 0
_target_msg_count = 0
# React on the first matching message, then apply the random interval
_target_next_threshold = 1
_self_ids = None

# Subtypes that are channel bookkeeping rather than someone posting content.
# Anything not listed here (file_share, thread_broadcast, me_message,
# bot_message from apps like Giphy, ...) is a real post and gets a reaction.
SYSTEM_SUBTYPES = {
    "message_changed",
    "message_deleted",
    "message_replied",
    "channel_join",
    "channel_leave",
    "channel_archive",
    "channel_unarchive",
    "channel_name",
    "channel_topic",
    "channel_purpose",
    "channel_convert_to_private",
    "channel_convert_to_public",
    "channel_posting_permissions",
    "group_join",
    "group_leave",
    "group_archive",
    "group_unarchive",
    "group_name",
    "group_topic",
    "group_purpose",
    "pinned_item",
    "unpinned_item",
    "ekm_access_denied",
}


def _next_interval_threshold(base):
    """Return a threshold of base ± 20%, always at least 1."""
    variance = max(0, int(base * 0.2))
    low = max(1, base - variance)
    high = max(low, base + variance)
    return random.randint(low, high)


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


def _is_own_message(event):
    """True if this app posted the message.

    Bolt's IgnoringSelfEvents middleware already drops these, so this only
    guards against reacting to our own announcements if that is ever disabled.
    """
    global _self_ids
    if _self_ids is None:
        try:
            auth = app.client.auth_test()
            _self_ids = (auth.get("bot_id"), auth.get("user_id"))
        except Exception:
            _self_ids = (None, None)
    own_bot_id, own_user_id = _self_ids
    return (own_bot_id is not None and event.get("bot_id") == own_bot_id) or (
        own_user_id is not None and event.get("user") == own_user_id
    )


@app.event("message")
def handle_message_event(body, logger):
    global _target_msg_count, _target_next_threshold

    event = body["event"]
    timestamp = event["ts"]
    channel = event["channel"]
    user = event.get("user")

    # Skip channel bookkeeping (edits, joins, deletes) and our own posts.
    # App-posted content such as a Giphy GIF arrives with a bot_id set, so a
    # blanket bot_id check would drop it.
    if event.get("subtype") in SYSTEM_SUBTYPES or _is_own_message(event):
        return

    use_target_emoji = False
    if (
        SLACK_TARGET_USER_ID
        and user == SLACK_TARGET_USER_ID
        and SLACK_TARGET_USER_EMOJI
    ):
        if SLACK_TARGET_RANDOM_INTERVAL:
            _target_msg_count += 1
            if _target_msg_count >= _target_next_threshold:
                use_target_emoji = True
                _target_msg_count = 0
                _target_next_threshold = _next_interval_threshold(
                    SLACK_TARGET_RANDOM_INTERVAL
                )
        else:
            use_target_emoji = True

    emoji = SLACK_TARGET_USER_EMOJI if use_target_emoji else get_emoji()

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
        # App-posted messages (e.g. Giphy) have no team field of their own
        team = message.get("team") or body.get("team_id")

        for reaction in message.get("reactions", []):
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
