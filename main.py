# modules
import os
import slack
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import string

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

# empty dictionary
dict_msg_count = {}
welcome_msg = {}

# banned words dictionary
banned_words = ["bad", "word"]


# welcome prompt to user dm's
class WelcomeMessage:
    START_TEXT = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Welcome to this awesome channel! \n\n"
                "*Get started by completing the tasks!*"
            ),
        },
    }

    DIVIDER = {"type": "divider"}

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.completed = False

    def get_message(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": "Welcome Robot!",
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task(),
            ],
        }

    def _get_reaction_task(self):
        checkmark = ":white_check_mark:"

        if not self.completed:
            checkmark = ":white_large_square:"

        text = f"{checkmark} *React to this message!*"

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        }


def send_welcome_msg(channel, user):
    if channel not in welcome_msg:
        welcome_msg[channel] = {}

    if user in welcome_msg[channel]:
        return

    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response["ts"]

    welcome_msg[channel][user] = welcome


# functions for filtering words
def check_banned_words(message):
    msg = message.lower()
    msg = msg.translate(str.maketrans("", "", string.punctuation))

    return any(word in msg for word in banned_words)


# route for slack events
@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")  # get channel id the bot are in
    user_id = event.get("user")  # get user id the user that sent prompt
    text = event.get("text")  # just text

    # send a mirror message to user
    if user_id is not None and BOT_ID != user_id:  # to prevent messages from looping
        if user_id in dict_msg_count:
            dict_msg_count[user_id] += 1
        else:
            dict_msg_count[user_id] = 1

        if text.lower() == "start":
            send_welcome_msg(f"@{user_id}", user_id)
        elif check_banned_words(text):
            ts = event.get("ts")
            client.chat_postMessage(  # send warning to user if user type banned words
                channel=channel_id, thread_ts=ts, text="THAT IS A BAD WORD!"
            )


# route for slack reactions
@slack_event_adapter.on("reaction_added")
def reaction(payload):
    event = payload.get("event", {})
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")

    if f"@{user_id}" not in welcome_msg:
        return

    welcome = welcome_msg[f"@{user_id}"][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message["ts"]


# slash command (/)
@app.route("/message-count", methods=["POST"])  # /message-count slash command
def message_count():
    data = request.form
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")

    message_count = dict_msg_count.get(user_id, 0)
    client.chat_postMessage(channel=channel_id, text=f"Messages: {message_count}")
    return Response(), 200


# if this specific file is run, then debug=True
if __name__ == "__main__":
    app.run(debug=True)
