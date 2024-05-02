# 👍 Slack Reaction Bot

## 📃 Description

A simple slack bot using `slack_bolt` to listen to message events for a given channel and automatically react to them. 

## 🛠️ Installation

### 🤖 Requirements

1. `slack_bolt` requires multiple enviornment variables. 
   1. `SLACK_BOT_TOKEN` which is a valid slack bot token with `reactions:write` and `channels:read` permissions.
   2. `SLACK_SIGNING_SECRET` the signing token for listening to slack events (in our case, incoming messages)
   3. `SLACK_REACTION_EMOJI` the string name of the emoji that we want to auto-react.

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
