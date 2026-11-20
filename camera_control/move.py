import requests as rq
import json
import time
import pair
from focusMove import bundleStatus

#url = 'http://127.0.0.1:32222/v1/bundle/205C32454D31'
httpURL = 'http://127.0.0.1:32222/v1'
LinkID1 = "205C32454D31"
LinkID2 = "205F385B5631"
index1 = 0
index2 = 1
index3 = 2
index4 = 3
index5 = 4
index6 = 5

#___________________________________________________________________________
def pairingStatus(LinkID): 
    #checking adapter pairing status
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
def realTimeMoveFixedDuration(LinkID): #Dolly는 지원하지 않음
    
    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command":"realTimeMoveFixedDuration",
        #"slide": 1.0
        #"headPan": 90.0,
        #"headTilt": 0.0
        "focus": -44500,
        "duration": 60.0
    }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeStoreCurrentPose(LinkID, index):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeStoreCurrentPose",
        "index": index
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
# def keyposeStoreWithNumericData(LinkID, index, headPan, headTilt, slide, focus):
#
#     url = "%s/bundle/%s" %(httpURL, LinkID)
#
#     payload = {
#         "command": "keyposeStoreWithNumericData",
#         "index": index,
#         "headPan": headPan,
#         "headTilt": headTilt,
#         "slide": slide,
#         "focus": focus
#     }
#     headers = {'Content-Type': 'application/json'}
#     response = rq.request("POST", url, headers=headers, json=payload)
#     print(response.text)
#     print(response.status_code)
#___________________________________________________________________________
def keyposeStoreWithNumericData(LinkID, index, headPan, headTilt, slide):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeStoreWithNumericData",
        "index": index,
        "headPan": headPan,
        "headTilt": headTilt,
        "slide": slide,
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeStoreWithNumericDataSlide(LinkID, index, slide):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeStoreWithNumericData",
        "index": index,
        "slide": slide
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    #print(response.status_code)
    #___________________________________________________________________________
def keyposeStoreWithNumericDataHead(LinkID, index, headPan, headTilt):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeStoreWithNumericData",
        "index": index,
        "headPan": headPan, #HeadPan(좌우 움직임): -90 이 기본
        "headTilt": headTilt #headTilt(위아래 움직임): 0 이 기본
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeStoreWithNumericDataFocus(LinkID, index, focus):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeStoreWithNumericData",
        "index": index,
        "focus": focus
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeLoopFixedSpeed(LinkID, index1, index2):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeLoopFixedSpeed",
        "index1": index1,
        "index2": index2,
        "acceleration": 0.5,
        "speed": 0.5
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeLoopFixedDuration(LinkID, index1, index2, duration):

    url = "%s/bundle/%s" %(httpURL, LinkID)

    payload = {
        "command": "keyposeLoopFixedSpeed",
        "index1": index1,
        "index2": index2,
        "duration": duration,
        "acceleration": 0.5
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeMoveFixedSpeed(LinkID, index):

    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "keyposeMoveFixedSpeed",
        "index": index,
        "acceleration": 0.5,
        "speed": 0.5
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeMoveFixedDuration(LinkID, index, duration):

    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command":"keyposeMoveFixedDuration",
        "index": index,
        "duration": duration,
        "acceleration": 1
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def keyposeReadNumericValues(LinkID, index):
    
    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "keyposeReadNumericValues",
        "index": index
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    #print(response.text)
    #print(response.status_code)
    return response.text
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
def deleteKeypose(LinkID,index):
    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "keyposeDeletePose",
        "index": index
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def moduleInfo(LinkID, index, module):

    info = keyposeReadNumericValues(LinkID, index)
    #print(info)
    #print(type(eval(info)))
    info = eval(info)

    if module == "focus":
        return info["data"]["focus"]
    elif module == "headTilt":
        return info["data"]["headTilt"]
    elif module == "headPan":
        return info["data"]["headPan"]
    elif module == "slide":
        return info["data"]["slide"]
#___________________________________________________________________________
def realTimeMove(LinkID): #wired setup 되어있는지 확인!!!
    url = "%s/bundle/%s" %(httpURL, LinkID)
    headers = {"Content-Type": "application/json"}
    payload = {
        "command":"realTimeMoveFixedDuration",
        "duration": 0.033, #fps 세팅: 1초/30frame = 0.033 [s/frame]
        # "headPan": 90.0, #위의 duration 동안 이동 가능한 각도의 위치
        # "headTilt": 10.0, #위의 duration 동안 이동 가능한 각도의 위치
        # "slide": 10.0,
        "focus": 200
    }
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def durationInfo(LinkID):
    info = pair.periodicStatus(LinkID)
    return info["data"]["plannedMotionDuration"]    
#___________________________________________________________________________
def calibration(LinkID, module):
    url = "%s/bundle/%s" %(httpURL, LinkID)
    
    if module == "focus":
        payload = {
        "command": "calibrate",
        "device": "focusPlusPro"
        }
    elif module == "slide":
        payload = {
        "command": "calibrate",
        "device": "slideModuleV3",
        "isOnGround": False,
        "isOnLeftSide" : True
        }
    elif module == "headPlus2":
        payload = {
        "command": "calibrate",
        "device": "headPlusV2"
        }

    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)
#___________________________________________________________________________
def focusManualMove(LinkID, focus): #뭐하는 함수인지 전혀 모르겠음
    url = "%s/bundle/%s" %(httpURL, LinkID)
    payload = {
        "command": "focusManualMove",
        "deltaEnc": focus
    }
    headers = {'Content-Type': 'application/json'}
    response = rq.request("POST", url, headers=headers, json=payload)
    print(response.text)
    print(response.status_code)

#___________________________________________________________________________    

if __name__ == "__main__":

    LinkID1 = "205C32454D31"
    LinkID2 = "205F385B5631"

    focusManualMove(LinkID1)
    # realTimeMove(LinkID1)

    status = bundleStatus(LinkID1)
    focusStart = float(status["data"]["readings"]["focus"])
    print(focusStart)

    # calibration(LinkID1, "headPlus2")
    #keyposeStoreCurrentPose(LinkID1, index1)
    # time.sleep(5)
    #slide = moduleInfo(LinkID1, index1, "slide")
    #print(slide)
    #keyposeStoreWithNumericDataSlide(LinkID1, index2, 100)
    # time.sleep(2)
    # keyposeMoveFixedDuration(LinkID1, index1, 15)

    #focus1 = float(pair.periodicStatus(LinkID)["data"]["readings"]["focus"]) #현재 초점 위치는 이걸로 불러올 수 없음 Info 사용할 것
    #slide1 = float(pair.periodicStatus(LinkID)["data"]["readings"]["slide"])
    #headPan1 = float(pair.periodicStatus(LinkID)["data"]["readings"]["headPan"])
    #headTilt1 = float(pair.periodicStatus(LinkID)["data"]["readings"]["headTilt"])

    

    #deleteKeypose(LinkID1, index1)
    # keyposeStoreCurrentPose(LinkID1, index1)
    # keyposeStoreWithNumericDataSlide(LinkID1, index2, 10)
    # keyposeMoveFixedDuration(LinkID1, index2, 10)
    # keyposeMoveFixedDuration(LinkID1, index1, 5)
    # focus = moduleInfo(LinkID2, index3, "focus")
    # headPan = moduleInfo(LinkID2, index3, "headPan")
    # headTilt = moduleInfo(LinkID2, index3, "headTilt")
    # slide = moduleInfo(LinkID2, index3, "slide")
    # print(focus)
    # print(headTilt)
    # print(headPan)
    # print(slide)
    #focus1 = moduleInfo(LinkID1, index1, "focus")
    #print(moduleInfo(LinkID1, index1, "focus"))

    #focus3 = focus2 - 61934.8

    #keyposeStoreWithNumericDataFocus(LinkID1, index3, focus3)
    #print(moduleInfo(LinkID1, index3, "focus"))

    #keyposeLoopFixedSpeed(LinkID1, index1, index3)
    
    #keyposeStoreWithNumericDataFocus(LinkID, index2, -102746.0-22000.0)
    #keyposeStoreWithNumericData(LinkID, index1, headPan1, headTilt1, slide1, -49711.0)
    #keyposeStoreWithNumericData(LinkID, index2, headPan1, headTilt1, slide1, 15000.0)

    #keyposeMoveFixedSpeed(LinkID1, index1)
    #time.sleep(3)
    #keyposeMoveFixedSpeed(LinkID1, index2)
    #time.sleep(3)
    #keyposeMoveFixedSpeed(LinkID1, index3)
