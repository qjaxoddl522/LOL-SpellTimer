import threading

def print_message():
    print("Hello, World!")

# 5초 후에 print_message 함수를 실행하는 타이머를 생성합니다.
timer = threading.Timer(5, print_message)

# 타이머를 시작합니다.
timer.start()

# 필요한 경우 타이머를 중지할 수 있습니다.
# timer.cancel()
