from datetime import datetime
import os
from core import config
import json
import requests


def save_data(file):

    now = datetime.now()
    date_and_time: str = now.strftime('%m_%d_%Y_%H_%M_%S')
    path_to_json = os.path.join(config.INPUT_DIRECTORY, f'{date_and_time}.json')
    with open(path_to_json, 'w') as input:
        # Converts the Input in a json document and save it inside the current working directory
        json.dump(file, input)

    return path_to_json

def save_as_json(data, path: str):
    with open(path, "w") as file:
        file.write(json.dumps(data, indent=4))
    return data


def send_response(data, requester, document_id):
    # Make Request
    # Wait until it is finished
    data['document_id'] = document_id
    try:
        response = requests.post(requester, json=data)
        print(response.status_code)
    except requests.exceptions.ConnectionError:
        print("You forgot to start the API. I will try to evaluate the table only with predefined rules.")
    except ConnectionRefusedError:
        print("You forgot to start the API. I will try to evaluate the table only with predefined rules.")