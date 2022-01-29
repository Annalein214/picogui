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
arduino_path="/dev/ttyUSB3"
encoder_path="/dev/ttyUSB2"

log_dir=os.getcwd() # current directory

log_level="debug" # debug, info

test_with_short_times=False 

cold=False


###################################################################################################
# Definitions

# bits to setup the encoder
# the 1 has to be between '' !
SETUP_P34=bytearray([2, '1', 0x59, 0x50, 0x33, 0x34, 0x53, 0x32, 0x3A, 0x58, 0x58, 0x03, 13, 10])
SETUP_P35=bytearray([2, 0x31, 0x59, 0x50, 0x33, 0x35, 0x53, 0x31, 0x31, 0x3A, 0x58, 0x58, 0x03, 13, 10])
# command to readposition
READPOSITION=bytearray([2, 0x31, 0x59, 0x50, 0x32, 0x32, 0x52, 0x3A, 0x58, 0x58, 0x03, 13, 10])

# Filter positions
FILTER450 = 2022
FILTER425 = 1816
FILTER400 = 1612
FILTER375 = 1407
FILTER350 = 1205
FILTER325 = 1001
OPEN = 796
CLOSED = 592    # looks good by eye
FILTER500 = 386
FILTER475 = 179

# order of filters
FILTERS = [FILTER450, FILTER475, FILTER500, CLOSED, OPEN, FILTER325, FILTER350, FILTER375, FILTER400, FILTER425]

# steps at warm temperatures
NEXT = "0745"
ADJUST = "0010"
STEP = "0005"
if cold:     # steps at cold temperatures
    NEXT= "1045"
    ADJUST="0015"
    STEP="0007"

ERRCNT = 5

if test_with_short_times:
    DELAY=60
else:
    DELAY=3600
###################################################################################################
# arduino

class Arduino:

    def __init__(self,port, encoder, log):
        self.port=port
        self.log=log
        self.encoder=encoder

        # check if given port is ok
        if port != None:
            test=self.test(port)
            if test == False:
                self.port=None

        # search for the correct port  #### here  TODO
        if port==None:
            # find a port 
            self.log.info("FA: No port given. Try to find port")
            ports=self.findPorts()
            self.log.debug("FA: Potential ports: %s"%(", ".join(ports)))

            # test potential ports
            for port in ports:
                test=self.test(port)
                if test==True:
                    self.port=port
                    break
                    
        if self.port==None:
            self.log.error("FA: No port found. Measurement switched off!")
        else:
            self.log.info("FA: Using device at port %s" % self.port)


    def test(self, port):
        try:
            self.log.info("FW: Test Port:%s"% port)
            self.port=port
            self.connect()
            return True
        except Exception as e:
            self.port=None
            try: self.close_connection() 
            except: pass
            self.encoder=None
            self.log.info("FW: Error testing port %s: %s" %( port, e))
            return False

    def connect(self,):
        self.arduino=serial.Serial(self.port, 9600, timeout=10)
        self.log.debug("FA: Initiated Arduino")
        self.waitForArduino()
        self.log.info("FA: Arduino ready!")

    def close_connection(self):
        if hasattr(self, 'arduino'):
            if self.arduino!=None:
                self.arduino.close() #'str' object has no attribute 'close'
                self.log.info("FA: Connection to Arduino closed!")

    def waitForArduino(self):
        # wait for Arduino response after boot up
        msg=""
        self.log.debug("FA: Waiting for Arduino...")
        while msg.find("Arduino is ready") == -1:
            while self.arduino.inWaiting() == 0:
                pass
            msg = str(self.arduino.readline()).strip('\n')
            self.log.debug("FA: Wait for Arduino: %s"%msg)


    def driveMotor(self, x):
        #print("Drive step: %s"%x)
        cmmd=x+"\n"
        self.arduino.write(cmmd)
        return self.arduino.readline()

    def run(self):
        self.log.info("FA: RUN")

        # make log entry
        log_string=""
        pos_old=self.encoder.readPosition()
        log_string+=str(pos_old)+"; "
        self.log.debug("FA: Old Position %s"%pos_old)

        for n in range(50): 
            log_string+="%s; " % str(time.strftime("%Y_%m_%d_%H_%M_%S"))
            drive=self.driveMotor("+"+NEXT)
            log_string+="%s; " % (drive.strip('\n'))
            pos_new=self.encoder.readPosition()
            log_string+="%s; " % (str(pos_new))
            adjPos=self.adjustPosition(pos_new, adj=ADJUST, stp=STEP) ###############
            log_string+="%s; " % str(adjPos)

            log_string+="%s; " % str(time.strftime("%Y_%m_%d_%H_%M_%S"))

            self.log.info("FA: Log String: %s"%log_string)
            log_string=""
            time.sleep(DELAY)

    def adjustPosition(self, 
                       pos, # new position
                       adj, # large step size
                       stp, # small step size
                       ): 

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
            self.log.debug("FA: Wrong position, searching closest filter...")
            # find the filter which is closest
            for i in range(len(FILTERS)):
                diff.append(abs(FILTERS[i]-int(adjPos)))
                sign.append(getSign(FILTERS[i]-int(adjPos)))
            if diff[1] > 1000:
                diff[1]=abs(diff[0]-2048)
                sign[1]="+"

            
            filtndx=diff.index(min(diff))
            self.log.debug("FA: Closest filter is %d (index %d)"%(FILTERS[filtndx],filtndx))

            # adjust direction
            cmmdstr+=sign[filtndx]

            # step size normal or small if very close
            if diff[filtndx]<4:
                cmmdstr+=stp
            else:
                cmmdstr+=adj

            # execute
            ret=self.driveMotor(cmmdstr)
            adjPos=int(self.encoder.readPosition())
            self.log.debug("FA: Adjust position from: %s with step: %s"%( adjPos,cmmdstr))

            if adjPos==FILTERS[filtndx]:
                foundPos=True
                self.log.debug("FA: Found position")
                return adjPos
            elif adjPos==2047:
                ERRCNT-=1
                if ERRCNT == 0:
                    raise RuntimeError
            else:
                self.log.debug("FA: Position not found")
                time.sleep(1)


###################################################################################################
# encoder
class Encoder:
    def __init__(self,port, log):
        self.port=port
        self.log=log

        if port != None:
            test=self.test(port)
            if test == False:
                self.port=None
    
        # search for the correct port  #### here  TODO
        if port==None:
            # find a port 
            self.log.info("FW: No port given. Try to find port")
            ports=self.findPorts()
            self.log.debug("FW: Potential ports: %s"%(", ".join(ports)))

            # test potential ports
            for port in ports:
                test=self.test(port)
                if test==True:
                    self.port=port
                    break
                    
        if self.port==None:
            self.log.error("FW: No port found. Measurement switched off!")
        else:
            self.log.info("FW: Using device at port %s" % self.port)


    def test(self, port):
        try:
            self.log.info("FW: Test Port:%s"% port)
            self.port=port
            self.connect()
            self.readPosition()
            return True
        except Exception as e:
            self.port=None
            try: self.close_connection() 
            except: pass
            self.encoder=None
            self.log.info("FW: Error testing port %s: %s" %( port, e))
            return False


    def connect(self):
        self.encoder=serial.Serial(self.port, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
        self.log.debug ("FW: Initiated Encoder %s"%self.port)
        self.setupEncoder()
        self.log.info ("FW: Encoder ready!")

    def setupEncoder(self):
        self.log.debug("FW: Setting up Encoder...")
        self.encoder.write(SETUP_P34)
        self.encoder.readline()
        self.log.debug("FW: Initialising Encoder...")
        self.encoder.write(SETUP_P35)
        self.encoder.readline()
        self.log.debug("FW: Encoder is ready!")

    def close_connection(self):
        if hasattr(self, 'encoder'):
            if self.encoder!=None:
                self.encoder.close()
                self.log.info("FW: Connection to Encoder closed!")

    def readPosition(self):
        self.encoder.write(READPOSITION)
        pos=self.encoder.readline()
        #print("Read Position: %s"%str(pos))
        pos=pos[2:-6] # rest is rubbish
        self.log.debug("FW: Read Position: %s"%str(pos))
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

            arduino=Arduino(arduino_path, encoder, logger)

            if not test_with_short_times: time.sleep(DELAY)            
            
            arduino.run()
            
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
        except: 
            traceback.print_exc()
            if 'arduino' in globals(): arduino.close_connection()
            if 'encoder' in globals(): encoder.close_connection()
            break

###################################################################################################












