import os
import requests
from tqdm import tqdm

VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
def get_last_version() -> str:
    try:
        return requests.get(VERSION_URL, timeout=10).json()[0]
    except Exception as e:
        print("버전 조회 실패, 인터넷 연결을 확인하세요.", e)
        return "14.10.1"

version = get_last_version()
CHAMP_LIST_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
print(f"최신 버전: {version}")

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
champion_list = listup_marksmen()

os.makedirs("images", exist_ok=True) #make images dir

#In DDragon, champ info tags, Marksman(adc)
ADC_EXTRAS = {"Ziggs", "Nilah"}

for champ_name in tqdm(champion_list, desc="원딜 챔피언 이미지 다운로드 중"):
    IMG_URL = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ_name}.png"
    IMG_PATH = f"images/{champ_name}.png"

    #if not images, make them
    if not os.path.exists(IMG_PATH):
        IMG_DATA = requests.get(IMG_URL).content
        with open(IMG_PATH, "wb") as f:
            f.write(IMG_DATA)

print("원딜 챔피언 이미지 다운로드 완료")
