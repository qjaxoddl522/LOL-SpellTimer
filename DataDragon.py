import requests

def get_latest_version():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)
    versions = response.json()
    return versions[0]  #첫 번째 항목이 최신 버전

def get_champion_name(championId):
    version = get_latest_version()
    url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion.json"
    response = requests.get(url)
    data = response.json()
    champions = data['data']

    for champion in champions.values():
        if int(champion['key']) == championId:
            return champion['name']

    return None #챔피언을 못찾았을 경우(설마 있겠나)

if __name__ == '__main__':
    #예시 사용
    championId = 12
    print(get_champion_name(championId))
