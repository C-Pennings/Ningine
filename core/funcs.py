import json

#functions
def load_json(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data
    except:
        raise Exception(f"Error loading json from path: {path}")

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
    except:
        raise Exception(f"Error saving json to path: {path}")