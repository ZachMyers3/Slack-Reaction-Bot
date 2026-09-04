# 👍 Slack Reaction Bot

## 📃 Description

A simple slack bot using `slack_bolt` to listen to message events for a given channel and automatically react to them. 

## 🛠️ Installation

### 🤖 Requirements

1. `slack_bolt` requires multiple environment variables.
   1. `SLACK_BOT_TOKEN` which is a valid slack bot token with `reactions:write` and `channels:read` permissions. Add `emoji:read` if using random mode.
   2. `SLACK_SIGNING_SECRET` the signing token for listening to slack events (in our case, incoming messages)
   3. `SLACK_REACTION_EMOJI` the emoji to react with, or set to `RANDOM` to use a random emoji from your workspace's custom emoji list.
   4. `EMOJI_CACHE_TTL` (optional) how long to cache the emoji list in seconds when using random mode. Defaults to 3600 (1 hour).
   5. `SLACK_TARGET_USER_ID` (optional) if set, this user gets the special handling below. Everyone else still gets the normal emoji (`SLACK_REACTION_EMOJI` / random).
   6. `SLACK_TARGET_USER_EMOJI` (optional) if set along with `SLACK_TARGET_USER_ID`, use this emoji for the target user's messages instead of the default emoji.
   7. `SLACK_TARGET_RANDOM_INTERVAL` (optional) if set along with `SLACK_TARGET_USER_ID` and `SLACK_TARGET_USER_EMOJI`, force the target emoji every N messages from that user (with ±20% random variance). Between those forced reactions the target user gets the normal emoji (`SLACK_REACTION_EMOJI` / random) instead.

### 🐍 Running Locally

1. Install dependencies with `poetry install`
2. Run application with `poetry run python ./src/app.py`

I used ngrok to route my port publically for initial testing.

```bash
ngrok http 3000
```

### 🐋 Running With Docker

The application is designed to be run within the docker container, we can build and then run the app with the following commands.

```bash
docker image build -t slack-reaction-bot .

docker run --rm --name slack-reaction-bot --env SLACK_BOT_TOKEN=xoxb-your-token-here --env SLACK_SIGNING_SECRET=signing-secret-here slack-reaction-bot
```

Pushes to `master` also publish the image to GitHub Container Registry as `ghcr.io/zachmyers3/slack-reaction-bot:latest` and `ghcr.io/zachmyers3/slack-reaction-bot:<short-sha>`.
