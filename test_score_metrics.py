import requests
import json
import urllib.parse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
sk = os.environ.get("LANGFUSE_SECRET_KEY")
host = os.environ.get("LANGFUSE_HOST")
auth = (pk, sk)

now = datetime.now(timezone.utc)
week_ago = now - timedelta(days=7)

query = {
  "view": "scores-numeric",
  "fromTimestamp": week_ago.isoformat(),
  "toTimestamp": now.isoformat(),
  "metrics": [
    { "measure": "value", "aggregation": "avg" }
  ],
  "filters": [
    { "type": "string", "column": "name", "operator": "=", "value": "citation_coverage" }
  ]
}

url = f"{host}/api/public/v2/metrics?query={urllib.parse.quote(json.dumps(query))}"
response = requests.get(url, auth=auth)
print(response.status_code)
if response.status_code == 200:
    print(json.dumps(response.json(), indent=2))
else:
    print("Error response text:", response.text)
