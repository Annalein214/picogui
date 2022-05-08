from __future__ import print_function
from __future__ import absolute_import

import serial, time, sys, traceback, os
from glob import glob

sys.path.append("../code/")
from log import log

###################################################################################################
# Configuration

VOLTAGE=1100

port="/dev/ttyUSB1"

log_dir=os.getcwd()+"/log/" # current directory

log_level="debug" # debug, info


###################################################################################################
# constants

r_voltage = bytearray([0x55, 0x31, 0x0D, 0x0A])
r_set_voltage = bytearray([0x55, 0x31, 0x0D, 0x0A])
r_polarity = bytearray([0x50, 0x31, 0x0D, 0x0A])
s_polarity_pos = bytearray([0x50, 0x31, 0x3D, 0x2B, 0x0D, 0x0A])
###################################################################################################
# data table

class DATA:

    def __init__(self,log_dir, logger):
        self.log_dir=log_dir
        self.i=0
        

        t=time.time()
        #self.starttime=t
        #self.time=t

        self.filename=self.log_dir+"/"+logger.formatTimeforLog(t)+".hv.csv"
        f=open(self.filename, "a")
        f.write("#Timestamp, Voltage / V\n")
        f.close()
        self.time=t

    def save(self,voltage):
        t=time.time()
        f=open(self.filename, "a")
        f.write("%f,%d\n" % (t,voltage))
        f.close()
    




    

###################################################################################################


class HV:
    def __init__(self,port, logger, data):
        self.port=port
        self.log=logger
        self.data=data

        # check if given port is ok
        if port != None:
            test=self.test(port)
            if test == False:
                self.port=None
    
        # search for the correct port
        if port==None:
            # find a port 
            self.log.info("HV: No port given. Try to find port")
            ports=self.findPorts()
            self.log.debug("HV: Potential ports: %s"%(", ".join(ports)))

            # test potential ports
            for port in ports:
                test=self.test(port)
                if test==True:
                    self.port=port
                    break
                    
        if self.port==None:
            self.log.error("HV: No port found. Measurement switched off!")
        else:
            self.log.info("HV: Using device at port %s" % self.port)

    def test(self, port):
        try:
            self.log.info("HV: Test Port:%s"% port)
            self.port=port
            v_curr=self.start_connection()
            # todo check v_curr
            return True
        except Exception as e:
            self.port=None
            try: self.close_connection()
            except: pass
            self.hv=None
            self.log.info("HV: Error testing port %s: %s" %( port, e))
            return False

    def findPorts(self):
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
        return ports

    def start_connection(self):
        self.hv=serial.Serial(self.port, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE ,timeout=2)
        self.log.info("HV: connected to HV at %s"%self.port)

        V_curr = float(self.read_current_voltage())
        if V_curr==None: raise Exception("HV ERROR: connected but cannot understand answer.")
        self.log.info("HV: Current Voltage: %f"%V_curr)
        return V_curr

    def read_current_voltage(self):    
        for i in range(2):
            self.hv.write(r_voltage)
            while self.hv.inWaiting() == 0:
                time.sleep(0.1)
            self.hv.readline()
            v_curr=self.hv.readline()
            ck=self.check_answer(v_curr)
            if ck == 1:
                self.data.save(float(v_curr))
                return v_curr
                break
            elif i==0:
                self.log.info("HV: did not understand. Trying again. Message: %s"%str(ck))
            else:
                self.log.info("HV: did not understand. Message: %s"%str(ck))
                return None

    def check_answer(self,answer):
        if answer.startswith('?'):
            return -1
        elif self.isDigit(answer):
            return 1
        else:
            print(answer)
            return 2

    def isDigit(self,x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    def check_polarity(self, V):
        if V == 0.0:
            self.hv.write(r_polarity)
            self.hv.readline()
            pol=self.hv.readline()
            if pol == '+':
                pass
            elif pol == '-':
                self.hv.write(s_polarity_pos)
                self.hv.readline()
        else:
            self.hv.write(s_voltage_0)
            self.hv.readline()

    def getVoltageByteArray(self,voltage):
        lyst=list([0x44, 0x31, 0x3D])
        for letter in str(voltage):
            lyst.append(0x30+int(letter))
        lyst.extend([0x0D, 0x0A])
        byteAarray=bytearray(lyst)
        return byteAarray # format: D1=1000\r\n

    def ramp(self, goal):
        self.log.info("HV: Adjusting HV to %d V, please wait ..."% goal)
        # current voltage: 
        v_ini=int(float(self.read_current_voltage()))

        if v_ini >= goal: 
            self.log.debug("HV: Current value higher than new: ramp down")
            diff=int(float(v_ini))-goal
        else: # v_ini < goal
            self.log.debug("HV: Current value lower than new: ramp up")
            diff=goal - v_ini

        steps= int(diff/100)
        stopploop=False

        for i in range(steps+2):
            if v_ini > goal: 
                int_goal=v_ini-i*100
                if int_goal<= goal: 
                    int_goal=goal
                    stopploop=True
            elif v_ini < goal: # v_ini < goal
                int_goal=v_ini+i*100
                if int_goal>= goal: 
                    int_goal=goal
                    stopploop=True
            else: # vini=goal:
                continue
            self.log.debug("HV: Set HV to: %f" % (int_goal))
            self.hv.write(self.getVoltageByteArray(int_goal))
            self.log.debug("HV: Device output: %s" % str(self.hv.readline()))
            time.sleep(3)
            V=int(float(self.read_current_voltage()))
            self.log.info("HV: Voltage: %f"%float(V))
            if abs(V-int_goal) > 100: 
                self.log.error("Voltage adjustment seems not to work. Wanted to reach %f"%int_goal)
            time.sleep(1) # sarah used 5 sec
            if stopploop: break
        self.log.info("HV: Finished adjusting HV")

    def close_connection(self):
        if hasattr(self, 'encoder'):
            if self.hv!=None:
                self.hv.close()
                self.log.info("HV: Connection to HV closed.")

    def take_data(self):
      
        V_curr = float(self.read_current_voltage())
        self.log.info("HV: take_data: voltage: %f"%(V_curr))

        if V_curr == 0.0:
            self.hv.write(s_polarity_pos)
            self.log.info("HV: take_data: s_polarity_pos: %s"%(str(self.hv.readline())))
        elif V_curr <= 0.0:
            self.hv.write(getVoltageByteArray(0))
            self.log.info("HV: take_data: s_voltage_0: %s"%(self.hv.readline()))
            self.hv.write(s_polarity_pos)
            self.log.info("HV: take_data: s_polarity_pos: %s"%(self.hv.readline()))
        # else: v_curr > 0    
        self.ramp(VOLTAGE)
        
        # log HV
        while True:
            V=self.read_current_voltage()
            self.log.info("HV: take_data: voltage: %f"%float(V))
            time.sleep(1)
###################################################################################################
# example how to run:

if __name__=="__main__":

    logger=log(save=True, level=log_level, directory=log_dir, 
                    end="hv.log", # use different ending than pico main script, to make sure there is no override
                    )

    data=DATA(log_dir, logger)

    while True:
        try:
            hv=HV(port, logger, data)
            hv.take_data()
        except (KeyboardInterrupt, SystemExit) as e:
            e2=str(traceback.print_exc())
            logger.error(e2)
            logger.error(str(e))
            hv.ramp(0)
            hv.close_connection()
            break
        except serial.SerialException as e:
            e2=str(traceback.print_exc())
            logger.error(e2)
            logger.error(str(e))
            hv.close_connection()
            continue

###################################################################################################










    

    
        
