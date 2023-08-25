# modules
import os
import slack
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter

# setting the environment variable path using dotenv
environment_variable_path = Path(".") / ".env"
load_dotenv(dotenv_path=environment_variable_path)

# flask configuration with slack api
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app
)

# connect slack with python code
client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]  # get bot id


# functions for slack events
@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")  # get channel id the bot are in
    user_id = event.get("user")  # get user id the user that sent prompt
    text = event.get("text")  # just text

    # send a mirror message to user
    if BOT_ID != user_id:  # to prevent messages from looping
        client.chat_postMessage(channel=channel_id, text=text)


if __name__ == "__main__":
    app.run(debug=True)
