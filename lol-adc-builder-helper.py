import os, io
import joblib
import requests
import pandas as pd
from PIL import Image
import customtkinter as ctk

# name ALIAS
ITEM_ALIAS = {
    "나보리 명멸검": "나보리",
    "구인수의 격노검": "구인수",
    "루난의 허리케인": "루난",
    "고속 연사포": "고연포",
    "몰락한 왕의 검": "몰락",
    "도미닉 경의 인사": "도미닉",
    "필멸자의 운명": "필멸",
    "요우무의 유령검": "요우무",
    "칠흑의 양날 도끼": "칠흑",

    "라바돈의 죽음모자": "라바돈",
    "리안드리의 고통": "리안드리",
    "라일라이의 수정홀": "라일라이",
    "존야의 모래시계": "존야",
    "대천사의 지팡이": "대천사",
    "대천사의 포옹": "대천사",
}
CHAMP_ALIAS = {
    "Ashe": "애쉬",
    "Corki": "코르키",
    "Caitlyn": "케이틀린",
    "Jhin": "진",
    "Jinx": "징크스",
    "Ezreal": "이즈리얼",
    "Lucian": "루시안",
    "MissFortune": "미스 포츈",
    "Samira": "사미라",
    "Sivir": "시비르",
    "Tristana": "트리스타나",
    "Vayne": "베인",
    "KaiSa": "카이사",
    "Xayah": "자야",
    "Aphelios": "아펠리오스",
    "KogMaw": "코그모",
    "Varus": "바루스",
    "Zeri": "제리",
    "Kalista": "칼리스타",
    "Nilah": "닐라",
    "Ziggs": "직스",
    "Twitch": "트위치",
    "Draven": "드레이븐",
    "Senna": "세나",
    "Azir": "아지르", 
    "Kaisa": "카이사",
    "Smolder": "스몰더",
    "Yunara": "유나라"
}

# ---- utility ----
def fetch_json(url: str, timeout=10): # JSON request
    try:
        return requests.get(url, timeout=timeout).json()
    except Exception as e:
        print("JSON 요청 실패", e)
        return None
    
def load_web_img(url: str, size=None, timeout=10): # WEB image request
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        if size is not None:
            img = img.resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size if size else img.size)
    except Exception as e:
        print("웹 이미지 로드 실패:", e)

        fallback = Image.new("RGBA", size if size else (256, 144), (15, 26, 49, 255))
        return ctk.CTkImage(light_image=fallback, dark_image=fallback, size=fallback.size)
    
def load_img(champ_name: str, size=(100, 100)): # image request
    PATH = os.path.join("images/champions", f"{champ_name}.png")
    img = None

    if os.path.exists(PATH):
        try:
            img = Image.open(PATH).convert("RGBA")
        except Exception as e:
            print(f"이미지 로드 실패 (f{champ_name}):", e)

    if img is None:
        img = Image.new("RGBA", size, (30, 40, 60, 255))  # placeholder

    if size and img.size != size:
        img = img.resize(size, Image.LANCZOS)

    return ctk.CTkImage(light_image=img, dark_image=img, size=size)

# ---- default setting ----
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("ADC-BUILDER for only you")
root.configure(bg="#0A1428")
root.geometry("1600x900")

# ---- Riot Data Dragon ----
VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
def get_last_version() -> str:
    try:
        return requests.get(VERSION_URL, timeout=10).json()[0]
    except Exception as e:
        print("버전 조회 실패", e)
        return "14.10.1"

version = get_last_version()
CHAMP_LIST_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"

def listup_marksmen(): # champ get
    try:
        champion_list = requests.get(CHAMP_LIST_URL).json()["data"] #champ data
    except Exception as e:
        raise RuntimeError(f"챔피언 목록 가져오기 실패: {e}")

    ADC_EXTRAS = {"Ziggs", "Nilah"}
    champions = [name for name, info in champion_list.items() if "Marksman" in info.get("tags", []) or name in ADC_EXTRAS]

    filternotadc = ["Akshan", "Graves", "Jayce", "Kayle", "Kindred", "Quinn", "Teemo", "TwistedFate", "Azir"] #they not adc

    filterchampions = sorted([name for name in champions if name not in filternotadc]) # filtering not adc
    filterchampions = sorted(filterchampions, key=lambda k: CHAMP_ALIAS.get(k, k))
    filterchampions.append("Azir") # Azir is not adc but my fav;
    return filterchampions

RUNE_STYLES = { # rune get
    8000: ("Precision",  "정밀"),
    8100: ("Domination", "지배"),
    8200: ("Sorcery",    "마법"),
    8300: ("Inspiration","영감"),
    8400: ("Resolve",    "결의"),
}
RUNE_ICON_CACHE = {}

def rune_style_name_ko(style_id: int):
    try:
        sid = int(style_id)
    except Exception:
        return None
    rune_name = RUNE_STYLES.get(sid)
    return rune_name[1] if rune_name else None

def load_rune_icon(style_id: int, size=(28, 28)):
    try:
        sid = int(style_id)
    except Exception:
        return None

    key = (sid, size)
    if key in RUNE_ICON_CACHE:
        return RUNE_ICON_CACHE[key]

    PATH = f"images/runes/{sid}.png"
    if not os.path.exists(PATH):
        return print("룬 데이터 로드 실패,")

    try:
        img = Image.open(PATH).convert("RGBA")
        if size and img.size != size:
            img = img.resize(size, Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        RUNE_ICON_CACHE[key] = ctk_img
        return ctk_img
    except Exception as e:
        print(f"룬 아이콘 로드 실패 ({sid}):", e)
        return None

# ---- Item metadata ----
ITEMS_JSON_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/item.json"
_ITEM_META = None

def load_item_meta():
    global _ITEM_META
    if _ITEM_META is not None:
        return _ITEM_META
    try:
        j = fetch_json(ITEMS_JSON_URL)
        _ITEM_META = j.get("data", {}) if j else {}
    except Exception as e:
        print("아이템 메타 로드 실패:", e)
        _ITEM_META = {}
    return _ITEM_META

def is_core_item(item_info: dict) -> bool:
    # only core item > 1600 gold 
    if not item_info:
        return False
    tags = set(item_info.get("tags", []))
    name = item_info.get("name", "")
    gold = (item_info.get("gold") or {}).get("total", 0)

    # exclusive item
    if "Consumable" in tags: return False
    if "Trinket"    in tags: return False
    if "Vision"     in tags: return False
    if "Boots"      in tags: return False
    if "Jungle"     in tags: return False
    if "Support"    in tags: return False
    if any(k in name for k in ["Elixir", "Potion", "Stealth Ward", "Farsight", "Oracle"]):
        return False

    return gold >= 1600

def load_item_icon(item_id: int, size=(40, 40)): #item images get
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{item_id}.png"
    return load_web_img(url, size=size)

def get_core(item_ids):
    # clear grid
    clear_core()

    items = [it for it in item_ids if it] [:3]
    if not items:
        return

    grid = ctk.CTkFrame(core_items_frame, fg_color="transparent")
    grid.pack(padx=8, pady=8, fill="x")

    cols = len(items)
    for c in range(cols):
        grid.grid_columnconfigure(c, weight=1, uniform="core3")
    grid.grid_rowconfigure(0, weight=1)

    meta = load_item_meta()

    for c, it in enumerate(items):
        cell = ctk.CTkFrame(
            grid,
            fg_color="#0F1A31",
            corner_radius=8,
            border_width=1,
            border_color="#334155",
        )
        cell.grid(row=0, column=c, padx=6, pady=6, sticky="nsew")

        icon = load_item_icon(it, size=(48, 48))
        ctk.CTkLabel(cell, text="", image=icon).pack(padx=10, pady=(10, 6))

        info = meta.get(str(it)) or {}
        name_ko = info.get("name", str(it))
        short = ITEM_ALIAS.get(name_ko, name_ko)  

        name_label = ctk.CTkLabel(cell, text=short, text_color="#EAEAEA", justify="center")
        name_label.pack(padx=10, pady=(0, 10))

def clear_core():
    for w in core_items_frame.winfo_children():
        w.destroy()

# ---- CSV data, joblib loader ----
CSV_PATH = "data/my_matches_ml.csv"
MODEL_PATH = "data/my_win_model.joblib"
NUM_MEAN_COLS = ["kills", "deaths", "assists", "goldPerMin", "csPerMin", "dmgPerMin", "visionScore", "xpPerMin"]

def load_stats_df():
    if not os.path.exists(CSV_PATH):
        return None
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig").copy()
    for c in ["champion", "win", "role"]:
        if c not in df.columns:
            raise ValueError(f"CSV에 '{c}' 컬럼이 없습니다.")
    df["role"] = df["role"].astype(str).map(normalize_role)

    if "gameVersion" in df.columns:
        df["patch"] = df["gameVersion"].astype(str).map(to_patch)
    else:
        df["patch"] = ""
    return df

def normalize_role(s: str) -> str:
    s = (s or "").upper()
    if s in ("BOTTOM", "BOT"): return "ADC"
    if s in ("UTILITY",): return "SUPPORT"
    if s == "MIDDLE": return "MID"
    return s or "UNKNOWN"

def to_patch(ver: str) -> str:
    if not isinstance(ver, str) or "." not in ver:
        return ""
    p = ver.split(".")
    return f"{p[0]}.{p[1]}" if len(p) >= 2 else ver

def _safe_mode(series, default=None):
    if len(series) == 0:
        return default
    s = series.dropna()
    if s.empty:
        return default
    return s.mode().iloc[0]

def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        print("모델 로드 실패:", e)
        return None

def get_champ_summary(df: pd.DataFrame, champ: str) -> dict | None:
    sub = df[df["champion"] == champ]
    if sub.empty:
        return None
    total = len(sub)
    wins = int(sub["win"].sum())
    winrate = wins / total if total > 0 else 0.0

    global_queue = int(_safe_mode(df.get("queueId", pd.Series(dtype=float)), 420)) if "queueId" in df.columns else 420
    global_patch = str(_safe_mode(df.get("patch", pd.Series(dtype=object)), ""))

    out = {
        "games": total,
        "wins": wins,
        "winrate": winrate,
        "role_mode": _safe_mode(sub["role"], "-"),
        "rune_primary_mode": int(_safe_mode(sub.get("runePrimary", pd.Series(dtype=float)), 8000))
                                if "runePrimary" in sub.columns else "-",
        "rune_sub_mode": int(_safe_mode(sub.get("runeSub", pd.Series(dtype=float)), 8300))
                                if "runeSub" in sub.columns else "-",
        "queue_mode": int(_safe_mode(sub.get("queueId", pd.Series(dtype=float)), global_queue)) if "queueId" in df.columns else global_queue,
        "patch_mode": str(_safe_mode(sub.get("patch", pd.Series(dtype=object)), global_patch)),
    }
    for c in NUM_MEAN_COLS:
        out[c] = float(sub[c].mean()) if c in sub.columns else 0.0
    return out

# ---- 3 core items from CSV ----
ITEM_COLS = [f"item{i}" for i in range(7)]

def top3_core_items_for_champ(df: pd.DataFrame, champ: str, top=3):
    meta = load_item_meta()
    if not meta:
        return []

    if not all(c in df.columns for c in ITEM_COLS):
        return []  # empty item col

    sub = df[df["champion"] == champ]
    if sub.empty:
        return []

    from collections import Counter
    bag = Counter()

    for _, row in sub[ITEM_COLS].iterrows():
        for it in row.values:
            try:
                it = int(it)
            except Exception:
                continue
            if it <= 0:
                continue
            info = meta.get(str(it))
            if is_core_item(info):
                bag[it] += 1

    if not bag:
        return []

    best = [it for it, _ in bag.most_common(top)]
    return best

# ---- header ----
header = ctk.CTkLabel(
    root,
    text="챔피언을 선택하세요.",
    font=("SEGOE UI", 24),
    text_color="#EAEAEA",
)
header.pack(pady=(10,6))

# ---- container ----
container = ctk.CTkFrame(root, fg_color="#0F1A31", corner_radius=12, border_width=1, border_color="#785A28")
container.pack(fill="both", expand=True, padx=12, pady=12)

container.grid_columnconfigure(0, weight=3, uniform="col")
container.grid_columnconfigure(1, weight=1, uniform="col")
container.grid_rowconfigure(0, weight=1)

# ---- left: champion grid ----
left = ctk.CTkFrame(container, fg_color="#0F1A31", corner_radius=12)
left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

# ---- right: item, stats table ----
right = ctk.CTkFrame(container, fg_color="#0F1A31", corner_radius=12, border_width=1, border_color="#334155")
right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

champ_img_label = ctk.CTkLabel(right, text="", image=None, width=120, height=120, fg_color="transparent")
champ_img_label.pack(pady=(12, 2))

info_title = ctk.CTkLabel(right, text=" ", font=("Segoe UI", 28), text_color="#D4B97E")
info_title.pack(pady=(0, 2))

status_label = ctk.CTkLabel(right, text="챔피언을 선택하면 이곳에\n내 평균 통계가 표시됩니다.", text_color="#EAEAEA", justify="center")
status_label.pack(pady=(0, 0))

core_frame_label = ctk.CTkLabel(right, text="추천 아이템 코어", font=("Segoe UI", 18, "bold"), text_color="#D4B97E")
core_frame_label.pack(pady=(4, 2))

core_items_frame = ctk.CTkFrame(right, fg_color="#0B1428", corner_radius=10)
core_items_frame.pack(fill="x", padx=12, pady=(0, 12))

# ---- data table ----
stats_frame = ctk.CTkFrame(right, fg_color="#0B1428", corner_radius=10)
stats_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
stats_frame.grid_columnconfigure(1, weight=1)
stat_labels = {}

def clear_stats():
    for w in stats_frame.winfo_children():
        w.destroy()
    stats_frame._row = 0    
    stat_labels.clear()

def put_row(key, val):
    r = getattr(stats_frame, "_row", 0)
    key_lbl = ctk.CTkLabel(stats_frame, text=key, text_color="#BFCAD6", anchor="w", font=("SEGOE UI", 18))
    val_lbl = ctk.CTkLabel(stats_frame, text=val, text_color="#EAEAEA", anchor="e", font=("SEGOE UI", 18))
    key_lbl.grid(row=r, column=0, sticky="w", padx=8, pady=3)
    val_lbl.grid(row=r, column=1, sticky="e", padx=8, pady=3)
    stat_labels[key] = val_lbl
    stats_frame._row = r + 1  

def put_row_rune(key, style_id):
    r = getattr(stats_frame, "_row", 0)

    # left: key
    key_label = ctk.CTkLabel(stats_frame, text=key, text_color="#BFCAD6", anchor="w")
    key_label.grid(row=r, column=0, sticky="w", padx=8, pady=1)

    # right: image + name
    cell = ctk.CTkFrame(stats_frame, fg_color="transparent")
    cell.grid(row=r, column=1, sticky="e", padx=8, pady=1)

    icon = load_rune_icon(style_id, size=(28, 28))
    name_ko = rune_style_name_ko(style_id) or str(style_id)

    if icon:
        ctk.CTkLabel(cell, text="", image=icon).pack(side="left", padx=(0, 6))
    ctk.CTkLabel(cell, text=name_ko, text_color="#EAEAEA").pack(side="left")

    stats_frame._row = r + 1

def format_float(x, digits=2):
    try:
        return f"{x:.{digits}f}"
    except Exception:
        return str(x)

# ---- label show, hide ----
def hide_status():
    if status_label.winfo_manager():
        status_label.pack_forget()

def show_status(msg: str):
    status_label.configure(text=msg)
    if not status_label.winfo_manager():
        status_label.pack(pady=(0, 0))

# ---- champion button ----
def on_champion_click(name: str):
    # clear table
    info_title.configure(text=CHAMP_ALIAS.get(name, name))
    clear_stats()
    clear_core()

    show_status("불러오는 중...")

    # get champ img
    ctk_img = load_img(name, size=(180, 180))
    champ_img_label.configure(image=ctk_img, text="")
    champ_img_label.image = ctk_img

    df = load_stats_df() # get data
    
    if df is None:
        show_status("CSV가 없습니다.")
        return

    try:
        summary = get_champ_summary(df, name)
    except Exception as e:
        show_status("요약 중 오류: {e}")
        return

    if summary is None:
        show_status("해당 챔피언으로 플레이한 기록이 없습니다.")
        return

    hide_status()

    # ---- table mean value ----
    put_row("플레이", f"{summary['games']}전 {summary['wins']}승")
    put_row("승률", f"{summary['winrate']*100:.1f}%")
    put_row("포지션", f"{summary['role_mode']}")

    put_row_rune("주 룬", f"{summary['rune_primary_mode']}")
    put_row_rune("부 룬", f"{summary['rune_sub_mode']}")

    put_row("K / D / A", f"{format_float(summary['kills'],1)} / {format_float(summary['deaths'],1)} / {format_float(summary['assists'],1)}")
    put_row("CS/Min", format_float(summary["csPerMin"], 2))
    put_row("Gold/Min", format_float(summary["goldPerMin"], 1))
    put_row("Dmg/Min", format_float(summary["dmgPerMin"], 1))
    put_row("XP/Min", format_float(summary["xpPerMin"], 1))

    # ---- table item core ----
    core3 = top3_core_items_for_champ(df, name, top=3)
    get_core(core3)

    # ---- predict winrate ----
    pipe = load_model()
    if pipe is None:
        put_row("예측 승률", "모델 없음 → analyze_my_winrate.py --train")
        return

    #predict table
    row = {
        "champion": name,
        "role": summary["role_mode"],
        "runePrimary": summary["rune_primary_mode"],
        "runeSub": summary["rune_sub_mode"],
        "queueId": summary["queue_mode"],
        "patch": summary["patch_mode"],
        "kills": summary["kills"],
        "deaths": summary["deaths"],
        "assists": summary["assists"],
        "goldPerMin": summary["goldPerMin"],
        "csPerMin": summary["csPerMin"],
        "dmgPerMin": summary["dmgPerMin"],
        "visionScore": summary["visionScore"],
        "xpPerMin": summary["xpPerMin"],
    }
    X = pd.DataFrame([row])
    try:
        proba = pipe.predict_proba(X)[:, 1][0]
        put_row("예측 승률", f"{proba*100:.1f}%")
    except Exception as e:
        put_row("예측 승률", f"예측 실패: {e}")


# ---- creat button ----
try:
    champs = listup_marksmen()
except RuntimeError as e:
    champs = []
    err = ctk.CTkLabel(left, text=str(e), text_color="#FF7B7B", font=("Segoe UI", 16))
    err.grid(row=0, column=0, padx=8, pady=8, sticky="w")

images = {}
cols = 7
for i, name in enumerate(champs):
    ctk_img = load_img(name, size=(100, 100))
    images[name] = ctk_img

    btn = ctk.CTkButton(
        left,
        text=CHAMP_ALIAS.get(name, name),
        font=("Segoe UI", 16, "bold"),
        fg_color="#1E2328",
        hover_color="#2A3238",
        text_color="#EAEAEA",
        image=ctk_img,
        compound="top",
        corner_radius=10,
        border_color="#785A28",
        border_width=2,
        width=180,
        height=140,
        command=lambda n=name: on_champion_click(n),
    )
    btn.grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="nsew")

for c in range(cols):
    left.grid_columnconfigure(c, weight=1)

root.mainloop()