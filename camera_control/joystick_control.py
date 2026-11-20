# joystick_control.py
import requests
import json

def joystickMoveHeadPLUS(linkID, panSpeed, tiltSpeed):
    url = f"http://127.0.0.1:32222/v1/bundle/{linkID}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "command": "joystickMove",
        "headPan": panSpeed,
        "headTilt": tiltSpeed
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=0.1)
    except Exception as e:
        print(f"[joystick_move] 전송 실패: {e}")

def joystickMoveSlide(linkID, slideSpeed):
    url = f"http://127.0.0.1:32222/v1/bundle/{linkID}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "command": "joystickMove",
        "slide": slideSpeed
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=0.1)
    except Exception as e:
        print(f"[joystickMoveSlide] 전송 실패: {e}")

def joystickMove(linkID, panSpeed, tiltSpeed, slideSpeed):
    url = f"http://127.0.0.1:32222/v1/bundle/{linkID}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "command": "joystickMove",
        "headPan": panSpeed,
        "headTilt": tiltSpeed,
        "slide": slideSpeed
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=0.1)
    except Exception as e:
        print(f"[joystick_move] 전송 실패: {e}")