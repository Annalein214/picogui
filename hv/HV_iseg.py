from __future__ import print_function
from __future__ import absolute_import

import serial, time, sys, traceback
from glob import glob

sys.path.append("../code/")
from log import log

###################################################################################################
# Configuration

path="/dev/ttyUSB1"

log_dir=os.getcwd() # current directory

log_level="debug" # debug, info

###################################################################################################
# Definitions

r_voltage = bytearray([0x55, 0x31, 0x0D, 0x0A])
r_set_voltage = bytearray([0x55, 0x31, 0x0D, 0x0A])
s_voltage_0 = bytearray([0x44, 0x31, 0x3D, 0x30, 0x0D, 0x0A])
s_voltage_100 = bytearray([0x44, 0x31, 0x3D, 0x31, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_200 = bytearray([0x44, 0x31, 0x3D, 0x32, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_300 = bytearray([0x44, 0x31, 0x3D, 0x33, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_400 = bytearray([0x44, 0x31, 0x3D, 0x34, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_500 = bytearray([0x44, 0x31, 0x3D, 0x35, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_600 = bytearray([0x44, 0x31, 0x3D, 0x36, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_700 = bytearray([0x44, 0x31, 0x3D, 0x37, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_800 = bytearray([0x44, 0x31, 0x3D, 0x38, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_900 = bytearray([0x44, 0x31, 0x3D, 0x39, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_1000 = bytearray([0x44, 0x31, 0x3D, 0x31, 0x30, 0x30, 0x30, 0x0D, 0x0A])
s_voltage_1100= bytearray([0x44, 0x31, 0x3D, 0x31, 0x31, 0x30, 0x30, 0x0D, 0x0A])
r_polarity = bytearray([0x50, 0x31, 0x0D, 0x0A])
s_polarity_pos = bytearray([0x50, 0x31, 0x3D, 0x2B, 0x0D, 0x0A])

voltages_up = [s_voltage_100, s_voltage_200, s_voltage_300, s_voltage_400, 
               s_voltage_500, s_voltage_600, s_voltage_700, s_voltage_800, 
               s_voltage_900, s_voltage_1000, s_voltage_1100]

voltages_down = [s_voltage_1000, s_voltage_900, s_voltage_800, s_voltage_700, 
                 s_voltage_600, s_voltage_500, s_voltage_400, s_voltage_300, 
                 s_voltage_200, s_voltage_100, s_voltage_0]


###################################################################################################


class HV:
    def __init__(self,path, log):
        self.path=path
        self.log=log

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
            try: self.close_connection(); except: pass
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
        self.hv=serial.Serial(self.path, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE ,timeout=2)
        self.log.info("HV: connected to HV at %s"%self.path)

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
        elif isDigit(answer):
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

    def ramp_up(self):
        self.log.info("HV: Ramping up HV - please wait!")    
        time.sleep(1)
        for i in range(len(voltages_up)): 
            self.HV_log.write(voltages_up[i])
            self.log.debug("HV: Device output %s" % str(device.readline()))
            time.sleep(2)
            V=read_current_voltage(device)
            self.log.info("HV: Voltage:",V)
            time.sleep(5)
        self.log.info("HV: Finished ramp up!")

    def ramp_down(self):
        self.log.info("HV: Ramping down HV - please wait!")
        v_ini=read_current_voltage(self.hv)

        if v_ini == "0.0":
            self.log.info("HV: HV already off!")
            return

        else:
            self.log.debug("HV: Current voltage: %f"%v_ini)
            time.sleep(1)
            for i in range(len(voltages_down)): 
                self.hv.write(voltages_down[i])
                self.hv.readline()
                time.sleep(2)
                V=self.read_current_voltage()
                self.log.info("HV: Voltage: %f"%V)
                time.sleep(5)
        self.log.info("HV: Finished ramp down! Good bye!")


    def close_connection(self):
        if hasattr(self, 'encoder'):
            if self.hv!=None:
                self.hv.close()
                self.log.info("HV: Connection to HV closed.")

    def take_data(HV):
      
        V_curr = float(self.read_current_voltage())
        self.log.info("HV: take_data: voltage: %s %f"%(V_curr))

        if V_curr == 0.0:
            self.hv.write(s_polarity_pos)
            self.log.info("HV: take_data: s_polarity_pos: %s %f"%(self.hv.readline()))
            self.ramp_up()
        elif V_curr >= 1000.0:
            pass
        else:
            self.hv.write(s_voltage_0)
            self.log.info("HV: take_data: s_voltage_0: %s %f"%(self.hv.readline()))
            self.hv.write(s_polarity_pos)
            self.log.info("HV: take_data: s_polarity_pos: %s %f"%(self.hv.readline()))
            self.ramp_up()
        
        while True:

            V=self.read_current_voltage()
            self.log.info("HV: take_data: voltage: %s %f"%(V))

            time.sleep(1)
###################################################################################################
# example how to run:

if __name__=="__main__":

    logger=log(save=True, level=log_level, directory=log_dir, 
                    end="fw.log", # use different ending than pico main script, to make sure there is no override
                    )

    while True:
        try:
            hv=HV()
            hv.take_data()
        except (KeyboardInterrupt, SystemExit):
            traceback.print_exc()
            hv.ramp_down()
            hv.close_connection()
            break
        except serial.SerialException as e:
            traceback.print_exc()
            self.log.error("HV: %s"%str(e))
            hv.close_connection()
            continue

###################################################################################################










    

    
        
