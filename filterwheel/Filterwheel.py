from __future__ import print_function
from __future__ import absolute_import

import serial
import time

# bits to setup the encoder
SETUP_P34=bytearray([2, '1', 0x59, 0x50, 0x33, 0x34, 0x53, 0x32, 0x3A, 0x58, 0x58, 0x03, 13, 10])
SETUP_P35=bytearray([2, 0x31, 0x59, 0x50, 0x33, 0x35, 0x53, 0x31, 0x31, 0x3A, 0x58, 0x58, 0x03, 13, 10])
# command to readposition
READPOSITION=bytearray([2, 0x31, 0x59, 0x50, 0x32, 0x32, 0x52, 0x3A, 0x58, 0x58, 0x03, 13, 10])

# Filter positions
CLOSED = 592
OPEN = 796
FILTER325 = 1001
FILTER350 = 1205
FILTER375 = 1407
FILTER400 = 1612
FILTER425 = 1816
FILTER450 = 2022
FILTER475 = 179
FILTER500 = 386

# order of filters
FILTERS = [FILTER450, FILTER475, FILTER500, CLOSED, OPEN, FILTER325, FILTER350, FILTER375, FILTER400, FILTER425]

# steps at warm temperatures
NEXT = "0745"
ADJUST = "0010"
STEP = "0005"

# steps at cold temperatures
NEXT_cold= "1045"
ADJUST_cold="0015"
STEP_cold="0007"

ERRCNT = 5


def waitForArduino(Arduino):
    # wait for Arduino response after boot up
    msg=""
    print("Waiting for Arduino...")
    while msg.find("Arduino is ready") == -1:
        while Arduino.inWaiting() == 0:
            pass

        msg = str(Arduino.readline())
        print("Wait for Arduino:%s"%msg)

def driveMotor(Arduino, x):
    #print("Drive step: %s"%x)
    cmmd=x+"\n"
    Arduino.write(cmmd)
    return Arduino.readline()


def setupEncoder(Encoder):
    print("Setting up Encoder...")
    Encoder.write(SETUP_P34)
    Encoder.readline()
    print("Initialising Encoder...")
    Encoder.write(SETUP_P35)
    Encoder.readline()
    print("Encoder is ready!")

def readPosition(Encoder):
    Encoder.write(READPOSITION)
    pos=Encoder.readline()
    #print("Read Position: %s"%str(pos))
    pos=pos[2:-6]
    print("Read Position: %s"%str(pos))
    return pos

def getSign(x):
    if x<0:
        return "-"
    else:
        return "+"

def adjustPosition(Arduino, Encoder, pos, adj, stp):
    adjPos=pos
    foundPos=False

    while foundPos==False:
        cmmdstr=""
        diff=[]
        sign=[]

        #print("Wrong position, searching closest filter...")
        # find the filter which is closest
        for i in range(len(FILTERS)):
            diff.append(abs(FILTERS[i]-int(adjPos)))
            sign.append(getSign(FILTERS[i]-int(adjPos)))
        if diff[1] > 1000:
            diff[1]=abs(diff[0]-2048)
            sign[1]="+"

        
        filtndx=diff.index(min(diff))
        #print("Closest filter is %d (index %d)"%(FILTERS[filtndx],filtndx))

        # adjust direction
        cmmdstr+=sign[filtndx]

        # step size normal or small if very close
        if diff[filtndx]<4:
            cmmdstr+=stp
        else:
            cmmdstr+=adj
        #print(filtndx)
        #print(diff[filtndx])
        #print(cmmdstr)

        # execute
        driveMotor(Arduino, cmmdstr)
        adjPos=int(readPosition(Encoder))
        #print("Adjust position from:",adjPos, " with step:",cmmdstr)

        if adjPos==FILTERS[filtndx]:
            foundPos=True
            #print("Found position")
            return adjPos
        elif adjPos==2047:
            ERRCNT-=1
            if ERRCNT == 0:
                raise RuntimeError
        else:
            #print("Position not found")
            time.sleep(1)

def connect_to_arduino():
    arduino=serial.Serial('/dev/ttyUSB1', 9600, timeout=10)
    print ("Initiated Arduino")
    waitForArduino(arduino)
    print ("Arduino ready!")
    return arduino

def connect_to_encoder():
    encoder=serial.Serial('/dev/ttyUSB0', 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
    print ("Initiated Encoder.")
    setupEncoder(encoder)
    print ("Encoder ready!")
    return encoder

def close_connection(dev):
    dev.close()
    print("Connection closed!")

def filterwheel(arduino, encoder):
    Data = []
    t=time.strftime("%Y_%m_%d_%H_%M_%S")
    Data.append(t)
    pos_old=readPosition(encoder)
    Data.append(pos_old)
    print("Old Position",pos_old)


    for n in range(30):

        if 1:
            nextfilter=NEXT
            adjustfilter=ADJUST
            stepfilter=STEP
        else:
            nextfilter=NEXT_cold
            adjustfilter=ADJUST_cold
            stepfilter=STEP_cold

        Data.append(time.strftime("%Y_%m_%d_%H_%M_%S"))
        done=driveMotor(arduino, "+"+nextfilter)
        done=done.strip('\n')
        Data.append(done)
        pos_new=readPosition(encoder)
        Data.append(pos_new)
        adaPos=adjustPosition(arduino, encoder, pos_new, adj=adjustfilter, stp=stepfilter)
        Data.append(adaPos)
        Data.append(time.strftime("%Y_%m_%d_%H_%M_%S"))

        with open("motorlog_"+t+".txt", 'a') as f:
            for item in Data:
                f.write("%s\n" % item)
        Data=[]
        time.sleep(10)



if __name__=="__main__":
    while(True):
        try:
            Arduino = connect_to_arduino()
            Encoder = connect_to_encoder()
            #time.sleep(3600)
            #time.sleep(20)
            filterwheel(Arduino, Encoder)
            break
        except serial.SerialException as e:
            print ("ERROR:", e )
            close_connection(Arduino)
            close_connection(Encoder)
            continue
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            close_connection(Arduino)
            close_connection(Encoder)
            break
