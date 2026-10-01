import json
import os
from config import Config

def read_db(name):
    path = os.path.join(Config.DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_db(name, data):
    path = os.path.join(Config.DATA_DIR, f"{name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id(collection):
    if not collection:
        return "1"
    max_id = max(int(item['id']) for item in collection)
    return str(max_id + 1)

def find_by_id(collection, id):
    return next((item for item in collection if item['id'] == str(id)), None)

def find_index_by_id(collection, id):
    for i, item in enumerate(collection):
        if item['id'] == str(id):
            return i
    return -1