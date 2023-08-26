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
