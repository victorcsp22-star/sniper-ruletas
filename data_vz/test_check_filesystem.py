import requests
import json

url = "https://lottobichos.com/FileSystemAndUpdate/checkFileSystem"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

# The JS sent:
# a = [{vistaArray: JSON.stringify([])}, {getFileArray: JSON.stringify(t)}]
# where t is the list of files:
files_to_get = [
    {"url": "/assets/js/geral-bundle.js", "execute": True},
    {"url": "/assets/js/web-bundle.js", "execute": True},
    {"url": "/assets/js/router-bundle.js", "execute": True}
]

# Let's test different payload formats
data_payload = {
    "data": json.dumps([
        {"vistaArray": json.dumps([])},
        {"getFileArray": json.dumps(files_to_get)}
    ])
}

r = requests.post(url, data=data_payload, headers=headers)
print("POST status:", r.status_code, "Length:", len(r.text))
print("Response preview:", r.text[:500])
