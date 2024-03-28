import requests
import hgtk

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
            return champion['id'] if language != 'ko_KR' else champion['name'] #영어는 id, 한글은 name 리턴
    return None

def get_champion_imageURL(championId):
    version = get_latest_version()
    championName = get_champion_name(championId, 'en_US')
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{championName}.png"
    return url

def get_spell_cooltime(spell, level):
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/summoner.json"
    response = requests.get(url)
    data = response.json()['data']

    spellName = None
    if spell == '방어막':
        spellName = 'SummonerBarrier'
    elif spell == '정화':
        spellName = 'SummonerBoost'
    elif spell == '점화':
        spellName = 'SummonerDot'
    elif spell == '탈진':
        spellName = 'SummonerExhaust'
    elif spell == '점멸':
        spellName = 'SummonerFlash'
    elif spell == '유체화':
        spellName = 'SummonerHaste'
    elif spell == '회복':
        spellName = 'SummonerHeal'
    elif spell == '총명':
        spellName = 'SummonerMana'
    elif spell == '강타':
        spellName = 'SummonerSmite'
    elif spell == '표식':
        spellName = 'SummonerSnowball'
    elif spell == '순간이동' or spell == '강력 순간이동':
        spellName = 'SummonerTeleport'

    return data[spellName]['cooldown'][0] if spell != '강력 순간이동' else 330-(min(10, level)-1)*10

if __name__ == '__main__':
    #예시 사용
    championId = 5
    print(get_champion_name(championId, 'ko_KR'))
    print(get_spell_cooltime('순간이동'))
