import requests as rq
import keyboard  # pip install keyboard
import pygame
import requests
import json
import time

httpURL = "http://127.0.0.1:32222/v1"
LinkID = "205C32454D31"

# Focus 제어 함수
def focusManualMove(LinkID, focus_delta):
    url = "%s/bundle/%s" % (httpURL, LinkID)
    payload = {
        "command": "focusManualMove",
        "deltaEnc": focus_delta
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = rq.post(url, headers=headers, json=payload, timeout=0.5)
        print(f"[focus {focus_delta:+}] Status:", response.status_code)
    except Exception as e:
        print("Error sending command:", e)

# ---------------------------------------------------------------------------
def bundleStatus(linkID):
    # ...
    url = "%s/bundle/%s/status" % (httpURL, linkID)
    headers = {"Content-Type": "application/json"}

    # ...
    response = requests.request(
        "GET", url, headers=headers, timeout=5.0
    )
    response_json = json.loads(response.text)
    return response_json

# ---------------------------------------------------------------------------
def main_joystick():
    # Pygame 초기화
    pygame.init()
    screen = pygame.display.set_mode([300, 100])
    pygame.display.set_caption("Focus Control")

    font = pygame.font.SysFont(None, 24)
    # 실시간 키 입력 처리 루프
    print("Press 't' to increase focus, 'y' to decrease focus, 'esc' to exit.")

    focusMove = 0
    joystickWasRunning = False
    isRunning = True

    while isRunning:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            # 키를 눌렀을 때
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    focusMove = 340
                elif event.key == pygame.K_y:
                    focusMove = -340
                elif event.key == pygame.K_ESCAPE:
                    isRunning = False
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_t, pygame.K_y):
                    focusMove = 0

        if focusMove != 0:
            focusManualMove(LinkID, focusMove)
            joystickWasRunning = True
        elif joystickWasRunning:
            joystickWasRunning = False
            focusManualMove(LinkID, 0)

        # Clear the screen
        screen.fill((180, 180, 180))
        img = font.render('t, y ---> Focus Axis Control', True, 0)
        screen.blit(img, (20, 20))

        status = bundleStatus(LinkID)
        focusReading = float(status["data"]["readings"]["focus"])
        img = font.render(f"focus reading: {focusReading:.2f} degrees", True, 0)
        screen.blit(img, (20, 88))

        pygame.display.flip()
        time.sleep(0.025) # 이걸로 focus encoder 속도 조절 가능
    
    # 종료 처리
    pygame.quit()
    print("Script exits.")

# 단독 실행 시만 동작
if __name__ == "__main__":
    main_joystick()