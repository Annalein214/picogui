###################################################################################################
''' Readme
This script lets an arduino drive a motor while it uses an encoder for precise positioning.

Make sure you adjust for the correct temperature (configure option "cold")

Make sure you know in which path you can find which serial device (Arduino & Encoder).
Plug them in one after each other and in between execute in terminal:
$ ls -al /dev/ttyUSB*
Fill the correct paths into the configuration section below


'''


###################################################################################################

from __future__ import print_function
from __future__ import absolute_import

import serial, time, sys, traceback, os
sys.path.append("../code/")
from log import log

###################################################################################################
# configuration
arduino_path="/dev/ttyUSB1"
encoder_path="/dev/ttyUSB0"

log_dir=os.getcwd() # current directory

log_level="debug" # debug, info

test_with_short_times=True 

cold=False


###################################################################################################
# Definitions

# bits to setup the encoder
SETUP_P34=bytearray([2, 1, 0x59, 0x50, 0x33, 0x34, 0x53, 0x32, 0x3A, 0x58, 0x58, 0x03, 13, 10])
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
if cold:
    # steps at cold temperatures
    NEXT= "1045"
    ADJUST="0015"
    STEP="0007"

ERRCNT = 5

if test_with_short_times:
    DELAY=10
else:
    DELAY=3600
###################################################################################################
# arduino

class Arduino:

    def __init__(self,path, encoder, log):
        self.path=path
        self.log=log
        self.encoder=encoder

    def connect(self,):
        self.arduino=serial.Serial(self.path, 9600, timeout=10)
        self.log.debug("Initiated Arduino")
        waitForArduino(self.arduino)
        self.log.info("Arduino ready!")

    def close_connection(self):
        self.arduino.close()
        self.log.info("Connection to Arduino closed!")

    def waitForArduino(self):
        # wait for Arduino response after boot up
        msg=""
        self.log.debug("Waiting for Arduino...")
        while msg.find("Arduino is ready") == -1:
            while self.arduino.inWaiting() == 0:
                pass
            msg = str(self.arduino.readline())
            self.log.debug("Wait for Arduino: %s"%msg)


    def driveMotor(self, x):
        #print("Drive step: %s"%x)
        cmmd=x+"\n"
        self.arduino.write(cmmd)
        return self.arduino.readline()

    def run(self):

        # make log entry
        log_string=""
        pos_old=readPosition(encoder)
        log_string+=str(pos_old)+"; "
        self.log.debug("Old Position",pos_old)


        for n in range(50): 

            log_string+="%s; " % str(time.strftime("%Y_%m_%d_%H_%M_%S"))

            drive=self.arduino.driveMotor("+"+NEXT)
            log_string+="%s; " % (drive.strip('\n'))
            pos_new=self.encoder.readPosition()
            log_string+="%s; " % (str(pos_new))
            adjPos=self.adjustPosition(pos_new, adj=ADJUST, stp=STEP) ###############
            log_string+="%s; " % str(adaPos)

            log_string+="%s; " % str(time.strftime("%Y_%m_%d_%H_%M_%S"))

            self.log.info(log_string)
            log_string=""
            time.sleep(DELAY)

    def adjustPosition(self, pos, adj, stp):

        def getSign(x):
            if x<0:
                return "-"
            else:
                return "+"

        adjPos=pos
        foundPos=False

        while foundPos==False:
            cmmdstr=""
            diff=[]
            sign=[]

            self.log.debug("Wrong position, searching closest filter...")
            # find the filter which is closest
            for i in range(len(FILTERS)):
                diff.append(abs(FILTERS[i]-int(adjPos)))
                sign.append(getSign(FILTERS[i]-int(adjPos)))
            if diff[1] > 1000:
                diff[1]=abs(diff[0]-2048)
                sign[1]="+"

            
            filtndx=diff.index(min(diff))
            self.debug("Closest filter is %d (index %d)"%(FILTERS[filtndx],filtndx))

            # adjust direction
            cmmdstr+=sign[filtndx]

            # step size normal or small if very close
            if diff[filtndx]<4:
                cmmdstr+=stp
            else:
                cmmdstr+=adj

            # execute
            self.arduino=driveMotor(cmmdstr)
            adjPos=int(self.encoder.readPosition())
            self.log.debug("Adjust position from:",adjPos, " with step:",cmmdstr)

            if adjPos==FILTERS[filtndx]:
                foundPos=True
                self.log.debug("Found position")
                return adjPos
            elif adjPos==2047:
                ERRCNT-=1
                if ERRCNT == 0:
                    raise RuntimeError
            else:
                self.log.debug("Position not found")
                time.sleep(1)


###################################################################################################
# encoder
class Encoder:
    def __init__(self,path, log):
        self.path=path
        self.log=log

    def connect(self):
        self.encoder=serial.Serial(self.path, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
        self.log.debug ("Initiated Encoder.")
        setupEncoder(self.encoder)
        self.log.info ("Encoder ready!")

    def setupEncoder(self):
        self.log.debug("Setting up Encoder...")
        self.encoder.write(SETUP_P34)
        self.encoder.readline()
        self.log.debug("Initialising Encoder...")
        self.encoder.write(SETUP_P35)
        self.encoder.readline()
        self.log.debug("Encoder is ready!")

    def close_connection(self):
        if hasattr(self, 'encoder'):
            self.log.info("Connection to Encoder closed!")

    def readPosition(self):
        self.encoder.write(READPOSITION)
        pos=self.encoder.readline()
        #print("Read Position: %s"%str(pos))
        pos=pos[2:-6] # rest is rubbish
        print("Read Position: %s"%str(pos))
        return pos

###################################################################################################
# example how to run:

if __name__=="__main__":

    logger=log(save=True, level=log_level, directory=log_dir, 
                    end="fw.log", # use different ending than pico main script, to make sure there is no override
                    )
    while(True): # use this in case there is suddenly a deconnection of devices
        
        try:
            
            encoder=Encoder(encoder_path, logger)
            encoder.connect()

            arduino=Arduino(arduino_path, encoder, logger)
            arduino.connect()

            time.sleep(DELAY)            
            
            arduino.run(Arduino, Encoder)
            
            break
        except serial.SerialException as e:
            traceback.print_exc()
            if 'arduino' in globals(): arduino.close_connection()
            if 'encoder' in globals(): encoder.close_connection()
            continue
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            traceback.print_exc()
            if 'arduino' in globals(): arduino.close_connection()
            if 'encoder' in globals(): encoder.close_connection()
            break

###################################################################################################












