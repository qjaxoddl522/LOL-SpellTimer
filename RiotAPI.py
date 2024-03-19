import requests

def get_puuid(api_key, name, tag):
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}"
    response = requests.get(url)
    return response.json()['puuid']

def get_current_game_info(api_key, puuid):
    url = f"https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}?api_key={api_key}"
    response = requests.get(url)
    return response.json()

def get_info(api_key, name, tag):
    puuid = get_puuid(api_key, name, tag)
    game_info = get_current_game_info(api_key, puuid)
    if 'status' in game_info: #게임을 못찾았을 경우
        return None
    else:
        return game_info['participants']

# 사용 예시
if __name__=="__main__":
    api_key = 'RGAPI-73aa5947-c143-402e-87a5-d242fca91837' #Riot API 키
    name = 'DRX' #계정 닉네임
    tag = '6698' #태그
    print(get_rune_info(api_key, name, tag))
#닉네임 검색으로는 문제가 생길 여지가 있어(닉네임 시스템 바꾸기 이전의 닉네임으로 검색됨),
#activePlayer: summonerName -> 닉네임+태그로 puuid를 얻고 puuid로 게임 관전
