import tkinter as tk
import LCUAPI
import RiotAPI
api_key = 'RGAPI-73aa5947-c143-402e-87a5-d242fca91837' #Riot API 키

#문제점1: 적 챔피언 첫번째가 플레이어로 설정되는 현상
#문제점2: 우주적 통찰력이 제대로 반영되지 않는 현상

#5명의 적 플레이어 정보
#[챔피언, 스펠1, 스펠2, 우주적 통찰력 여부, 쿨감신 여부]
enemyInfo = [{'champ':None, 'spell1':None, 'spell2':None, 'cosmic':False, 'ionia':False} for _ in range(5)]
enemyTeamStart = 0

timer = 3
def startGame(): #UI텍스트 업데이트
    global timer
    global text
    if timer == 1:
        gameData = LCUAPI.checkIngame() #게임을 인식 못하면 None 반환
        if gameData != None:
            name, tag = gameData['activePlayer']['summonerName'].split('#')
            participants = RiotAPI.get_info(api_key, name, tag)
            if participants != None: #게임 찾음
                canvas.itemconfigure(text, text="게임을 찾았습니다!")
                findEnemyRune(name, tag, participants)
                findEnemyInfo(gameData)
                updateEnemyInfo()
                print(enemyInfo)
                return
        timer = 3
    else:
        timer -= 1
    #텍스트 업데이트
    canvas.itemconfigure(text, text=f"게임을 찾는 중...{timer}")
    window.after(1000, startGame)

def findEnemyRune(name, tag, participants): #룬 정보 채우기
    global enemyTeamStart
    for participant in participants:        
        if participant['riotId'] == f"{name}#{tag}": #현재 participant가 플레이어
            #teamId가 100이면 상대는 레드팀
            enemyTeamStart = 5 if participant['teamId'] == 100 else 0
            for i, j in enumerate(range(enemyTeamStart, enemyTeamStart+5)):
                print(participants[j]['riotId'], participants[j]['perks']['perkIds'])
                #우주적 통찰력(8347)이 있으면 True
                enemyInfo[i]['cosmic'] = (8347 in participants[j]['perks']['perkIds'])

def findEnemyInfo(gameData): #최초 적 정보 채우기
    global enemyTeamStart
    players = gameData['allPlayers']
    for i, enemy in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
        print(enemy['championName'], enemyTeamStart)
        enemyInfo[i]['champ'] = enemy['championName']
        enemyInfo[i]['spell1'] = enemy['summonerSpells']['summonerSpellOne']['displayName']
        enemyInfo[i]['spell2'] = enemy['summonerSpells']['summonerSpellTwo']['displayName']
        for item in enemy['items']:
            if item['itemID'] == 3158:
                enemyInfo[i]['ionia'] = True

def updateEnemyInfo(): #적 정보 갱신
    global enemyTeamStart
    while True:
        gameData = LCUAPI.checkIngame()
        if gameData != None:
            players = gameData['allPlayers']
            #챔피언 순서 갱신
            for i, enemy1 in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                if enemyInfo[i]['champ'] != enemy1['championName']:
                    for j, enemy2 in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                        if enemyInfo[i]['champ'] == enemy2['championName']:
                            enemyInfo[i], enemyInfo[j] = enemyInfo[j], enemyInfo[i]
            #적 정보 갱신 
            for i, enemy in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                enemyInfo[i]['spell1'] = enemy['summonerSpells']['summonerSpellOne']['displayName']
                enemyInfo[i]['spell2'] = enemy['summonerSpells']['summonerSpellTwo']['displayName']
                for item in enemy['items']:
                    if item['itemID'] == 3158:
                        enemyInfo[i]['ionia'] = True
        #else:
            break

window = tk.Tk()

#창 설정
window.title("롤 스펠타이머")
window.resizable(False, False) #창 크기 고정
canvas = tk.Canvas(window, width=300, height=100) #캔버스 크기로 창 크기 설정
canvas.pack()

#텍스트 설정
font = ('Malgun Gothic', 20)
text = canvas.create_text(150, 50, text=f"게임을 찾는 중...{timer}", font=font, anchor="center")
window.after(1000, startGame) #텍스트 업데이트

window.mainloop()
