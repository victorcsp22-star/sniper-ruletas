import re

with open("lottobrasil_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Extract script with id="coreJS"
match = re.search(r'<script[^>]*id="coreJS"[^>]*>(.*?)</script>', html, re.DOTALL)
if match:
    core_js = match.group(1)
    print("Found coreJS, length:", len(core_js))
    
    # Save it to a file so we can analyze it
    with open("core.js", "w", encoding="utf-8") as f_out:
        f_out.write(core_js)
    
    # Search for URLs, http, endpoints, websocket, fetch, ajax
    urls = set(re.findall(r'https?://[^\s"\'`<>]+', core_js))
    print("Full URLs:", urls)
    
    paths = set(re.findall(r'["\'](/[a-zA-Z0-9_\-\./]+)["\']', core_js))
    candidate_paths = [p for p in paths if any(k in p.lower() for k in ["sorteio", "result", "bicho", "lot", "api", "data", "date", "jogo", "hora", "post"])]
    print("\nCandidate paths:", candidate_paths[:30])
    
    # Search for keywords like fetch, axios, XMLHttpRequest, socket
    for kw in ["fetch", "axios", "XMLHttpRequest", "WebSocket", "io(", "ajax", "socket"]:
        matches = re.findall(rf'.{{0,30}}{kw}.{{0,40}}', core_js)
        print(f"\nKeyword '{kw}' ({len(matches)} matches):")
        for m in matches[:5]:
            print("  ", m.strip())
else:
    print("coreJS not found!")
