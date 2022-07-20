import requests
import json
import pandas as pd
from tqdm import tqdm
import datetime

url = "http://10.194.9.119:5000/getLoadedModels"

headers = {}

response = requests.request("GET", url, headers=headers)
sent_index = json.loads(response.content)["sentence_index"]
df = pd.read_csv("gamechangerml/src/model_testing/queries.csv")

url = "http://10.194.9.119:5000/transSentenceSearch"

headers = {"Content-Type": "application/json"}
queries = df.queries
model_resp = []
for i in tqdm(queries):
    payload = json.dumps({"text": i})
    response = requests.request("POST", url, headers=headers, data=payload)
    resp = {}
    cont = json.loads(response.content)[0]
    resp["text"] = cont["text"][:300]
    resp["score"] = cont["score"]
    model_resp.append(resp)

new_df = df.copy()
new_df["score"] = [x["score"] for x in model_resp]

new_df["text"] = [x["text"] for x in model_resp]
new_df["model"] = sent_index
time = datetime.datetime.today().strftime("%Y%M%d%M")

new_df.to_csv(f"query_results_{time}.csv")
