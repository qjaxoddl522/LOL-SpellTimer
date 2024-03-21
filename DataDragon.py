import requests

def get_latest_version():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)
    versions = response.json()
    return versions[0]  #첫 번째 항목이 최신 버전

def get_champion_name(championId, language): #ko_KR 또는 en_US
    version = get_latest_version()
    url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/{language}/champion.json"
    response = requests.get(url)
    data = response.json()
    champions = data['data']

    for champion in champions.values():
        if int(champion['key']) == championId:
            return champion['name']
    return None

def get_champion_imageURL(championId):
    version = get_latest_version()
    championName = get_champion_name(championId, 'en_US').replace(' ', '')
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{championName}.png"
    return url

if __name__ == '__main__':
    #예시 사용
    championId = 5
    print(get_champion_name(championId, 'ko_KR'))
    print(get_champion_imageURL(championId))
