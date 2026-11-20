import os
from dotenv import load_dotenv

load_dotenv()
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
def joystickMove(linkID, slide):
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
if __name__ == "__main__":

    # ASSUMPTIONS
    # ===========
    # - HeadPLUS series product is paired via edelkrone Web APP.
    # - linkID for the particular link Adapter copied and pasted to this
    # script after pairing is done.

    # ...
    linkID = os.environ["EDELKRONE_LINK_ID"]

    # We are using the pygame library to create minimal amount of user
    # interaction layer.
    pygame.init()
    screen = pygame.display.set_mode([400, 160])
    pygame.display.set_caption("edelkrone SDK - Joystick Example")

    # ...
    font = pygame.font.SysFont(None, 24)

    # Default values
    slideDirection = 0.0
    joystickWasRunning = False

    # ...
    isRunning = True
    while isRunning:

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False
            elif event.type == pygame.KEYDOWN:
                if ((event.key == pygame.K_a) and (slideDirection == 0.0)):
                    slideDirection = 1.0
                elif ((event.key == pygame.K_d) and (slideDirection == 0.0)):
                    slideDirection = -1.0

            elif event.type == pygame.KEYUP:
                if ((event.key == pygame.K_a) or (event.key == pygame.K_d)):
                    slideDirection = 0.0


        # If at least one of the axis active send joystickMove
        # command ...
        if (slideDirection != 0.0):
            # Absolute values of Joystick speeds are fixed for this
            # example for simplicity sake.
            slideSpeed = 0.75 * slideDirection
            joystickMove(linkID, slideSpeed)
            joystickWasRunning = True

        # Send one last *stop* command after both axes are set to zero.
        if ((slideDirection == 0.0) and (joystickWasRunning == True)):
            joystickWasRunning = False
            joystickMove(linkID, 0.0)

        # Clear the screen
        screen.fill((180, 180, 180))

        # ...
        img = font.render('a, d ---> Slide Axis Control', True, 0)
        screen.blit(img, (20, 44))

        # ...
        status = bundleStatus(linkID)
        print(status)

        ...
        slideReading = float(status["data"]["readings"]["slide"])
        slideReading_str = "Pan reading: %7.2f degrees" % (slideReading)
        img = font.render(slideReading_str, True, 0)
        screen.blit(img, (20, 78))


        # Update the screen
        pygame.display.flip()
        time.sleep(0.025)

    # ...
    pygame.quit()
    print("Script exits.")