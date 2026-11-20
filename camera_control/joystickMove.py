# -----------------------------------------------------------------------------
#
#
# -----------------------------------------------------------------------------
import requests
import json
import time
import pygame

# Local SDK endpoint URL
httpURL = "http://127.0.0.1:32222/v1"


# ---------------------------------------------------------------------------
def joystickMoveHeadPLUS(linkID, pan, tilt):
    # ...
    url = "%s/bundle/%s" % (httpURL, linkID)
    headers = {"Content-Type": "application/json"}
    payload = {
        "command": "joystickMove",
        "headPan": pan,
        "headTilt": tilt
    }

    # ...
    response = requests.request("POST", url, headers=headers, json=payload)
    response_json = json.loads(response.text)


# ---------------------------------------------------------------------------
def joystickMoveSlide(linkID, slide):
    # ...
    url = "%s/bundle/%s" % (httpURL, linkID)
    headers = {"Content-Type": "application/json"}
    payload = {
        "command": "joystickMove",
        "slide": slide
    }

    # ...
    response = requests.request("POST", url, headers=headers, json=payload)
    response_json = json.loads(response.text)


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
# def run_joystick_loop(linkID, ):
#     # pygame 초기화
#     pygame.init()
#     screen = pygame.display.set_mode([400, 160])
#     pygame.display.set_caption("edelkrone SDK - Joystick Example")
#
#     font = pygame.font.SysFont(None, 24)
#
#     # Default values
#     panDirection = 0.0
#     tiltDirection = 0.0
#     slideDirection = 0.0
#     joystickWasRunning = False
#
#     isRunning = True
#     while isRunning:
#         # Handle events
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 isRunning = False
#             elif event.type == pygame.KEYDOWN:
#                 if ((event.key == pygame.K_q) and (panDirection == 0.0)):
#                     panDirection = -1.0
#                 elif ((event.key == pygame.K_e) and (panDirection == 0.0)):
#                     panDirection = 1.0
#                 elif ((event.key == pygame.K_w) and (panDirection == 0.0)):
#                     tiltDirection = 1.0
#                 elif ((event.key == pygame.K_s) and (panDirection == 0.0)):
#                     tiltDirection = -1.0
#                 elif ((event.key == pygame.K_a) and (slideDirection == 0.0)):
#                     slideDirection = 1.0
#                 elif ((event.key == pygame.K_d) and (slideDirection == 0.0)):
#                     slideDirection = -1.0
#
#             elif event.type == pygame.KEYUP:
#                 if ((event.key == pygame.K_q) or (event.key == pygame.K_e)):
#                     panDirection = 0.0
#                 elif ((event.key == pygame.K_w) or (event.key == pygame.K_s)):
#                     tiltDirection = 0.0
#                 elif event.key in [pygame.K_a, pygame.K_d]:
#                     slideDirection = 0.0
#
#         # If at least one of the axis active send joystickMove command ...
#         if ((panDirection != 0.0) or (tiltDirection != 0.0)) or (slideDirection != 0.0):
#             # Absolute values of Joystick speeds are fixed for this
#             # example for simplicity sake.
#             panSpeed = 0.75 * panDirection
#             tiltSpeed = 0.75 * tiltDirection
#             slideSpeed = 0.75 * slideDirection
#             joystickMoveHeadPLUS(linkID, panSpeed, tiltSpeed)
#             joystickMoveSlide(linkID, slideSpeed)
#             joystickWasRunning = True
#
#         # Send one last *stop* command after both axes are set to zero.
#         if ((panDirection == 0.0) and (tiltDirection == 0.0)
#                 and (slideDirection == 0.0) and joystickWasRunning):
#             joystickWasRunning = False
#             joystickMoveHeadPLUS(linkID, 0.0, 0.0)
#             joystickMoveSlide(linkID, 0.0)
#
#         # Clear the screen
#         screen.fill((180, 180, 180))
#
#         # 안내 텍스트
#         img = font.render('w, s ---> Tilt Axis Control', True, 0)
#         screen.blit(img, (20, 20))
#
#         img = font.render('q, e ---> Pan Axis Control', True, 0)
#         screen.blit(img, (20, 44))
#
#         img = font.render('a, d ---> Slide Axis Control', True, 0)
#         screen.blit(img, (20, 68))
#
#         # 상태 읽기
#         status2 = bundleStatus(linkID)
#
#         panReading = float(status2["data"]["readings"]["headPan"])
#         panReading_str = "Pan reading: %7.2f degrees" % (panReading)
#         img = font.render(panReading_str, True, 0)
#         screen.blit(img, (20, 88))
#
#         tiltReading = float(status2["data"]["readings"]["headTilt"])
#         tiltReading_str = "Tilt Reading: %7.2f degrees" % (tiltReading)
#         img = font.render(tiltReading_str, True, 0)
#         screen.blit(img, (20, 112))
#
#         slideReading = float(status2["data"]["readings"]["slide"])
#         slideReading_str = "Slide: %7.2f cm" % (slideReading)
#         img = font.render(slideReading_str, True, 0)
#         screen.blit(img, (20, 136))
#
#         # Update the screen
#         pygame.display.flip()
#         time.sleep(0.025)
#
#     pygame.quit()
#     print("Script exits.")
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    # ASSUMPTIONS
    # ===========
    # - HeadPLUS series product is paired via edelkrone Web APP.
    # - linkID for the particular link Adapter copied and pasted to this
    # script after pairing is done.

    # ...
    # linkID1 = "205C32454D31"
    linkID2 = "205F385B5631"

    # We are using the pygame library to create minimal amount of user
    # interaction layer.
    pygame.init()
    screen = pygame.display.set_mode([400, 160])
    pygame.display.set_caption("edelkrone SDK - Joystick Example")

    # ...
    font = pygame.font.SysFont(None, 24)

    # Default values
    panDirection = 0.0
    tiltDirection = 0.0
    slideDirection = 0.0
    joystickWasRunning = False

    # ...
    isRunning = True
    slideSpeed = 0.0
    while isRunning:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            elif event.type == pygame.KEYDOWN:
                if ((event.key == pygame.K_q) and (panDirection == 0.0)):
                    panDirection = -1.0
                elif ((event.key == pygame.K_e) and (panDirection == 0.0)):
                    panDirection = 1.0
                elif ((event.key == pygame.K_w) and (panDirection == 0.0)):
                    tiltDirection = 1.0
                elif ((event.key == pygame.K_s) and (panDirection == 0.0)):
                    tiltDirection = -1.0
                elif ((event.key == pygame.K_a) and (slideDirection == 0.0)):
                    slideDirection = 1.0
                elif ((event.key == pygame.K_d) and (slideDirection == 0.0)):
                    slideDirection = -1.0

            elif event.type == pygame.KEYUP:
                if ((event.key == pygame.K_q) or (event.key == pygame.K_e)):
                    panDirection = 0.0
                elif ((event.key == pygame.K_w) or (event.key == pygame.K_s)):
                    tiltDirection = 0.0
                elif event.key in [pygame.K_a, pygame.K_d]:
                    slideDirection = 0.0

        # If at least one of the axis active send joystickMove
        # command ...
        if ((panDirection != 0.0) or (tiltDirection != 0.0)) or (slideDirection != 0.0):
            # Absolute values of Joystick speeds are fixed for this
            # example for simplicity sake.
            panSpeed = 0.75 * panDirection
            tiltSpeed = 0.75 * tiltDirection
            targetSpeed = 0.1 * slideDirection
            slideSpeed += 0.1 * (targetSpeed - slideSpeed)
            joystickMoveHeadPLUS(linkID2, panSpeed, tiltSpeed)
            joystickMoveSlide(linkID2, slideSpeed)
            print('slide speed: ', slideSpeed)
            joystickWasRunning = True

        # Send one last *stop* command after both axes are set to zero.
        if ((panDirection == 0.0) and (tiltDirection == 0.0) and (slideDirection == 0.0) and (joystickWasRunning == True)):
            joystickWasRunning = False
            joystickMoveHeadPLUS(linkID2, 0.0, 0.0)
            joystickMoveSlide(linkID2, 0.0)

        # Clear the screen
        screen.fill((180, 180, 180))

        # ...
        img = font.render('w, s ---> Tilt Axis Control', True, 0)
        screen.blit(img, (20, 20))

        # ...
        img = font.render('q, e ---> Pan Axis Control', True, 0)
        screen.blit(img, (20, 44))

        # ...
        img = font.render('a, d ---> Slide Axis Control', True, 0)
        screen.blit(img, (20, 68))

        # ...
        # status1 = bundleStatus(linkID1)
        status2 = bundleStatus(linkID2)
        # print(status)

        ...
        panReading = float(status2["data"]["readings"]["headPan"])
        panReading_str = "Pan reading: %7.2f degrees" % (panReading)
        img = font.render(panReading_str, True, 0)
        screen.blit(img, (20, 88))

        # ...
        tiltReading = float(status2["data"]["readings"]["headTilt"])
        tiltReading_str = "Tilt Reading: %7.2f degrees" % (tiltReading)
        img = font.render(tiltReading_str, True, 0)
        screen.blit(img, (20, 112))

        slideReading = float(status2["data"]["readings"]["slide"])
        slideReading_str = f"Slide: %7.2f cm" %(slideReading)
        img = font.render(slideReading_str, True, 0)
        screen.blit(img, (20, 136))

        # Update the screen
        pygame.display.flip()
        time.sleep(0.025)

    # ...
    pygame.quit()
    print("Script exits.")