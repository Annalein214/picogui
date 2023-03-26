from __future__ import print_function
from __future__ import absolute_import

import serial, sys, glob, traceback
import numpy as np

port="/dev/ttyUSB0"

class Photodiode:

    def readDevice(self):
        # get the data
        self.initialise()
        if self.device==None:
            return False
        # the device gives a float value in millivoltage after the string "Diode "
        raw = self.device.readline()
        self.log.debug("PA: Raw1: %s"% raw)
        string = str(raw)
        self.log.debug("PA: Raw2: %s"% string)

        string = string.replace("\\r", "").replace("\\n", "").replace("b'", "").replace("'", "")
        self.log.debug("PA: Raw3: %s"% string)

        if not "Diode" in str(string):
            raise RuntimeError("PA: Value not from Diode: %s" % raw)
        voltage=float(string.split(" ")[1])

        self.log.debug("PA: Voltage: %f"% voltage)
        self.device.close()
        return voltage

    def initialise(self,):
        # start connection to device, used by test()
        self.device=serial.Serial(str(self.port), 9600,timeout=2)

    def test(self, port):
        # tests a port and initializes it => stop once port found, otherwise wrong device will get initialized
        try:
        #if True:
            self.log.info("PA: Test Port %s for photodiode"% port)
            self.port=port
            self.initialise()
            if self.device==None:
                raise Exception("No device initialised!")
            voltage=self.readDevice()
            self.device.close()
            return True
        except Exception as e:
            #e2=str(traceback.print_exc())
            #print(e2)
            self.port=None
            try: self.device.close() 
            except: pass
            self.device=None
            self.log.info("PA: Error testing port %s: %s" %( port, e))
            return False


    def __init__(self, log,port=port):
        '''
        - test port given to function
        - list all possible ports
        - test the ports
        - initilaizes the working port
        '''
        self.port=port
        self.log=log
        self.log.info("PA: Port given: %s"%port)

        if port != None:
            test=self.test(port)
            if test == False:
                self.port=None
    
        if self.port==None:

            # find a port 
            self.log.info("PA: No port given. Try to find port for platform "+sys.platform)
            if sys.platform.startswith('win'):
                ports = ['COM%s' % (i + 1) for i in range(256)]
                # not tested!
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # access to serial ports is given by
                # sudo usermod -a -G dialout USERNAME
                ports = glob.glob('/dev/ttyUSB*')
            elif sys.platform.startswith('darwin'):
                ports = glob.glob('/dev/tty.*')
                # not tested!
            else:
                raise EnvironmentError('Unsupported platform')

            #print "Test ports", ports
            for port in ports:
                if "Bluetooth" in port: continue
                if "BLTH" in port: continue

                test=self.test(port)
                if test==True:
                    self.port=port
                    break
                    #print "Port found", port
                    
        if self.port==None:
            self.log.error("PA: No port found. Measurement switched off!")
            self.online=False
        else:
            self.log.info("PA: Using device at port %s for photodiode" % self.port)
            self.online=True


if __name__ == "__main__":

    # make a dummy log class
    class log:
        def __init__(self):
            pass
        def error(self, str):
            print("ERROR: "+str)
        def debug(self,str):
            print("DEBUG: "+str)
        def info(self,str):
            print("INFO: "+str)

    log=log()
    t=Photodiode(log, port=port)

    try:
       print (t.readDevice())
    except:
       pass




