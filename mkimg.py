import os
import requests
from tqdm import tqdm

version_url = "https://ddragon.leagueoflegends.com/api/versions.json" #Riot Data Dragon url
version = requests.get(version_url).json()[0] #get version
print(f"🔹 최신 버전: {version}")

champion_data_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
champion_data = requests.get(champion_data_url).json()["data"] #champ data

os.makedirs("images", exist_ok=True) #make images dir

#In DDragon, champ info tags, Marksman(adc)
adc_champions = [name for name, info in champion_data.items() if "Marksman" in info["tags"]] 

for champ_name in tqdm(adc_champions, desc="원딜 챔피언 이미지 다운로드 중"):
    img_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ_name}.png"
    img_path = f"images/{champ_name}.png"

    #if not images, make them
    if not os.path.exists(img_path):
        img_data = requests.get(img_url).content
        with open(img_path, "wb") as f:
            f.write(img_data)

print("원딜 챔피언 이미지 다운로드 완료")
