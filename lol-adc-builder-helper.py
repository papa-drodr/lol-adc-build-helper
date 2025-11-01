import os
import io
import customtkinter as ctk
from tkinter import font
from PIL import Image
import requests

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
        raise RuntimeError(f"챔피언 목록 가져오기 실패", e)

    ADC_EXTRAS = {"Ziggs", "Nilah"}
    champions = [name for name, info in champion_list.items() if "Marksman" in info.get("tags", []) or name in ADC_EXTRAS]

    filternotadc = ["Akshan", "Graves", "Jayce", "Kayle", "Kindred", "Quinn", "Teemo", "TwistedFate", "Azir"] #they not adc

    filterchampions = sorted([name for name in champions if name not in filternotadc]) #filtering not adc
    filterchampions.append("Azir") #Azir is not adc but my fav;
    
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

    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    return ctk_img

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
    print(f"{name} 클릭됨")
    pass
    #TODO new window open

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

for c in range(cols): #make grid
    frame.grid_columnconfigure(c, weight=1)

root.mainloop()
