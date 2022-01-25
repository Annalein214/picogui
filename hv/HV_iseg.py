import serial
import time
import datetime



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

voltages_up = [s_voltage_100, s_voltage_200, s_voltage_300, s_voltage_400, s_voltage_500, s_voltage_600, s_voltage_700, s_voltage_800, s_voltage_900, s_voltage_1000, s_voltage_1100]

voltages_down = [s_voltage_1000, s_voltage_900, s_voltage_800, s_voltage_700, s_voltage_600, s_voltage_500, s_voltage_400, s_voltage_300, s_voltage_200, s_voltage_100, s_voltage_0]


def read_current_voltage(device):    
    for i in range(2):
        device.write(r_voltage)
        while device.inWaiting() == 0:
            time.sleep(0.1)
        device.readline()
        v_curr=device.readline()
        ck=check_answer(v_curr)
        if ck == 1:
            return v_curr
            break
        else:
            print("HV did not understand. Trying again.")
            print(ck)

def check_answer(answer):
    if answer.startswith('?'):
        return -1
    elif isDigit(answer):
        return 1
    else:
        print(answer)
        return 2

def isDigit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

def check_polarity(device, V):
    if V == 0.0:
        device.write(r_polarity)
        device.readline()
        pol=device.readline()
        if pol == '+':
            pass
        elif pol == '-':
            device.write(s_polarity_pos)
            device.readline()
    else:
        device.write(s_voltage_0)
        device.readline()

def ramp_up(device):
    print("\nRamping up HV - please wait!")    
    time.sleep(1)
    for i in range(len(voltages_up)): 
        device.write(voltages_up[i])
        print("Device output",device.readline())
        time.sleep(2)
        V=read_current_voltage(device)
        print("Voltage:",V)
        time.sleep(5)
    print("Finished ramp up!")

def ramp_down(device):
    print("\nRamping down HV - please wait!")
    v_ini=read_current_voltage(device)

    if v_ini == "0.0":
        print("HV already off!")
        return

    else:
        print(v_ini)
        time.sleep(1)
        for i in range(len(voltages_down)): 
            device.write(voltages_down[i])
            device.readline()
            time.sleep(2)
            V=read_current_voltage(device)
            print("Voltage:",V)
            time.sleep(5)
    print("Finished ramp down! Good bye!")


def start_connection():
    HV=serial.Serial("/dev/ttyUSB1", 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
    print("connected to HV")

    V_curr = float(read_current_voltage(HV))
    print("Voltage: ",V_curr)
    return HV

def close_connection(dev):
    dev.close()
    print("Connection to HV closed.")

def logging(msg):
    log

def take_data(HV):
  
    HV_log=[]
    V_curr = float(read_current_voltage(device))

    t=datetime.datetime.now()
    t_str=t.strftime("%Y_%m_%d_%H_%M_%S")
    HV_log.append(t_str)
    HV_log.append(V_curr)
    print(t_str)
    print(V_curr)

    if V_curr == 0.0:
        HV.write(s_polarity_pos)
        HV_log.append(HV.readline())
        ramp_up(HV)
    elif V_curr >= 1000.0:
        pass
    else:
        HV.write(s_voltage_0)
        HV_log.append(HV.readline())
        HV.write(s_polarity_pos)
        HV_log.append(HV.readline())
        ramp_up(HV)
    
    while True:
        t1=datetime.datetime.now()
        t1_str=t1.strftime("%Y_%m_%d_%H_%M_%S")
        V=read_current_voltage(HV)
        HV_log.append(t1)
        HV_log.append(V)
        print(V)
        if t1-t < datetime.timedelta(hours=1):
            with open("HVlog_"+t_str+".txt", 'a') as f:
                for item in HV_log:
                    f.write("%s\n" % item)
        elif t1-t > datetime.timedelta(hours=1):
            with open("HVlog_"+t1_str+".txt", 'a') as f:
                for item in HV_log:
                    f.write("%s\n" % item)
            t=t1
            t_str=t1_str

        HV_log=[]
        time.sleep(1)

if __name__=="__main__":
  while True:
    try:
        device = start_connection()
        take_data(device)
    except (KeyboardInterrupt, SystemExit):
        ramp_down(device)
        close_connection(device)
        break
    except serial.SerialException as e:
        print("ERROR",e)
        close_connection(device)
        continue
    

    
        
