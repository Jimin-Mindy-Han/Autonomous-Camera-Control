import requests as rq
import json
import time

#url = 'http://127.0.0.1:32222/v1/bundle/205C32454D31'
httpURL = 'http://127.0.0.1:32222/v1'
LinkID1 = "205C32454D31" 
LinkID2=  "205F385B5631" 
dollymac = "84:CC:A8:62:8D:DA" #dollyPlus mac address
head1mac = "84:CC:A8:62:54:32" #headPlusPro mac address
slidemac = "8C:4B:14:04:9D:2A" #slider mac address
head2mac = "C4:DE:E2:EB:A9:4E" #headPlus v2 mac address
focusmac = "C4:DE:E2:EB:D4:26" #focus/zoom Module mac adress
index1 = 0
index2 = 1
index3 = 2
#___________________________________________________________________________
def pairingScanStart(LinkID):

    url = "%s/link/%s" %(httpURL, LinkID)
    
    payload = {
        "command": "wirelessPairingScanStart"
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text) #json.loads가 response.text파일을 딕셔너리로 바꿔주는 거였다!
    print(response.text)
    print(response.status_code)
'''
    if (response_dict["result"] == "ok") :
        print("스캔 정상")
        time.sleep(7)
        PairingScanResults(LinkID)
'''
#___________________________________________________________________________
def pairingScanResults(LinkID):

    url = "%s/link/%s" %(httpURL, LinkID)
    
    payload = {
        "command": "wirelessPairingScanResults"
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    print(response.text)
    print(response.status_code)
'''
    if (response_dict["result"] == "ok") :
        time.sleep(5)
        PairingCreateBundle(LinkID)
'''
#___________________________________________________________________________
def pairingCreateBundle1(LinkID, macAdress): #only 1

    url = "%s/link/%s" %(httpURL, LinkID)

    payload = {
        "command": "wirelessPairingCreateBundle",
        "deviceCount": 1,
        "forcedMasterDevice": "none",
        "macList": [
                macAdress
        ]
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def pairingCreateBundle(LinkID): #pair two

    url = "%s/link/%s" %(httpURL, LinkID)

    payload = {
        "command": "wirelessPairingCreateBundle",
        "deviceCount": 2,
        "forcedMasterDevice": "none",
        "macList": [
            head1mac,
            dollymac
        ]
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def attachToBundle(LinkID):

    url = "%s/link/%s" %(httpURL, LinkID)

    payload = {
        "command": "wirelessPairingAttachToBundle",
        #"mac": "84:CC:A8:62:8D:DA", #dollyPlus
        "mac": "84:CC:A8:62:54:32" #headPlusPro mac
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def pairingStatus(LinkID):
    url = "%s/link/%s" %(httpURL, LinkID)
    payload = {
        "command": "wirelessPairingStatus"
    }
    headers = {'Content-Type': 'application/json'}    
    response = rq.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def wired(LinkID):
    url = "%s/link/%s" %(httpURL, LinkID)
    
    payload = {
        "command": "link2PairingScanResults"
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def connectToWiredDevice(LinkID):
    url = "%s/link/%s" %(httpURL, LinkID)
    
    payload = {
        "command": "link2PairingConnect",
        "forcedMasterDevice": "none"
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def getWiredPairingStatus(LinkID):
    url = "%s/link/%s" %(httpURL, LinkID)
    payload = {
        "command": "link2PairingStatus"
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def disconnect(LinkID): #unpair

    url = "%s/link/%s" %(httpURL, LinkID)

    payload = {
        "command": "disconnect"
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("GET", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def detectLinkAdapter(LinkID):
    url = "%s/link/%s/detect" %(httpURL, LinkID)

    headers = {'Content-Type': 'application/json'}
    response = rq.request("GET", url, headers=headers)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def linkAdapterStatus():
    url = "%s/device" %(httpURL)
    payload = {
        "command": "linkStatus"
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
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
#___________________________________________________________________________
def periodicStatus(LinkID):
    url = "%s/bundle/%s/status" %(httpURL, LinkID)
    payload = {
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("GET", url, headers=headers, json=payload)
    response_dict = json.loads(response.text) #dict 형으로 바꿔주기
    return response_dict
    #print(response.status_code)
#___________________________________________________________________________

if __name__ == "__main__":

    print("_______________ PAIRING START _______________")

    # disconnect(LinkID1)
    # time.sleep(5)
    # pairingScanStart(LinkID1)
    # time.sleep(5)
    # pairingScanResults(LinkID1)
    # time.sleep(5)
    # wired(LinkID1)
    # time.sleep(5)
    # connectToWiredDevice(LinkID1)
    # time.sleep(5)
    # getWiredPairingStatus(LinkID1)

    disconnect(LinkID2)
    time.sleep(5)
    pairingScanStart(LinkID2)
    time.sleep(5)
    pairingScanResults(LinkID2)
    time.sleep(5)
    pairingCreateBundle(LinkID2)
    time.sleep(5)
    attachToBundle(LinkID2)
    time.sleep(5)
    pairingStatus(LinkID2)
    time.sleep(5)
    print(periodicStatus(LinkID2))
    
    print("________________ PAIRING END ________________")

