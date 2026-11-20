import move
import pair
import time

LinkID1 = "205C32454D31"
LinkID2 = "205F385B5631"
#ang_ini = 0
index1 = 0
index2 = 1
index3 = 2
index4 = 3
index5 = 4
index6 = 5

if __name__ == "__main__":

    #time.sleep(10)

    #ang_ini = float(move.moduleInfo(LinkID1, index2, "focus"))
    #print(ang_ini)
    
    #time.sleep(3)
    #move.calibration(LinkID2, "focus")
    #time.sleep(15)
    move.calibration(LinkID1, "slide")
    #time.sleep(7)
    #move.calibration(LinkID2, "headPlus2")
    #ang_fin = float(pair.periodicStatus(LinkID1)["data"]["readings"]["focus"])
    #print(ang_fin)

    #ang_dif = ang_fin - ang_ini #92574.0
    #print(ang_dif)