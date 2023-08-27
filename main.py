# modules
import packages as pack

# setting the environment variable path using dotenv
environment_variable_path = pack.Path(".") / ".env"
pack.load_dotenv(dotenv_path=environment_variable_path)

# flask configuration with slack api
app = pack.Flask(__name__)
slack_event_adapter = pack.SlackEventAdapter(
    pack.os.environ["SIGNING_SECRET"], "/slack/events", app
)

# connect slack with python code
client = pack.slack.WebClient(token=pack.os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]  # get bot id

# empty dictionary
dict_msg_count = {}
welcome_msg = {}


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
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response["ts"]

    if channel not in welcome_msg:
        welcome_msg[channel] = {}

    welcome_msg[channel][user] = welcome


# functions for slack events
@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
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


# slash command (/)
@app.route("/message-count", methods=["POST"])  # /message-count slash command
def message_count():
    data = pack.request.form
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")

    message_count = dict_msg_count.get(user_id, 0)
    client.chat_postMessage(channel=channel_id, text=f"Messages: {message_count}")
    return pack.Response(), 200


# if this specific file is run, then debug=True
if __name__ == "__main__":
    app.run(debug=True)
