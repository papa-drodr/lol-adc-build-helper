import os, time, json
import requests
from urllib.parse import quote
from tqdm import tqdm

#API key and name 
from secret_config import RIOT_API_KEY, MY_PUUID

HEADERS = {"X-Riot-Token": RIOT_API_KEY}
REGION_CLUSTER = "asia"

#QUEUE filter | solo rank = 420
QUEUE_ID = 420

# ---- get match data ----
def list_match_ids(puuid: str, total=300, start_time=None, queue=None):
    url = f"https://{REGION_CLUSTER}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    got, start = [], 0
    while len(got) < total:
        remain = total - len(got)
        count = min(100, remain)
        params = {"start": start, "count": count}
        if start_time: params["startTime"] = int(start_time)
        if queue: params["queue"] = int(queue)

        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()

        batch = r.json()
        if not batch:
            break
        got.extend(batch)
        start += len(batch)
        if len(batch) < count:
            break
        time.sleep(0.5)
    return got

def get_match_detail(mid, retry=3):
    url = f"https://{REGION_CLUSTER}.api.riotgames.com/lol/match/v5/matches/{mid}"
    for i in range(retry):
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            wait = 60 * (i + 1)   # 1분 → 2분 → 3분 점진 대기
            print(f"429 Too Many Requests → {wait}s 대기 후 재시도...")
            time.sleep(wait)
        else:
            print(f"skip {mid} ({r.status_code})")
            return None
    return None
def main():
    # 2025-01-08 00:00 UTC, season 15 start
    season_start = 1736294400  

    match_ids = list_match_ids(MY_PUUID, total=1000, start_time=season_start, queue=QUEUE_ID)
    os.makedirs("data", exist_ok=True)

    saved = 0
    out_path = "data/my_matches_raw.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for mid in tqdm(match_ids, desc="load matches"):
            try:
                m = get_match_detail(mid)
                if MY_PUUID in m.get("metadata", {}).get("participants", []):
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
                    saved += 1

                    time.sleep(0.5)
            except Exception as e:
                print("skip", mid, e)

    print(f"저장 완료: {saved}개의 매치 -> {out_path}")

if __name__ == "__main__":
    main()