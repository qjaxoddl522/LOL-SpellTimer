from PyQt5.QtWidgets import QApplication, QDesktopWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QStackedLayout
from PyQt5.QtGui import QPixmap, QPixmapCache, QCursor
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
import sys, threading
import RiotAPI, LCUAPI, DataDragon
api_key = 'RGAPI-73aa5947-c143-402e-87a5-d242fca91837' #Riot API 키

#문제점: 적 챔피언 첫번째가 플레이어로 설정되는 현상

#5명의 적 플레이어 정보
#[챔피언, 챔피언ID, 스펠1, 스펠2, 우주적 통찰력 여부, 쿨감신 여부]
enemyInfo = [{'champ':None, 'champId':1, 'spell1':'점멸', 'spell2':'점화', 'cosmic':False, 'ionia':False} for _ in range(5)]
enemyInfo[2]['champId'] = 4
enemyTeamStart = 0 #블루팀 레드팀 구분용도

#기본 UI
class UI(QWidget):
    def __init__(self, overlay):
        super().__init__()

        self.overlay = overlay

        # 창 설정
        self.setWindowTitle("롤 스펠타이머")
        self.setFixedSize(300, 100) # 창 크기 고정
        
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
            threading.Thread(target=self.checkGameData).start()
            self.time = 1
        else:
            self.time += 1
        #텍스트 업데이트
        self.label.setText("게임을 찾는 중"+(self.time*"."))

    def checkGameData(self):
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

                self.timer.stop()
                self.label.setText("게임을 찾았습니다!")
                self.findEnemyInfo(gameData)
                self.findEnemyRune(name, tag, participants)
                self.updateEnemyInfo()
                print(*enemyInfo, sep='\n')
                self.overlay.updateUI(enemyInfo)
    
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
                if DataDragon.get_champion_name(participants[i]['championId'], 'ko_KR') == enemyInfo[j]['champ']:
                    enemyInfo[j]['champId'] = participants[i]['championId']
                    #우주적 통찰력(8347)이 있으면 True
                    enemyInfo[j]['cosmic'] = (8347 in participants[i]['perks']['perkIds'])
                    break

    def updateEnemyInfo(self): #적 정보 갱신
        global enemyTeamStart
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
            self.overlay.updateUI(enemyInfo)

    def closeEvent(self, event):
        self.overlay.close()

#오버레이 UI
class OverlayUI(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("오버레이")
        self.setFixedSize(135, 200)
        self.setStyleSheet("background-color: rgba(127, 127, 127, 255);")
        
        #위치 지정
        screen = QDesktopWidget().screenGeometry()
        self.move(screen.width() - 155, screen.height() - 650)
        
        #레이아웃 지우기 및 오버레이 설정
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        #self.setAttribute(Qt.WA_TranslucentBackground) #배경지우기

        #수직 레이아웃 생성
        self.layout = QVBoxLayout()
        #배경을 채우기 위한 간격 제거
        self.layout.setContentsMargins(5, 0, 5, 0) #왼, 위, 오, 아래
        self.layout.setSpacing(0)
        
        self.updateUI(enemyInfo)

        #마우스 이벤트
        self.mFlag = False #드래그용 마우스 클릭 확인
        self.mPosition = 0, 0

    #UI 배치 겸 업데이트
    def updateUI(self, enemyInfo):
        #기존 위젯 제거
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)

        #이미지 넣고 레이아웃에 배치
        for i in range(len(enemyInfo)):
            #수평 레이아웃(개인용)
            layoutChampion = QHBoxLayout()
            layoutChampion.setSpacing(10)

            #챔피언 이미지 라벨
            label = QLabel(self)
            layoutChampion.addWidget(label)
            
            url = DataDragon.get_champion_imageURL(enemyInfo[i]['champId'])
            pixmap = QPixmapCache.find(url)
            #이미지가 캐시에 없으면 다운로드
            if pixmap == None:
                manager = QNetworkAccessManager(self)
                manager.finished.connect(lambda reply, u=url, l=label:self.handleFinished(reply, u, l))
                manager.get(QNetworkRequest(QUrl(url)))
            #이미지가 캐시에 있으면 사용
            else:
                label.setPixmap(pixmap)
            
            #스펠1 버튼
            buttonSpell1 = QPushButton(self)
            layoutChampion.addWidget(buttonSpell1)
            #버튼에 이미지 설정
            buttonSpell1.setStyleSheet("QPushButton {{border-image: url(spell/{0});}}".format(enemyInfo[i]['spell1']))
            #버튼 크기 설정
            buttonSpell1.setFixedSize(QSize(35, 35))
            
            #스펠2 버튼
            buttonSpell2 = QPushButton(self)
            layoutChampion.addWidget(buttonSpell2)
            #버튼에 이미지 설정
            buttonSpell2.setStyleSheet("QPushButton {{border-image: url(spell/{0});}}".format(enemyInfo[i]['spell2']))
            #버튼 크기 설정
            buttonSpell2.setFixedSize(QSize(35, 35))
            
            self.layout.addLayout(layoutChampion)
        self.setLayout(self.layout)
        self.show()
    
    #설정 후 이미지 불러오기
    def handleFinished(self, reply, url, label):
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)

        #이미지 크기 조절
        pixmap = pixmap.scaled(35, 35, Qt.KeepAspectRatio)

        #라벨에 이미지 설정
        label.setPixmap(pixmap)

        #이미지 캐시에 저장
        QPixmapCache.insert(url, pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mFlag = True
            self.mPosition = event.globalPos() - self.pos() #마우스 위치 저장
            self.setCursor(QCursor(Qt.OpenHandCursor)) #마우스 커서 변경

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.mFlag:
            self.move(event.globalPos() - self.mPosition) #창 위치 이동

    def mouseReleaseEvent(self, event):
        self.mFlag = False
        self.setCursor(QCursor(Qt.ArrowCursor)) #마우스 커서 변경

if __name__ == '__main__':
    app = QApplication(sys.argv)

    overlay = OverlayUI()
    ui = UI(overlay)
    
    sys.exit(app.exec_())
