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
            pprint.pprint(game_data)
        else:
            print("오류:", response.status_code)
    except requests.exceptions.ConnectionError:
        print("게임이 실행되고 있지 않습니다.")
