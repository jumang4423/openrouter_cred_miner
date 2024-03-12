from openai import OpenAI
import requests
import json
from dotenv import load_dotenv
import os
from os.path import join, dirname
import re

# load .env file
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
CRED_LIST_FILEPATH = os.environ.get("CRED_LIST_FILEPATH")


def check_key(key: str) -> bool:
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )

        client.chat.completions.create(
            model="google/gemma-7b-it:nitro",
            messages=[
                {
                    "role": "system",
                    "content": "RETURN ONLY '0' AS YOUR ASSISTANT RESPONSE",
                }
            ],
            max_tokens=1,
            stream=False,
        )

        # if response has choices[0].content then it's valid
        return True

    except Exception as e:
        print(e)
        return False
    

cred_list = []
with open(CRED_LIST_FILEPATH, 'r') as f:
    data = json.load(f)
    cred_list = data['credentials']

for cred in cred_list:
    print(f"checking if valid...")
    if not check_key(cred):
        # exclude the key from json
        print(f"invalid...")
        print(f"removing {cred} from list...")
        cred_list.remove(cred)
        with open(CRED_LIST_FILEPATH, 'w') as f:
            json.dump({'credentials': cred_list}, f)
