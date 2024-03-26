import pprint
import requests

#롤 클라이언트의 실시간 게임 데이터를 가져오는 API URL
url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
headers = {"Accept": "application/json"}

requests.packages.urllib3.disable_warnings() #경고 메시지 비활성화

def checkIngame():
    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            game_data = response.json()
            return game_data
        else:
            return None
    except requests.exceptions.ConnectionError:
        return None

if __name__=="__main__":
    try:
        response = requests.get(url, headers=headers, verify=False)  #SSL 인증서 검사를 무시하기 위해 verify=False를 설정

        if response.status_code == 200:
            game_data = response.json()
            """for i in game_data['allPlayers']:
                print(i)"""
            #print(game_data['activePlayer']['summonerName'])
            pprint.pprint(game_data)
            """
            players = game_data['allPlayers'] #플레이어들의 정보 딕셔너리
            for player in players:
                print(f"챔피언: {player['championName']}")
                print("스펠 정보:")
                for spellNum in player['summonerSpells']:
                    print(f"{player['summonerSpells'][spellNum]['displayName']}")
                print("룬 정보:")
                for rune in player['runes']:
                    print(f"{player['runes'][rune]['displayName']}")
                print("아이템 정보:")
                for item in player['items']:
                    print(f"아이템 이름: {item['displayName']}, 아이템 ID: {item['itemID']}, 슬롯: {item['slot']}")
                print()
            """
        else:
            print("오류:", response.status_code)
    except requests.exceptions.ConnectionError:
        print("게임이 실행되고 있지 않습니다.")
