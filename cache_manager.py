import json
from datetime import datetime

CACHE_FILE = "cache_logs.json"

def save_log(question,answer,source):
    hallucination = False

    if "I do not know" in answer:
        hallucination = True


    log_entry = {
        "question":question,
        "answer":answer,
        "source":source,
        "hallucination":hallucination,
        "timestamp":str(datetime.now())
    }

    try:
        with open(CACHE_FILE, "r") as file:
            logs =  json.load(file)

    except:
        logs = []

    logs.append(log_entry)
    with open(CACHE_FILE,"w") as file:
        json.dump(logs,file,indent=4)