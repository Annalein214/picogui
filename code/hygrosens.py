from __future__ import print_function
from __future__ import absolute_import

import serial, sys, glob
import numpy as np

class Hygrosens:

    def readDevice(self,port=None):
        if port==None: port=self.port
        # the device gives a 11 bit value back which goes from -50 to +200 degrees Celsius
        # that is the reason for the following factor and the substraction of 50 later on
        factor = 2048.0/200 
        s=serial.Serial(str(port), 9600,timeout=2)
        s.write("t")
        raw = s.readline()
        temperatures=[round(int(i,16)/factor-50,2) for i in raw.split(";")[1:5]]
        self.log.debug("Hygrosens Raw: %s"% raw)
        #print(temperatures)
        #print(";".join(["%f" % i for i in temperatures]))
        self.log.debug("Hygrosens Temp: %s"% (";".join(["%f" % i for i in temperatures])))
        s.close()
        if len(temperatures)==0: raise Exception("Wrong device, I assume. Temperature array empty.")
        return np.array(temperatures)

    def test(self, port):
        
        try:
        #if True:
            self.log.info("Hygrosens: Test Port:%s"% port)
            t=self.readDevice(port)
            return True
        except Exception as e:
        #else:
            self.log.info("Hygrosens: Error testing port %s: %s" %( port, e))
            return False
    
    def __init__(self, log,port=None):
        self.port=None
        self.log=log
    
        if port==None:
            # find a port 
            self.log.info("Hygrosens: No port given. Try to find port")
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
        else:
            test=self.test(port)
            if test==True:
                    self.port=port
                    #print "Port found", port
                    
        if self.port==None:
            self.log.error("Hygrosens: No port found. Measurement switched off!")
        else:
            self.log.info("Hygrosens: Using device at port %s" % self.port)


##########################################################################################

if __name__ == "__main__":

    from log import log
    log=log(save=False, level="debug")
    t=Hygrosens(log)

    print (t.readDevice())







