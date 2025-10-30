import customtkinter as ctk
from PIL import Image
import requests

ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.title("상위 1퍼 원딜의 LoL 원딜 빌드 추천기")
root.geometry("1200x900")

version_url = "https://ddragon.leagueoflegends.com/api/versions.json" #Riot Data Dragon url
version = requests.get(version_url).json()[0] #Get version

champion_data_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
champion_data = requests.get(champion_data_url).json()["data"] #champ data
champions = [name for name, info in champion_data.items() if "Marksman" in info["tags"]] 
filternotadc = ["Akshan", "Graves", "Jayce", "Kayle", "Kindred", "Quinn", "Teemo", "TwistedFate", "Azir"] #they not adc

filterchampions = [name for name in champions if name not in filternotadc] #filtering not adc
filterchampions.sort() 
filterchampions.append("Azir") #Azir is not adc but my fav;

images = {}

cols = 5  # 한 줄에 5개씩
for i, name in enumerate(filterchampions):
    img = Image.open(f"images/{name}.png")
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
    images[name] = ctk_img

    btn = ctk.CTkButton(
        root,
        text=name,
        image=ctk_img,
        compound="top",
        width=150,
        height=150,
        command=lambda n=name: print(f"{n} 클릭됨")
    )
    btn.grid(row=i // cols, column=i % cols, padx=5, pady=5, sticky="nsew")

#grid 화면 정렬
for i in range(cols):
    root.grid_columnconfigure(i, weight=1)
for j in range((len(filterchampions) // cols) + 1):
    root.grid_rowconfigure(j, weight=1)

root.mainloop()
