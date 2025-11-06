import os, io
import requests
from PIL import Image
import customtkinter as ctk


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

# ---- default setting ----
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("상위 1퍼 원딜의 LoL 원딜 빌드 추천")
root.configure(bg="#0A1428")
root.geometry("1280x755")

# ---- Riot Data Dragon ----
VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
def get_last_version() -> str:
    try:
        return requests.get(VERSION_URL, timeout=10).json()[0]
    except Exception as e:
        print("버전 조회 실패, 인터넷 연결을 확인하세요.", e)
        return "14.10.1"

version = get_last_version()
CHAMP_LIST_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"

def listup_marksmen():  
    try:
        champion_list = requests.get(CHAMP_LIST_URL).json()["data"] #champ data
    except Exception as e:
        raise RuntimeError(f"챔피언 목록 가져오기 실패: {e}")

    ADC_EXTRAS = {"Ziggs", "Nilah"}
    champions = [name for name, info in champion_list.items() if "Marksman" in info.get("tags", []) or name in ADC_EXTRAS]

    filternotadc = ["Akshan", "Graves", "Jayce", "Kayle", "Kindred", "Quinn", "Teemo", "TwistedFate", "Azir"] #they not adc

    filterchampions = sorted([name for name in champions if name not in filternotadc]) # filtering not adc
    filterchampions.append("Azir") # Azir is not adc but my fav;
    
    return filterchampions

# ---- image loader ----
def load_img(champ_name: str, size=(100, 100)):
    PATH = os.path.join("images", f"{champ_name}.png")
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


# ---- UI: 상단 안내 ----
header = ctk.CTkLabel(
    root,
    text="챔피언을 선택하세요.",
    font=("Calibri Bold", 24),
    text_color="#EAEAEA",
)
header.pack(pady=10)

selected_label = ctk.CTkLabel(
    root,
    text="선택: -",
    font=("Calibri Bold", 18),
    text_color="#D4B97E"
)
selected_label.pack(pady=(0, 10))

# ---- scroll ----
frame = ctk.CTkScrollableFrame(root, fg_color="#0F1A31", corner_radius=12, border_width=1, border_color="#785A28")
frame.pack(fill="both", expand=True, padx=12, pady=12)

# ---- btn event ----
def on_champion_click(name: str):
    selected_label.configure(text=f"선택: {name}")
    open_champion_window(name)

# ---- creat btn ----
try:
    champs = listup_marksmen()
except RuntimeError as e:
    champs = []
    error_label = ctk.CTkLabel(frame, text=str(e), text_color="#FF7B7B", font=("Calibri Bold", 16))
    error_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")

images = {}
cols = 7
for i, name in enumerate(champs):
    ctk_img = load_img(name, size=(100, 100))
    images[name] = ctk_img

    btn = ctk.CTkButton(
        frame,
        text=name,
        font=("Calibri Bold", 16, "bold"),
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

for c in range(cols): # make grid
    frame.grid_columnconfigure(c, weight=1)


# ---- champion window ----
def open_champion_window(name: str):
    DETAIL_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{name}.json"
    SPLASH_BASE = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{name}_{{skin}}.jpg"

    win = ctk.CTkToplevel(root)
    win.title(f"{name} • 상세 정보")
    win.geometry("980x640")
    win.configure(fg_color="#0A1428")

    # ---- title and loading ----
    title = ctk.CTkLabel(win, text=f"{name}", font=("Calibri Bold", 24), text_color="#EAEAEA")
    title.pack(pady=(12, 4))

    status_label = ctk.CTkLabel(win, fg_color="#0F1A31", text="데이터 불러오는 중..")
    status_label.pack(pady=(0, 8))

    # ---- main container ----
    container = ctk.CTkFrame(win, fg_color="#0F1A31", corner_radius=12, border_width=1, border_color="#785A28")
    container.pack(fill="both", expand=True, padx=12, pady=12)

    # ---- left, right ----
    container.grid_columnconfigure(0, weight=1, uniform="col")
    container.grid_columnconfigure(1, weight=1, uniform="col")   
    container.grid_rowconfigure(1, weight=1)

    # ---- left(splash, skin) ----
    left = ctk.CTkFrame(container, fg_color="#0F1A31")
    left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(12, 6), pady=12)

    #splash
    splash_label = ctk.CTkLabel(left, text="")
    splash_label.pack(pady=(6, 6))

    #skin
    skin_select = ctk.CTkOptionMenu(left, values=["0"], command=lambda v:None)
    skin_select.pack(pady=(0, 12))

    # ---- right(overview, skill, build) ----
    right = ctk.CTkTabview(container, fg_color="#0F1A31", segmented_button_selected_color="#785A28")
    right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(6, 12), pady=12)

    tab_overview = right.add("개요")
    tab_spells   = right.add("스킬")
    tab_build    = right.add("빌드")

    # overview tap
    overview_text = ctk.CTkTextbox(tab_overview, fg_color="#0B1428", text_color="#EAEAEA", wrap="word", height=200)
    overview_text.pack(fill="both", expand=True, padx=10, pady=10)

    # skill tap
    spells_frame = ctk.CTkScrollableFrame(tab_spells, fg_color="#0B1428", corner_radius=8)
    spells_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # TODO build tap
    build_hint = ctk.CTkLabel(tab_build, text="여기에 룬/아이템 추천을 붙일 예정입니다.", text_color="#EAEAEA")
    build_hint.pack(pady=10)

    # ---- data load ----
    data = fetch_json(DETAIL_URL)
    if not data:
        status_label.configure(text="데이터 로드 실패")
        return
    
    try:
        champ = data["data"][name]
    except KeyError:
        status_label.configure(text="챔피언 데이터가 비어있습니다.")
        return
    
    lore = champ.get("lore", "설명이 없습니다.")
    tags = ", ".join(champ.get("tags", [])) or "-"
    overview_text.insert("1.0", f"[역할] {tags}\n\n{lore}")
    overview_text.configure(state="disabled")

    # skin collecion
    skins = champ.get("skins", [])
    skins_ids = [str(s.get("num", 0)) for s in skins] or ["0"]
    skins_name = [s.get("name", "Skin") for s in skins] or ["Classic"]

    # splash load
    def set_splash(skin_num: str):
        url = SPLASH_BASE.format(skin=skin_num)
        img = load_web_img(url,  size=(460, 260))
        splash_label.configure(image=img, text="")
        splash_label.image = img

    # skin select menu
    display_values = [f"{i}. {n}" if n.lower() != "default" else f"{i}. Classic" for i, n in zip(skins_ids, skins_name)]
    skin_select.configure(values=display_values, command=lambda v: set_splash(v.split(".")[0]))
    set_splash(skins_ids[0])

    # skill menu
    passive = champ.get("passive", {})
    spells = champ.get("spells", [])

    def add_spell_row(parent, label, name, desc):
        row = ctk.CTkFrame(parent, fg_color="#0E1A2E", corner_radius=8)
        row.pack(fill="x", padx=6, pady=6)
        title = ctk.CTkLabel(row, text=f"{label} {name}", text_color="#EAEAEA", font=("Calibri Bold", 16))
        title.pack(anchor="w", padx=8, pady=(6, 0))
        body  = ctk.CTkLabel(row, text=desc, text_color="#BFCAD6", wraplength=540, justify="left")
        body.pack(anchor="w", padx=8, pady=(2, 8))

    # add passive
    add_spell_row(spells_frame, "P", passive.get("name", "Passive"),
                  passive.get("description", "No description."))

    # add Q W E R
    keys = ["Q", "W", "E", "R"]
    for k, sp in zip(keys, spells):
        add_spell_row(spells_frame, k, sp.get("name", "Skill"), sp.get("description", "No description."))

    status_label.configure(text="로드 완료")



root.mainloop()
