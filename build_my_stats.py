import os, json
import collections
import pandas as pd
from secret_config import MY_PUUID

def open_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

#second -> minute
def per_min(value, dur_sec): return value / max(dur_sec / 60.0, 1e-9)

#most item series
def top_items(series, topk=6):
    bag = collections.Counter()
    for lst in series:
        for it in lst:
            if it and it != 0:
                bag[it] += 1
    return [it for it, _ in bag.most_common(topk)]

def main():
    PATH = "data/my_matches_raw.jsonl"
    if not os.path.exists(PATH):
        raise FileNotFoundError(f"{PATH}가 없습니다. 먼저 load_my_matches.py를 실행하세요.")
    
    #---- get data, make DataFrame
    rows = []
    for raw in open_jsonl(PATH):
        info = raw["info"]
        meta = raw["metadata"]
        dur = info.get("gameDuration", 0)
        parts = info.get("participants", [])

        #only my data
        me = next((p for p in parts if p.get("puuid") == MY_PUUID), None)        
        if me is None:
            continue

        k = me.get("kills", 0)
        d = me.get("deaths", 0)
        a = me.get("assists", 0)
        cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
        dmg = me.get("totalDamageDealtToChampions", 0)
        gold = me.get("goldEarned", 0)
        dur = info.get("gameDuration", 0)

        item_cols = {f"item{i}": me.get(f"item{i}", 0) for i in range(7)}

        rows.append({
            "matchId": meta["matchId"],
            "gameDuration": dur,
            "champion": me.get("championName"),
            "role": (me.get("teamPosition") or me.get("role") or "").upper(),
            "win": int(me.get("win", False)),

            #battle, damage, farming
            "kills": k,
            "deaths": d,                
            "assists": a,
            "kda": (k + a) / max(d, 1),
            "killParticipation": me.get("challenges", {}).get("killParticipation", 0),                
            "gold": gold,
            "goldPerMin": per_min(gold, dur),
            "cs": cs,
            "csPerMin": per_min(cs, dur),
            "dmg": dmg,
            "dmgPerMin": per_min(dmg, dur),
            "damageTaken": me.get("totalDamageTaken", 0),
            "damageMitigated": me.get("damageSelfMitigated", 0),

            #vision, level
            "visionScore": me.get("visionScore", 0),
            "wardsPlaced": me.get("wardsPlaced", 0),
            "wardsKilled": me.get("wardsKilled", 0),
            "champLevel": me.get("champLevel", 0),
            "xp": me.get("champExperience", 0),
            "xpPerMin": per_min(me.get("champExperience", 0), dur),

            #rune, meta
            "gameVersion": info.get("gameVersion", ""),
            "queueId": info.get("queueId", 0),
            "runePrimary": me.get("perks", {}).get("styles", [{}])[0].get("style", None),
            "runeSub": me.get("perks", {}).get("styles", [{}])[1].get("style", None),
            **item_cols,
        })
    
    df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    out_csv = "data/my_matches_ml.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print(f"머신러닝용 CSV 생성 완료 ({len(df)} 경기)")
    print(f"경로: {out_csv}")
    print("컬럼 예시:", list(df.columns)[:12])
    print(df.head(3))

if __name__ == "__main__":
    main()