from __future__ import print_function
from __future__ import absolute_import

import serial, sys, glob
import numpy as np

port="/dev/ttyUSB0"

class Hygrosens:

    def readDevice(self):
        # the device gives a 11 bit value back which goes from -50 to +200 degrees Celsius
        # that is the reason for the following factor and the substraction of 50 later on
        factor = 2048.0/200 
        self.device.write("t")
        raw = self.device.readline()
        temperatures=[round(int(i,16)/factor-50,2) for i in raw.split(";")[1:5]]
        self.log.debug("HY: Raw: %s"% raw)
        #print(temperatures)
        #print(";".join(["%f" % i for i in temperatures]))
        self.log.debug("HY: Temp: %s"% (";".join(["%f" % i for i in temperatures])))
        return np.array(temperatures)

    def initialise(self,):
        self.device=serial.Serial(str(self.port), 9600,timeout=2)

    def test(self, port):
        try:
        #if True:
            self.log.info("HY: Test Port:%s"% port)
            self.port=port
            self.initialise()
            temperatures=self.readDevice()
            if len(temperatures)==0: raise Exception("Wrong device, I assume. Temperature array empty.")
            return True
        except Exception as e:
            self.port=None
            try: self.device.close() 
            except: pass
            self.device=None
            self.log.info("HY: Error testing port %s: %s" %( port, e))
            return False
    
    def close_connection(self):
        if hasattr(self, 'device'):
            if self.device!=None:
                self.device.close()
                self.log.info("HY: Connection to Encoder closed!")

    def __init__(self, log,port=port):
        self.port=port
        self.log=log
        self.log.info("HY: Port given: %s"%port)
        if port != None:
            test=self.test(port)
            if test == False:
                self.port=None
    
        if port==None:
            # find a port 
            self.log.info("HY: No port given. Try to find port")
            if sys.platform.startswith('win'):
                ports = ['COM%s' % (i + 1) for i in range(256)]
                # not tested!
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                ports = glob.glob('/dev/ttyUSB*')
            elif sys.platform.startswith('darwin'):
                ports = glob.glob('/dev/tty.*')
                # not tested!
            else:
                raise EnvironmentError('Unsupported platform')
            #print "Test ports", ports
            for port in ports:
                test=self.test(port)
                if test==True:
                    self.port=port
                    break
                    #print "Port found", port
                    
        if self.port==None:
            self.log.error("HY: No port found. Measurement switched off!")
        else:
            self.log.info("HY: Using device at port %s" % self.port)


##########################################################################################

if __name__ == "__main__":

    from log import log
    log=log(save=False, level="debug")
    t=Hygrosens(log, port=port)

    print (t.readDevice())







