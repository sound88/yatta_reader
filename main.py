import threading
import requests
import time
import serial
import yatta_lib

EPC_LEN = 12
epc_tag = []

rxBuff = []


# setup UART Tx pin(Board) 8 Rx pin(Board) 10 
uart = serial.Serial('/dev/ttyS0',115200,timeout=1)
uart.close()
uart.open()


timeoutFlag = False
def timeout_handler():
    timeoutFlag = True
    
def timeout_start(timeout_sec):
    timeoutFlag = False
    threading.Timer(timeout_sec, timeout_handler).start()


def waitRxReader(timeout_ms):
    rx_idx = 0
    global rxBuff
    timeout_start(timeout_ms)
    while True:
        rxByte = uart.read(1)
        #print rx_idx
        #print rxByte.encode("hex")
        if(rx_idx == 0):
            if(rxByte.encode("hex") == "a0"):
                #print "Header detected"
                rxBuff.append(rxByte)
                rx_idx = rx_idx +1
        else:
            rxBuff.append(rxByte)
            rx_idx = rx_idx + 1
            if(rx_idx == int(rxBuff[1].encode("hex"), 16)+1):
                #chksum
                return True
        if(timeoutFlag == True):
            return False
            
        

#A0 04 01 89 01 D1
#A0 13 01 89 8C 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 37 BB
#A0 13 01 89 74 30 00 E2 00 40 74 85 0A 01 03 16 30 70 E1 36 29
#A0 13 01 89 D4 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 36 74 
#A0 13 01 89 D4 30 00 E2 00 40 74 85 0A 01 03 16 30 70 E1 35 CA
#A0 13 01 89 D4 30 00 E2 00 40 74 85 0A 01 03 16 90 67 DD 2F 7D
#A0 0A 01 89 00 00 11 00 00 00 05 B6

# like C's memcpy(buf+i, foo, 2)
#buf[i:i+2] = foo

def get_inventory():
    global rxBuff
    txBuf = [0xA0,0x04,0x01,0x89,0x01,0xD1]
    #print "get_inventory"
    uart.write(serial.to_bytes(txBuf))
    if(waitRxReader(2) == True):
        if(rxBuff[1].encode("hex")  > "0a"):
            #epc availabe
            epc_tag = rxBuff[7:7+EPC_LEN]
            print "epc_tag = " + epc_tag
            return True
        else:
            print "epc tag not found"
            return False
    else:
        print "waitRxReader timeout"
        return False

    
ethernet_serial_number = open("/sys/class/net/eth0/address").read()
#print "Start Inventory\n\r"
while True:
    if (get_inventory() == True):
        timestamp = str(time.time())
        tagid = epc_tag
        server_url = "http://chaichana.org/yatta/?sn=" + ethernet_serial_number + "&tag_id=" + tagid + "&dev_time=" + timestamp
        print server_url 
        r = requests.get(server_url)
        print r.status_code
        print r.headers
        print r.text[0:1000]
