import network
import os
import time
import socket
import json
import esp
import machine
from machine import I2C, Pin
import time
from machine import Pin,DAC
import utime, math
import _thread

wlanConfig = "undefind"
cpu_value = 0
ram_value = 0
timedown = 500
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dac_pin25 = Pin(25, Pin.OUT)
dac_pin26 = Pin(26, Pin.OUT)
dac25 = DAC(dac_pin25)
dac26 = DAC(dac_pin26)

def getTime():
    t = time.gmtime()
    timeY = str(t[0]) #年
    timeM = str(t[1]) #月
    timeD = str(t[2]) #日
    timeHour = str(t[3]) #时
    timeMinute = str(t[4]) #分
    timeSecond = str(t[5]) #秒
    return str(timeY+"/"+timeM+"/"+timeD +" "+timeHour+":"+timeMinute+":"+timeSecond)
def lerp(v1,v2,d):
    return v1 * (1 - d) + v2 * d

def dacThread( threadName, delay):
    global ram_value
    ramlerp = 0
    i = 0.0
    while(True):
        i += 0.01
        ramlerp = lerp(ramlerp,ram_value,i)
        dac25.write(int(ramlerp))
        if(i >= 1.0):
            i = 0.0
        #time.sleep(0.5)
        
        
def dacThread2( threadName, delay):
    global cpu_value
    cpulerp = 0
    i = 0.0
    while(True):
        i += 0.01
        cpulerp = lerp(cpulerp,cpu_value,i)
        dac26.write(int(cpulerp))
        if(i >= 1.0):
            i = 0.0
        #time.sleep(0.5)
        
def dacThread3( threadName, delay):
    global ram_value
    global cpu_value
    global timedown
    while(True):
        try:
            timedown = 500
            data,addr=s.recvfrom(32)
            stringKey = data.decode("utf-8")
            array_value =  stringKey.split(",")    
            cpu_value = int(array_value[1])
            ram_value = int(array_value[0])
            time.sleep(0.1)
        except Exception as e:
            print(e)
            time.sleep(0.1)
def connectDown(threadName):
    global timedown
    global ram_value
    global cpu_value
    while(True):
        if timedown < 0:
            print("udp Pack Time Out Reset")
            cpu_value = 0
            ram_value = 0
            time.sleep(5)
            cpu_value = 200
            ram_value = 200
            time.sleep(5)
            machine.reset()
        else:
            timedown = timedown - 1
        time.sleep(0.01)
def tryConnectWifi(wlanSetting):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    wlan.active(True)
    print(wlanSetting)
    if type(wlanSetting) != dict:
        while True:
            print("Wait to connect Setting Wifi")
            for wlanInfo in wlan.scan():
                wlanName = str(wlanInfo[0]).replace('b','').replace("'",'').encode('raw_unicode_escape').decode()
                if wlanName == "Setting":
                    wlan.connect("Setting","123456789")
                    while not wlan.isconnected():
                        time.sleep(0.5)
                        pass
                    print('Success Connect Setting Wifi.')
                    wlanConfig = wlan.ifconfig()
                    print('network config:',wlanConfig)
                    initMainConfig(list(wlanConfig))
                    return
            time.sleep(5)
    else:
        retryTime = 0
        print('Try Connect Wifi')
        while retryTime < 10:
            wlan.connect(wlanSetting["wifiSid"],wlanSetting["wifiPassword"])
            time.sleep(5)
            wlanConfig = wlan.ifconfig()
            if not wlan.isconnected():
                retryTime = retryTime + 1
            else:
                print('Success Connect Wifi')
                print('network config:',wlanConfig)
                s.bind((list(wlanConfig)[0],4499))
                return
        os.remove("main.config")
        reset()
    return
def initConfig():
    if "main.config" in os.listdir():
        configfile = open("main.config")
        config = configfile.read()
        wlanSetting = json.loads(config)
        configfile.close()
    else:
        wlanSetting = "undefind"
    return wlanSetting
def initMainConfig(Config):
    print(Config[0])
    s.bind((str(Config[0]),4499))
    print("wait Setting Info")
    while True:
        data, addr = s.recvfrom(1024)
        recvData = data.decode("utf-8")
        print(recvData)
        trueData = json.loads(recvData)
        if trueData["head"] == "setting":
            print("Recv Setting Data",trueData)
            writeSettingFile(trueData["data"])
            machine.reset()
            return
def writeSettingFile(setting):
    files = open("main.config",mode='w+')
    files.write(json.dumps({'wifiSid':setting["ssid"],'wifiPassword':setting["password"]}))
    files.flush()
    files.close()
    return

try:
    tryConnectWifi(initConfig())
except:
    machine.reset()
dac25.write(0)
dac26.write(0)
_thread.start_new_thread( dacThread, ("Thread_1", 1, ) )
_thread.start_new_thread( dacThread2, ("Thread_2", 2, ) )
_thread.start_new_thread( dacThread3, ("Thread_3", 3, ) )
_thread.start_new_thread( connectDown, ("Thread_4",) )


