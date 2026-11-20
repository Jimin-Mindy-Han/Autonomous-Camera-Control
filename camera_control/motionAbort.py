import requests as rq
import json
import time

LinkID1 = "205C32454D31"
LinkID2=  "205F385B5631"
httpURL = 'http://127.0.0.1:32222/v1'

#___________________________________________________________________________
def motionAbort(LinkID):
    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "motionAbort"
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)

# ___________________________________________________________________________
def focusManualMove(LinkID):
    url = "%s/bundle/%s" % (httpURL, LinkID)
    payload = {
        "command": "focusManualMove",
        "deltaEnc": 1
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)

#___________________________________________________________________________
def calibration(LinkID):
    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "calibrate",
        "device": "focusPlusPro"
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)

if __name__ == "__main__":

    motionAbort(LinkID2)

    #focusManualMove(LinkID)

    #calibration(LinkID)