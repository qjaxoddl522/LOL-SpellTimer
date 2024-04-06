from pprint import pprint

from PyQt5.QtWidgets import QApplication, QDesktopWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QPixmapCache, QCursor, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
import sys, threading, time, keyboard
import RiotAPI, LCUAPI, DataDragon
api_key = 'RGAPI-73aa5947-c143-402e-87a5-d242fca91837' #Riot API 키

#5명의 적 플레이어 정보
#[챔피언, 챔피언ID, 스펠1, 스펠2, 스펠1쿨타임, 스펠2쿨타임, 우주적 통찰력 여부, 쿨감신 여부]
enemyInfo = [{'champ':'애니', 'champId':i+1, 'spell1':'점멸', 'spell2':'점화', 'spell1CT':0, 'spell2CT':0, 'level':0, 'timerThread':[None, None],'cosmic':False, 'ionia':False} for i in range(5)]
enemyTeamStart = 0 #블루팀 레드팀 구분용도
gameMode = None #현재 게임 모드(협곡, 칼바람)
spellText = '' #스펠 정보 텍스트(채팅용)
ingameTime = [0, time.time()] #[마지막으로 저장된 게임 시간, 실제 시간(api 호출 간격 시간차 고려를 위함)]

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
        font.setFamily('나눔고딕')
        self.label.setFont(font) #폰트를 라벨에 적용
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        self.show()

        self.timer = QTimer()
        #타이머가 시간마다 실행할 함수 설정
        self.timer.timeout.connect(self.startGame)
        #타이머 시간 설정 (1000ms = 1초)
        self.timer.start(1000)

    # UI텍스트 업데이트 및 시작 확인
    def startGame(self):
        global enemyTeamStart
        if self.time == 3:
            threading.Thread(target=self.checkGameData).start()
            self.time = 1
        else:
            self.time += 1
        #텍스트 업데이트
        self.label.setText("게임을 찾는 중"+(self.time*"."))

    #게임 시작 확인 및 오버레이 UI 작동
    def checkGameData(self):
        global enemyTeamStart, gameMode
        gameData = LCUAPI.checkIngame() #인식 못하면 None 반환
        if gameData != None and (gameData['gameData']['gameMode'] in ("CLASSIC", "ARAM")) and gameData['events']['Events']: #인게임 데이터 확인
            name, tag = gameData['activePlayer']['summonerName'].split('#')
            participants = RiotAPI.get_info(api_key, name, tag)
            if participants != None: #RiotAPI 게임 인식
                gameMode = gameData['gameData']['gameMode']
                #enemyTeamStart 찾기
                for participant in participants:
                    if participant['riotId'] == f"{name}#{tag}": #현재 participant가 플레이어
                        #teamId가 100이면 상대는 레드팀
                        enemyTeamStart = 5 if participant['teamId'] == 100 else 0
                        break

                self.timer.stop()
                self.label.setText("게임을 찾았습니다!")
                self.findEnemyInfo(gameData)
                self.findEnemyRune(participants)
                self.overlay.signalUI.emit()
                keyboard.add_hotkey('alt', self.overlay.pasteSpellText)
                threading.Thread(target=self.checkGameEnd).start()
                pprint(enemyInfo)

    #게임이 끝났는지 확인 및 정보 갱신
    def checkGameEnd(self):
        while self.overlay.stopSignal is False:
            gameData = LCUAPI.checkIngame()
            if gameData != None: #인게임 인식
                global ingameTime
                ingameTime = [round(gameData['gameData']['gameTime']), time.time()]
                self.updateEnemyInfo(gameData)
                time.sleep(3)
                continue
            break
        # 게임을 인식 못했을 경우 = 게임이 끝났을 경우
        self.close()  # 종료(closeEvent 작동)

    # 최초 적 정보 채우기
    def findEnemyInfo(self, gameData):
        global enemyTeamStart
        players = gameData['allPlayers']
        for i, enemy in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
            enemyInfo[i]['champ'] = enemy['championName']
            enemyInfo[i]['spell1'] = enemy['summonerSpells']['summonerSpellOne']['displayName']
            enemyInfo[i]['spell2'] = enemy['summonerSpells']['summonerSpellTwo']['displayName']
            enemyInfo[i]['level'] = enemy['level']
            for item in enemy['items']:
                if item['itemID'] == 3158: #쿨감신
                    enemyInfo[i]['ionia'] = True

    # 룬 정보 채우기
    def findEnemyRune(self, participants):
        global enemyTeamStart
        for i in range(enemyTeamStart, enemyTeamStart+5):
            for j in range(len(enemyInfo)):
                #챔피언 id와 저장된 챔피언 정보가 같으면 같은 사람
                if DataDragon.get_champion_name(participants[i]['championId'], 'ko_KR') == enemyInfo[j]['champ']:
                    enemyInfo[j]['champId'] = participants[i]['championId']
                    #우주적 통찰력(8347)이 있으면 True
                    enemyInfo[j]['cosmic'] = (8347 in participants[i]['perks']['perkIds'])
                    break

    # 적 정보 갱신
    def updateEnemyInfo(self, gameData):
        global enemyTeamStart
        flag = False  #정보가 바뀌었는지 확인하는 플래그
        if gameData != None:
            players = gameData['allPlayers']
            #챔피언 순서 갱신
            for i, enemy1 in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                if enemyInfo[i]['champ'] != enemy1['championName']:
                    for j, enemy2 in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                        if enemyInfo[i]['champ'] == enemy2['championName']:
                            enemyInfo[i], enemyInfo[j] = enemyInfo[j], enemyInfo[i]
                            flag = True
                            
            #적 정보 갱신
            for i, enemy in enumerate(players[enemyTeamStart : enemyTeamStart+5]):
                if enemyInfo[i]['level'] != enemy['level']: #레벨은 UI를 갱신하지 않아도 됨
                    enemyInfo[i]['level'] = enemy['level']

                for dataSpellNum, infoSpellNum in zip(('summonerSpellOne', 'summonerSpellTwo'), ('spell1', 'spell2')):
                    #'강타'가 포함된 스펠(원시의 강타 등)들을 모두 '강타'로 취급
                    if '강타' in enemy['summonerSpells'][dataSpellNum]['displayName']:
                        enemy['summonerSpells'][dataSpellNum]['displayName'] = '강타'
                    #'마법공학 점멸'을 점멸로 취급
                    if '점멸' in enemy['summonerSpells'][dataSpellNum]['displayName']:
                        enemy['summonerSpells'][dataSpellNum]['displayName'] = '점멸'
                    #날아갈 수 있는 상태의 표식은 공백으로 표시되므로 이전 스펠 그대로 적용
                    if enemy['summonerSpells'][dataSpellNum]['displayName'] == '':
                        enemy['summonerSpells'][dataSpellNum]['displayName'] = enemyInfo[i][infoSpellNum]

                    #이외의 변화한 스펠은 반영
                    #print(enemyInfo[i][infoSpellNum], enemy['summonerSpells'][dataSpellNum]['displayName'])
                    if enemyInfo[i][infoSpellNum] != enemy['summonerSpells'][dataSpellNum]['displayName']:
                        enemyInfo[i][infoSpellNum] = enemy['summonerSpells'][dataSpellNum]['displayName']
                        flag = True

                for item in enemy['items']:
                    if item['itemID'] == 3158: #쿨감신
                        if not enemyInfo[i]['ionia']:
                            enemyInfo[i]['ionia'] = True
                            flag = True

            #수정된 사항이 있으면 UI 갱신
            if flag is True:
                self.overlay.signalUI.emit()

    #창 닫을 때 함께 종료
    def closeEvent(self, event):
        self.overlay.stopSignal = True
        self.overlay.close()
        self.timer.stop()

overlayUISize = 35 #아이콘UI 길이
#오버레이 UI
class OverlayUI(QWidget):
    signalUI = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.signalUI.connect(self.refreshUI)
        
        self.setWindowTitle("오버레이")
        self.setFixedSize(135, 200)
        self.setStyleSheet("background-color: rgba(127, 127, 127, 255);")
        
        #위치 지정
        screen = QDesktopWidget().screenGeometry()
        self.move(screen.width() - 155, screen.height() - 650)
        
        #레이아웃 지우기 및 오버레이 설정
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        #self.setAttribute(Qt.WA_TranslucentBackground) #배경지우기

        # 스레드를 종료시키기 위한 시그널
        self.stopSignal = False
        # 마우스 이벤트
        self.mFlag = False  # 드래그용 마우스 클릭 확인
        self.mPosition = 0, 0
        
        self.initUI()

        #self.signalUI.emit()
        #self.show()

    #UI 초기 생성
    def initUI(self):
        #수직 레이아웃 생성
        self.layout = QVBoxLayout()
        #배경을 채우기 위한 간격 제거
        self.layout.setContentsMargins(5, 0, 5, 0) #왼, 위, 오, 아래
        self.layout.setSpacing(0)

        #폰트 불러오기
        fontDB = QFontDatabase()
        fontID = fontDB.addApplicationFont('JetBrainsMono-Bold.ttf')
        fontName = fontDB.applicationFontFamilies(fontID)[0]

        #각 위젯 생성
        self.layoutChampion = [QHBoxLayout() for _ in range(len(enemyInfo))]
        self.imageLabel = [QLabel(self) for _ in range(len(enemyInfo))]
        self.buttonSpell1 = [QPushButton(self) for _ in range(len(enemyInfo))]
        self.buttonSpell2 = [QPushButton(self) for _ in range(len(enemyInfo))]
        
        #레이아웃에 배치
        for i in range(len(enemyInfo)):
            #수평 레이아웃(개인용)
            self.layoutChampion[i].setSpacing(10)

            #챔피언 이미지 라벨
            self.layoutChampion[i].addWidget(self.imageLabel[i])

            for j, buttonSpell in enumerate((self.buttonSpell1[i], self.buttonSpell2[i])):
                #스펠 버튼 챔피언 레이아웃에 추가
                self.layoutChampion[i].addWidget(buttonSpell)
                #버튼 폰트, 크기 설정
                buttonSpell.setFont(QFont(fontName, 11))
                buttonSpell.setFixedSize(QSize(overlayUISize, overlayUISize))
                #버튼 클릭
                buttonSpell.clicked.connect(lambda trash=False, i=i, j=j : self.onButtonClicked(i, str(j+1)))

            self.layout.addLayout(self.layoutChampion[i])
        self.setLayout(self.layout)

    #UI 새로고침
    def refreshUI(self):
        for i in range(len(enemyInfo)):
            url = DataDragon.get_champion_imageURL(enemyInfo[i]['champId'])
            pixmap = QPixmapCache.find(url)
            #이미지가 캐시에 없으면 다운로드
            if pixmap == None:
                manager = QNetworkAccessManager(self)
                manager.finished.connect(lambda reply, u=url, l=self.imageLabel[i] : self.handleFinished(reply, u, l))
                manager.get(QNetworkRequest(QUrl(url)))
            #이미지가 캐시에 있으면 사용
            else:
                self.imageLabel[i].setPixmap(pixmap)

            for j, buttonSpell in enumerate((self.buttonSpell1[i], self.buttonSpell2[i])):
                j = str(j+1)
                #버튼 이미지 설정
                imgName = enemyInfo[i][f'spell{j}'] + ('CT' if enemyInfo[i][f'spell{j}CT'] > 0 else '')
                buttonSpell.setStyleSheet("QPushButton {{border-image: url(spell/{0}); color: white}}".format(imgName))

                #버튼 텍스트 설정
                buttonSpell.setText('{0}:{1:02d}'.format(enemyInfo[i]['spell'+j+'CT'] // 60,
                                                         enemyInfo[i]['spell'+j+'CT'] % 60
                                                         ) if enemyInfo[i]['spell'+j+'CT'] > 0 else '')
        self.show()

    #설정 후 이미지 불러오기
    def handleFinished(self, reply, url, label):
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)

        #이미지 크기 조절
        pixmap = pixmap.scaled(overlayUISize, overlayUISize, Qt.KeepAspectRatio)

        #라벨에 이미지 설정
        label.setPixmap(pixmap)

        #이미지 캐시에 저장
        QPixmapCache.insert(url, pixmap)

    #버튼 클릭
    def onButtonClicked(self, player, spellNum): #(오버레이 객체, 적 번호, 스펠 번호)
        btn = self.sender()
        if enemyInfo[player]['spell'+spellNum+'CT'] == 0: #타이머 정지 상태
            btn.setStyleSheet("QPushButton {{border-image: url(spell/{0}CT); color: white;}}".format(enemyInfo[player]['spell'+spellNum]))

            #쿨타임 가져오기 및 계산
            cooltime = DataDragon.get_spell_cooltime(enemyInfo[player]['spell'+spellNum], enemyInfo[player]['level'])
            spellHaste = (18 if enemyInfo[player]['cosmic'] else 0) + (12 if enemyInfo[player]['ionia'] else 0) + (70 if gameMode == "ARAM" else 0)
            cooltime = round(cooltime * (1 - (spellHaste / (100 + spellHaste))))

            enemyInfo[player]['spell'+spellNum+'CT'] = cooltime-1
            string = '{0}:{1:02d}'.format(enemyInfo[player]['spell' + spellNum + 'CT'] // 60,
                                          enemyInfo[player]['spell' + spellNum + 'CT'] % 60)
            btn.setText(string)

            enemyInfo[player]['timerThread'][int(spellNum)-1] = threading.Timer(1, self.updateTimer, args=[player, spellNum, enemyInfo[player]['champId']])
            enemyInfo[player]['timerThread'][int(spellNum)-1].start()
        else: #타이머가 돌아가고 있음
            enemyInfo[player]['timerThread'][int(spellNum)-1].cancel()
            btn.setStyleSheet("QPushButton {{border-image: url(spell/{0});}}".format(enemyInfo[player]['spell' + spellNum]))
            enemyInfo[player]['spell'+spellNum+'CT'] = 0
            btn.setText('')
        #클립보드 갱신
        self.refreshSpellText()

    # 타이머 작동
    # 챔피언 id를 받는 이유는 타이머가 작동할 때 챔피언 순서가 바뀌었는지 확인하기 위함
    def updateTimer(self, player, spellNum, champId):
        if self.stopSignal is True: #프로그램 중지 시그널 확인
            return
        #순서가 바뀌었으면 바뀐 챔피언 인덱스를 찾아 player 변경
        if enemyInfo[player]['champId'] != champId:
            for i, enemy in enumerate(enemyInfo):
                if enemy['champId'] == champId:
                    player = i
                    champId = enemyInfo[player]['champId']

        if enemyInfo[player]['spell' + spellNum + 'CT'] > 0:
            enemyInfo[player]['spell' + spellNum + 'CT'] -= 1
            string = '{0}:{1:02d}'.format(enemyInfo[player]['spell' + spellNum + 'CT'] // 60,
                                      enemyInfo[player]['spell' + spellNum + 'CT'] % 60)
            getattr(self, 'buttonSpell' + str(spellNum))[player].setText(string)
            enemyInfo[player]['timerThread'][int(spellNum) - 1] = threading.Timer(1, self.updateTimer, args=[player, spellNum, champId])
            enemyInfo[player]['timerThread'][int(spellNum) - 1].start()
        else: #타이머 종료
            btn = getattr(self, 'buttonSpell' + str(spellNum))[player]
            btn.setStyleSheet("QPushButton {{border-image: url(spell/{0});}}".format(enemyInfo[player]['spell' + spellNum]))
            btn.setText('')
            self.refreshSpellText()

    def refreshSpellText(self):
        global spellText
        spellText = ''
        for enemy in enemyInfo:
            flag = False
            temp = enemy['champ']+' '
            for i in ('1', '2'):
                if enemy['spell'+i+'CT'] > 0:
                    # 스펠 시간을 초단위로 나타냄
                    second = ingameTime[0] + enemy['spell'+i+'CT'] + (time.time() - ingameTime[1])
                    temp += "{0}{1}:{2:02d} ".format(enemy['spell'+i], int(second//60), int(second%60))
                    flag = True
            if flag is True: #스펠 쿨타임이 붙음
                spellText += temp

    def pasteSpellText(self):
        keyboard.write(spellText)

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
