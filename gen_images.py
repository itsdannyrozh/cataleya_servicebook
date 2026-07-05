#!/usr/bin/env python3
"""
CATALEYA service-book image generator.
Uses kie.ai GPT Image 2 (text-to-image) via the Market createTask/recordInfo API.

Usage:
    python3 gen_images.py <manifest.json> [--only id1,id2] [--force]

Manifest: a JSON list of objects:
    { "id": "cover-bg", "aspect_ratio": "16:9", "resolution": "2K", "prompt": "..." }

Images are downloaded to assets/generated/<id>.png (idempotent: skips existing
unless --force). A run log is written so we can see failures.
"""
import json, sys, os, time, urllib.request, urllib.error, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.environ.get("KIE_API_KEY", "940c5d23b1a9e01c995486138d9c438b")
BASE = "https://api.kie.ai/api/v1/jobs"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "generated")
CTX = ssl.create_default_context()
WORKERS = int(os.environ.get("KIE_WORKERS", "5"))
RETRIES = 2

def _req(url, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
        return json.loads(r.read().decode())

def create_task(prompt, aspect_ratio="16:9", resolution="2K"):
    body = {
        "model": "gpt-image-2-text-to-image",
        "input": {"prompt": prompt, "aspect_ratio": aspect_ratio, "resolution": resolution},
    }
    resp = _req(f"{BASE}/createTask", "POST", body)
    if resp.get("code") != 200:
        raise RuntimeError(f"createTask failed: {resp}")
    return resp["data"]["taskId"]

def poll(task_id, timeout=900):
    start = time.time()
    delay = 3
    while time.time() - start < timeout:
        resp = _req(f"{BASE}/recordInfo?taskId={task_id}")
        data = resp.get("data", {})
        state = data.get("state")
        if state == "success":
            result = json.loads(data["resultJson"])
            urls = result.get("resultUrls", [])
            if not urls:
                raise RuntimeError(f"success but no urls: {data}")
            return urls[0]
        if state == "fail":
            raise RuntimeError(f"task failed: {data.get('failCode')} {data.get('failMsg')}")
        time.sleep(delay)
        delay = min(delay + 2, 12)
    raise TimeoutError(f"timeout polling {task_id}")

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    return len(data)

def generate_one(item, force=False):
    iid = item["id"]
    path = os.path.join(OUT_DIR, f"{iid}.png")
    if os.path.exists(path) and not force and os.path.getsize(path) > 1000:
        print(f"  [skip] {iid} (exists, {os.path.getsize(path)} bytes)", flush=True)
        return True
    ar = item.get("aspect_ratio", "16:9")
    res = item.get("resolution", "2K")
    last = None
    for attempt in range(1, RETRIES + 2):
        try:
            tid = create_task(item["prompt"], ar, res)
            url = poll(tid)
            n = download(url, path)
            print(f"  [ok  ] {iid}  ({n} bytes){'' if attempt==1 else ' [retry %d]'%attempt}", flush=True)
            return True
        except Exception as e:
            last = e
            print(f"  [warn] {iid} attempt {attempt}: {str(e)[:120]}", flush=True)
            time.sleep(3 * attempt)
    print(f"  [FAIL] {iid}: {last}", flush=True)
    return False

def main():
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = set(args[i+1].split(","))
        args = args[:i] + args[i+2:]
    manifest_path = args[0]
    with open(manifest_path) as f:
        items = json.load(f)
    if only:
        items = [it for it in items if it["id"] in only]
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating {len(items)} image(s) with {WORKERS} workers -> {OUT_DIR}", flush=True)
    ok, fail = 0, 0
    failed_ids = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(generate_one, it, force): it["id"] for it in items}
        for fut in as_completed(futs):
            iid = futs[fut]
            if fut.result():
                ok += 1
            else:
                fail += 1
                failed_ids.append(iid)
    print(f"\nDONE: {ok} ok, {fail} failed")
    if failed_ids:
        print("FAILED IDS:", ",".join(failed_ids))
        sys.exit(1)

if __name__ == "__main__":
    main()
