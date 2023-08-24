# modules
import os
import slack
from pathlib import Path
from dotenv import load_dotenv

# setting the environment variable path using dotenv
environment_variable_path = Path(".") / ".env"
load_dotenv(dotenv_path=environment_variable_path)

# connect slack with python code
client = slack.WebClient(token=os.environ["SLACK_TOKEN"])

client.chat_postMessage(channel="#youtube_bot", text="Hello, world!")
