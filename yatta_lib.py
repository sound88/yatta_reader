import serial
import queue
import threading
import time
import arrow
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.basicConfig(filename = 'tag.log', format='[ %(asctime)s ][ %(name)s ][ %(levelname)s ] %(message)s')

yattaHTTPQ = queue.Queue()
yattaLogQ = queue.Queue()

## Initial Variable ###

COMMAND_SUCCESS = b'\10'

EPC_LEN = 12
epc_tag = []
uart = 0
rxBuff = []
yatta_mode = 0
sim_rx_idx = 0
timeoutFlag = False
sim_rx_inventory0 = [0xA0, 0x13, 0x01, 0x89, 0x8C, 0x30, 0x00, 0x30, 0x08, 0x33, 0xB2, 0xDD, 0xD9, 0x01, 0x40, 0x00, 0x00, 0x00, 0x01, 0x37, 0xBB]
sim_rx_inventory1 = [0xA0, 0x13, 0x01, 0x89, 0x74, 0x30, 0x00, 0xE2, 0x00, 0x40, 0x74, 0x85, 0x0A, 0x01, 0x03, 0x16, 0x30, 0x70, 0xE1, 0x36, 0x29]
sim_rx_inventory2 = [0xA0, 0x13, 0x01, 0x89, 0xD4, 0x30, 0x00, 0x30, 0x08, 0x33, 0xB2, 0xDD, 0xD9, 0x01, 0x40, 0x00, 0x00, 0x00, 0x01, 0x36, 0x74]
sim_rx_inventory3 = [0xA0, 0x13, 0x01, 0x89, 0xD4, 0x30, 0x00, 0xE2, 0x00, 0x40, 0x74, 0x85, 0x0A, 0x01, 0x03, 0x16, 0x30, 0x70, 0xE1, 0x35, 0xCA]
sim_rx_inventory4 = [0xA0, 0x13, 0x01, 0x89, 0xD4, 0x30, 0x00, 0xE2, 0x00, 0x40, 0x74, 0x85, 0x0A, 0x01, 0x03, 0x16, 0x90, 0x67, 0xDD, 0x2F, 0x7D]
sim_rx_inventory5 = [0xA0, 0x0A, 0x01, 0x89, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00, 0x05, 0xB6]




def timeout_handler():
    timeoutFlag = True
    
def timeout_start(timeout_sec):
    timeoutFlag = False
    threading.Timer(timeout_sec, timeout_handler).start()

def init(yatta_sim):
        global yatta_mode , uart
        yatta_mode = yatta_sim
        if(yatta_mode == 0):
            uart = serial.Serial('/dev/ttyS0',115200,timeout=1)
            uart.close()
            uart.open()
            return
        else:
            return
                        

def yatta_txData(dataBuff):
        global yatta_mode , uart
        if(yatta_mode == 0):
                uart.write(serial.to_bytes(dataBuff))

def yatta_waitRxReader(timeout_ms):
        global yatta_mode , uart , rxBuff
        uartRxBuff = []
        if(yatta_mode == 0): # Real hardware
            rx_idx = 0
            global rxBuff
            packLen = 0
            timeout_start(timeout_ms)
            while True:
                rxByte = uart.read(1)
                if(rx_idx == 0):
                    if(rxByte == b'\xa0'):   #if(rxByte.encode("hex") == "a0"):
                        #print("Header detected")
                        uartRxBuff.append(rxByte) #uartRxBuff.append(rxByte.encode('hex'))
                        rx_idx = rx_idx +1
                elif (rx_idx == 1):
                    packLen = int.from_bytes(rxByte, byteorder='little')
                    uartRxBuff.append(rxByte)
                    rx_idx = rx_idx +1
                else:
                    uartRxBuff.append(rxByte) #uartRxBuff.append(rxByte.encode('hex'))
                    rx_idx = rx_idx + 1

                if((rx_idx > 1) and (rx_idx - 2 == packLen)):
                    rxBuff = uartRxBuff
                    #print("rxBuff=", rxBuff)
                    return True
                if(timeoutFlag == True):
                    rxBuff = []
                    return False
        else: # simulation
            global sim_rx_idx
            if(sim_rx_idx == 0):
                rxBuff = sim_rx_inventory0
            elif(sim_rx_idx == 1):
                rxBuff = sim_rx_inventory1
            elif(sim_rx_idx == 2):
                rxBuff = sim_rx_inventory2
            elif(sim_rx_idx == 3):
                rxBuff = sim_rx_inventory3
            elif(sim_rx_idx == 4):
                rxBuff = sim_rx_inventory4
            elif(sim_rx_idx == 5):
                rxBuff = sim_rx_inventory5
            else:
                sim_rx_idx = 0
                return False
            sim_rx_idx = (sim_rx_idx+1)%6
            return True

#Cyclic Redundancy Check (CRC) computation includes all data from Len. A reference CRC computation program is presented as follow:
def CheckSum(uBuff, uBuffLen):
	i = 0
	uSum=0
	for i in range (0,uBuffLen):
	    uSum = uSum + uBuff[i]
	
	uSum = (~uSum) + 1
	return uSum%256

#uBuff = [0xA0 , 0x04 , 0x01 , 0x74 , 0x00]
#checksum_ans =  CheckSum(uBuff, 5)
#print(format(checksum_ansprint ,'#04X')

#A0 04 01 89 01 D1
#A0 13 01 89 8C 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 37 BB
#A0 13 01 89 74 30 00 E2 00 40 74 85 0A 01 03 16 30 70 E1 36 29
#A0 13 01 89 D4 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 36 74 
#A0 13 01 89 D4 30 00 E2 00 40 74 85 0A 01 03 16 30 70 E1 35 CA
#A0 13 01 89 D4 30 00 E2 00 40 74 85 0A 01 03 16 90 67 DD 2F 7D
#A0 0A 01 89 00 00 11 00 00 00 05 B6
yattaHTTPQ_lastGetAvailable = False
yattaHTTPQ_lastGetData = ""

def qHttp_Empty():
    global yattaHTTPQ
    return yattaHTTPQ.empty()
    
def getQHttp():
    global yattaHTTPQ
    global yattaHTTPQ_lastGetAvailable
    if(yattaHTTPQ.empty()):
        http_str = ""
    else:
        http_str = yattaHTTPQ.get()
    yattaHTTPQ_lastGetAvailable = False
    #print("getAHttp" + http_str
    return http_str
    
def peekQHttp():
    global yattaHTTPQ
    global yattaHTTPQ_lastGetData
    global yattaHTTPQ_lastGetAvailable
    if(yattaHTTPQ_lastGetAvailable == False):
        yattaHTTPQ_lastGetData = yattaHTTPQ.get()
        yattaHTTPQ_lastGetAvailable = True
    return yattaHTTPQ_lastGetData
def numQHTTP():
    global yattaHTTPQ
    global yattaHTTPQ_lastGetData
    global yattaHTTPQ_lastGetAvailable
    if(yattaHTTPQ_lastGetAvailable == False):
        return yattaHTTPQ.qsize()
    else:
        return yattaHTTPQ.qsize()+1
### End yattaHTTPQ

### Start yattaLogQ
yattaLogQ_lastGetAvailable = False
yattaLogQ_lastGetData = ""

def getQLog():
    global yattaLogQ
    global yattaLogQ_lastGetAvailable, yattaLogQ_lastGetData
    yattaLogQ_lastGetAvailable = False
    #print("Flushed QLog"
    return yattaLogQ.get()

def peekQLog():
    global yattaLogQ
    global yattaLogQ_lastGetAvailable, yattaLogQ_lastGetData
    if(yattaLogQ_lastGetAvailable == False):
        yattaLogQ_lastGetData = yattaLogQ.get()
        yattaLogQ_lastGetAvailable = True
    return yattaLogQ_lastGetData
def qLog_Empty():
    global yattaLogQ
    return yattaLogQ.empty()
### End yattaLogQ
tag_debug = 0 
        
def push_epc_tag(ts, epc_list):
    #import ipdb; ipdb.set_trace()
    global tag_debug, yattaHTTPQ, yattaLogQ, yatta_mode
    #Convert EPC to string of hex
    if(epc_list[0] == b'\xe2'):   #if(str(epc_list[0]) == "e2"):
        if(yatta_mode == 0):
            tagid_str = str(epc_list) #''.join(epc_list)
        else:
            tagid_str = str(epc_list) #''.join(format(x, '02X') for x in epc_list)
        #debug
        tag_debug = tag_debug+1
        yattaHTTPQ.put(str(tag_debug) + "&dev_time=" + str(ts))
        #yattaHTTPQ.put(str(tagid_str) + "&dev_time=" + str(ts))
        #yattaLogQ.put(str(ts)  + ' ' + str(tagid_str) + '\r\n') # Format data 1. timeStamp(UTC) epc_tag
#1/18/2017 9:53:22 PM  A0 04 01 74 01 E6
#1/18/2017 9:53:22 PM  A0 04 01 74 10 D7
#1/18/2017 9:53:22 PM  A0 04 01 89 01 D1
#1/18/2017 9:53:22 PM  A0 04 01 89 22 B0

#1/18/2017 9:53:22 PM  A0 04 01 74 02 E5
#1/18/2017 9:53:22 PM  A0 04 01 74 10 D7
#1/18/2017 9:53:22 PM  A0 04 01 89 01 D1
#1/18/2017 9:53:22 PM  A0 04 01 89 22 B0

#1/18/2017 9:53:22 PM  A0 04 01 74 03 E4
#1/18/2017 9:53:22 PM  A0 04 01 74 10 D7
#1/18/2017 9:53:22 PM  A0 04 01 89 01 D1
#1/18/2017 9:53:22 PM  A0 04 01 89 22 B0

#1/18/2017 9:53:22 PM  A0 04 01 74 00 E7
#1/18/2017 9:53:22 PM  A0 04 01 74 10 D7
#1/18/2017 9:53:22 PM  A0 04 01 89 01 D1
#1/18/2017 9:53:22 PM  A0 04 01 89 22 B0

#1/18/2017 9:53:22 PM  A0 04 01 74 01 E6
#1/18/2017 9:53:22 PM  A0 04 01 74 10 D7
#1/18/2017 9:53:22 PM  A0 04 01 89 01 D1
def getTemp():
    global rxBuff
    tx_buff = [0xA0,0x03,0x01,0x7b,0x00]
    checksum_ans =  CheckSum(tx_buff, 4)
    tx_buff[4] = checksum_ans
    #print("setWorkAntenna:" + str(ant) +">>"+ str(tx_buff)
    yatta_txData(tx_buff)
    #TODO: make below
    if(yatta_waitRxReader(0.5) == True):
        temp = rxBuff[5]
        rxBuff = []
        return temp
    else:
        #print("setWorkAntenna timeout
        return 0
    
def setWorkAntenna(ant):
    global rxBuff
    if(ant < 4):
        tx_buff = [0xA0,0x04,0x01,0x74,ant,0x00]
        checksum_ans =  CheckSum(tx_buff, 5)
        tx_buff[5] = checksum_ans
        #print("setWorkAntenna:" + str(ant) +">>"+ str(tx_buff))
        yatta_txData(tx_buff)
        #TODO: make below
        if(yatta_waitRxReader(0.5) == True):
            if(rxBuff[4] == COMMAND_SUCCESS):
                #print("setWorkAntenna " + str(ant) +" Success")
                rxBuff = []
                return True
            else:
                #print("setWorkAntenna " + str(ant) +" ErrorCode=" + rxBuff[4])
                rxBuff = []
                return False
        else:
            #print("setWorkAntenna " + str(ant) +" timeout")
            return False
    else:
        #print("setWorkAntenna wrong ant")
        return False
    
    
def get_inventory():
    global rxBuff
    global epc_tag
    global yatta_mode
    num = 0
    cmd = 0x89 #realtime_inventory_cmd
    tx_buff = [0xA0,0x04,0x01,cmd,0x01,0xD1]
    #print("$Start get_inventory yatta_mode="+str(yatta_mode))
    yatta_txData(tx_buff)
    #TODO: make below
    while(yatta_waitRxReader(0.5) == True):
        current_timestamp = arrow.utcnow().to('Asia/Bangkok').format('YYYY-MM-DD HH:mm:ss')
        if yatta_mode == 0:
            if(rxBuff[1]  == b'\x0a'):    #if(int(rxBuff[1], 16)  == 0x0A):
                #epc done with success
                antId = rxBuff[4]
                #readRate = str(int.from_bytes(rxBuff[6], byteorder='little'))+str(int.from_bytes(rxBuff[5], byteorder='little'))
                readRate = int.from_bytes(rxBuff[5], byteorder='little')
                readRate = int.from_bytes(rxBuff[6], byteorder='little')+readRate*16
                print(str(antId)+":get_inventory readRate = " + str(readRate))
                logger.info(str(antId)+":get_inventory readRate = " + str(readRate))
                #print(str(antId)+":get_inventory readRate= ")
                rxBuff = []
                return True
            elif(rxBuff[1]  == b'\x04'):    #(int(rxBuff[1], 16)  == 0x04):
                #don with error
                print('[' + current_timestamp + ']' + " get_inventory error="+ str(rxBuff[4]))
                logger.error("get_inventory error=> "+ beautify_log(str(rxBuff[4])))
                rxBuff = []
                return False
            else:
                #epc available
                epc_tag = rxBuff[7:7+EPC_LEN]
                push_epc_tag(time.time(), rxBuff[7:7+EPC_LEN])
                rxBuff = []
                num = num+1
                print('[' + current_timestamp + ']' + " get_inventory=>" + beautify_log(str(epc_tag))) #TODO:Push Q here
                logger.info(" get_inventory=>" + beautify_log(str(epc_tag)))
        else:
            if(rxBuff[1]  == b'\x13'):
                #epc available
                #epc_tag = rxBuff[7:7+EPC_LEN]
                push_epc_tag(time.time(), rxBuff[7:7+EPC_LEN])
                rxBuff = []
                print('[' + current_timestamp + ']' + " get_inventory total num= " + str(num))
                logger.info(" get_inventory total num= " + str(num))
                return True
            else:
                print("epc tag not found "+str(rxBuff))
                logger.error("epc tag not found "+str(rxBuff))
                # add logger.error
                return False

def beautify_log(log_message):
    # timestamp = arrow.utcnow().to('Asia/Bangkok').format('YYYY-MM-DD HH:mm:ss')
    log_message = log_message.replace("b'\\x", '').replace("'", '').replace(",", '').replace('[', '').replace(']', '')
    log_message = log_message.upper().replace(' ', '')
    return (log_message)




