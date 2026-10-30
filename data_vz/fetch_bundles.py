import requests
import json

url = "https://lottobichos.com/FileSystemAndUpdate/checkFileSystem"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

get_file_array = [
    {"url": "/assets/js/geral-bundle.js", "integridad": 0, "size": 0, "execute": True, "update": True},
    {"url": "/assets/js/web-bundle.js", "integridad": 0, "size": 0, "execute": True, "update": True},
    {"url": "/assets/js/router-bundle.js", "integridad": 0, "size": 0, "execute": True, "update": True}
]

data = {
    "vistaArray": json.dumps([]),
    "getFileArray": json.dumps(get_file_array)
}

r = requests.post(url, data=data, headers=headers)
print("Status:", r.status_code)
try:
    res = r.json()
    print("Keys:", res.keys())
    check_file = res.get("checkFile", {})
    files = check_file.get("data", [])
    print(f"Files returned: {len(files)}")
    for f in files:
        if isinstance(f, dict):
            print("File url:", f.get("url"), "size:", len(f.get("file_get_contents", "")))
            with open(f.get("url").split('/')[-1], "w", encoding="utf-8") as out:
                out.write(f.get("file_get_contents", ""))
except Exception as e:
    print("Error parsing json:", e)
    print("Raw text:", r.text[:500])
