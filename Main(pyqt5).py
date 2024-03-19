from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
import sys
import RiotAPI, LCUAPI, DataDragon
api_key = 'RGAPI-73aa5947-c143-402e-87a5-d242fca91837' #Riot API 키

#문제점: 적 챔피언 첫번째가 플레이어로 설정되는 현상

#5명의 적 플레이어 정보
#[챔피언, 스펠1, 스펠2, 우주적 통찰력 여부, 쿨감신 여부]
enemyInfo = [{'champ':None, 'spell1':None, 'spell2':None, 'cosmic':False, 'ionia':False} for _ in range(5)]
enemyTeamStart = 0 #블루팀 레드팀 구분용도

#기본 UI
class UI(QWidget):
    def __init__(self, overlay):
        super().__init__()

        self.overlay = overlay

        self.time = 1
        self.label = QLabel("게임을 찾는 중"+(self.time*"."), self) #위젯 생성
        self.label.setAlignment(Qt.AlignCenter) #라벨 위치 설정
        
        font = self.label.font() #라벨에 사용할 폰트 설정
        font.setPointSize(20)
        font.setFamily('Godo M')
        self.label.setFont(font) #폰트를 라벨에 적용
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        
        self.setLayout(layout)

        # 창 설정
        self.setWindowTitle("롤 스펠타이머")
        self.setFixedSize(300, 100) # 창 크기 고정
        self.show()

        self.timer = QTimer(self)
        #타이머 시간 설정 (1000ms = 1초)
        self.timer.setInterval(1000)
        #타이머가 시간마다 실행할 함수 설정
        self.timer.timeout.connect(self.startGame)
        self.timer.start()

    def startGame(self): #UI텍스트 업데이트
        global enemyTeamStart
        if self.time == 3:
            gameData = LCUAPI.checkIngame() #게임을 인식 못하면 None 반환
            if gameData != None:
                name, tag = gameData['activePlayer']['summonerName'].split('#')
                participants = RiotAPI.get_info(api_key, name, tag)
                if participants != None and len(participants): #RiotAPI 게임 찾음
                    
                    #enemyTeamStart 찾기
                    for participant in participants:
                        if participant['riotId'] == f"{name}#{tag}": #현재 participant가 플레이어
                            #teamId가 100이면 상대는 레드팀
                            enemyTeamStart = 5 if participant['teamId'] == 100 else 0
                            break
                    
                    self.label.setText("게임을 찾았습니다!")
                    self.findEnemyInfo(gameData)
                    self.findEnemyRune(name, tag, participants)
                    self.updateEnemyInfo()
                    print(*enemyInfo, sep='\n')
                    self.timer.stop()
                    return
            self.time = 1
        else:
            self.time += 1
        #텍스트 업데이트
        self.label.setText("게임을 찾는 중"+(self.time*"."))

    def findEnemyInfo(self, gameData): #최초 적 정보 채우기
        global enemyTeamStart
        players = gameData['allPlayers']
        print(players)
        for i, enemy in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
            enemyInfo[i]['champ'] = enemy['championName']
            enemyInfo[i]['spell1'] = enemy['summonerSpells']['summonerSpellOne']['displayName']
            enemyInfo[i]['spell2'] = enemy['summonerSpells']['summonerSpellTwo']['displayName']
            for item in enemy['items']:
                if item['itemID'] == 3158: #쿨감신
                    enemyInfo[i]['ionia'] = True

    def findEnemyRune(self, name, tag, participants): #룬 정보 채우기
        global enemyTeamStart
        for i in range(enemyTeamStart, enemyTeamStart+5):
            for j in range(len(enemyInfo)):
                #챔피언 id와 저장된 챔피언 정보가 같으면 같은 사람
                if DataDragon.get_champion_name(participants[i]['championId']) == enemyInfo[j]['champ']:
                    #우주적 통찰력(8347)이 있으면 True
                    enemyInfo[j]['cosmic'] = (8347 in participants[i]['perks']['perkIds'])
                    break

    def updateEnemyInfo(self): #적 정보 갱신
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

    def closeEvent(self, event):
        self.overlay.close()

#오버레이 UI
class OverlayUI(QWidget):
    def __init__(self):
        super().__init__()

        #레이아웃 지우기 및 오버레이 설정
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel("오버레이 UI", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.setFixedSize(300, 100)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    overlay = OverlayUI()
    ui = UI(overlay)
    
    sys.exit(app.exec_())
