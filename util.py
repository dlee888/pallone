import os
import json

def get_var(name):
    try:
        return os.environ[name]
    except Exception as e:
        # print(e)
        vars = json.load(open('environment.json'))
        print(name, vars[name])
        return vars[name]