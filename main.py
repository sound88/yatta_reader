import time
import threading
import requests
#import yatta_cfg
import yatta_lib
import os


mainTimeoutFlag = False
def mainTimeout_handler():
    global mainTimeoutFlag
    mainTimeoutFlag = True
    
def mainTimeout_start(timeout_sec):
    global mainTimeoutFlag
    mainTimeoutFlag = False
    threading.Timer(timeout_sec, mainTimeout_handler).start()
    
SIM_READDER = 0 #setup VH-xx to UART Tx pin(Board) 8 Rx pin(Board) 10
#SIM_READDER = 1  #Sim rfid reader


#yatta_cfg
global sn
global host_url
global logDirectory


#yatta_lib
global EPC_LEN
global epc_tag


index_datalog = 0


#yatta_cfg.init()
#----------ethernet_serial_number-----------#
sn = "b8:27:eb:80:28:b4" #open("/sys/class/net/eth0/address").read()

#sn = open("/sys/class/net/eth0/address").read()
#----------host_url-----------#
#host_url = "http://chaichana.org/yatta/"
#host_url = "http://intaniarunner.com/icmm2017/rubbibYatta.php"
#host_url = "http://intaniarunner.com/icmm2017/raceYattaServer.php"
host_url = "http://intaniarunner.com/icmm2017/raceYattaServer.php" 


#----------log_directory-----------#
logDirectory = '/home/pi/samyan/yatta_log/'


print "---------------yatta_cfg Init--------------"
print sn
print host_url
print logDirectory


yatta_lib.init(SIM_READDER)






#A0 04 01 89 01 D1 -------->Tx
#A0 13 01 89 8C 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 37 BB <-------Rx
#A0 13 01 89 74 30 00 E2 00 40 74 85 0A 01 03 16 30 70 E1 36 29 <-------Rx
#A0 13 01 89 D4 30 00 30 08 33 B2 DD D9 01 40 00 00 00 01 36 74 <-------Rx
#A0 13 01 89 D4 30 00 E2 00 40 74 85 0A ., foo, 2)
#buf[i:i+2] = foo






print "--------Start Inventory YATTA!!!"
antId = 0
antEnabled = [True, True, True, True]
antInit = [False, False, False, False]
yatta_st = 0
scaning_time_sec = 2 #30
sendingCnt = 0
try:
    #Scan EPC
    while True:
        if(yatta_st == 0):  #set timer
            print "setTimer"
            mainTimeout_start(scaning_time_sec)
            yatta_st = 1
            print "Scaning start " + str(scaning_time_sec) +" sec"
            
        elif(yatta_st == 1):  #set scan
            if(antEnabled[antId] == True):
                yatta_lib.setWorkAntenna(antId)
                if(yatta_lib.get_inventory() == False):
                    antEnabled[antId] = False
                    print str(antId) + " False"
                else:
                    if(antInit[antId] == False):
                        antInit[antId] = True;
                        print str(antId) + " init success"    
##            antId++
            if(mainTimeoutFlag):
                yatta_st = 2
                print "Sending data " + str(yatta_lib.numQHTTP())+ " ..."
        elif (yatta_st == 2):   #
            if not (yatta_lib.qHttp_Empty()):
                #------------ Local data log part --------------
                tmpHTTPYatta = yatta_lib.getQHttp()
                if (0):
                    print "httpThread>> peekQHttp=" + tmpHTTPYatta
                    yatta_lib.getQHttp()
                else: #Below using send http
                    server_url = host_url + "?sn=" + sn + "&tag_id=" + tmpHTTPYatta
                    #print "httpThread>> http request=" + server_url
                    try:
                        r = requests.get(server_url)
                        if(r.status_code == 200):
                            sendingCnt = sendingCnt+1
                            #print "httpThread>> return ="+str(r.status_code)
                            #yatta_lib.getQHttp()
                    except:
                        print "network fail"
                        
#End sending
                #print "\t:NumLog= " + str(yatta_lib.numQHTTP())
                    
            if not (yatta_lib.qLog_Empty()):
                #------------ Local data log part --------------
                timestamp = time.time
                if not os.path.exists(logDirectory):
                    os.makedirs(logDirectory)
                # Filename is "dataLog_ts.txt"
                Filename = "dataLog_" + str(time.strftime("%Y%m%d" , time.localtime() ) ) +'.txt'
                f = open(logDirectory + Filename, 'a')     # open(filename, mode).
                #datalog_str = str(index_datalog) + ' ' +  str(timestamp)  + ' ' + str(tagid_str) + '\r\n' # Format data 1. timeStamp(UTC) epc_tag
                datalog_str = yatta_lib.getQLog()
                f.write(datalog_str) 
                #print "logThread>>" + datalog_str
                f.close()
                
            if (yatta_lib.qHttp_Empty() and yatta_lib.qLog_Empty()):
                yatta_st = 0
                print "Data flushed " + str(sendingCnt)
                sendingCnt = 0
            
   
        
        #antId=(antId+1)%4
        
##        if(antId == 0):
##            temp = yatta_lib.getTemp();
##            print "Temp= " + str(temp)+" degC" + " NumLog= " + str(yatta_lib.numQHTTP())
            
            
##        if not (yatta_lib.qHttp_Empty()):
##            #------------ Local data log part --------------
##            tmpHTTPYatta = yatta_lib.peekQHttp()
##            print "httpThread>> peekQHttp=" + tmpHTTPYatta
##            server_url = host_url + "?sn=" + sn + "&tag_id=" + tmpHTTPYatta
##            print "httpThread>> http request=" + server_url
##            try:
##                r = requests.get(server_url)
##                #print "httpThread>> return ="+str(r.status_code)
##                #if(r.status_code == 200):
##                yatta_lib.getQHttp()
##            except:
##                print "network fail"
##                
##            #print "\t:NumLog= " + str(yatta_lib.numQHTTP())
##                
##        if not (yatta_lib.qLog_Empty()):
##            #------------ Local data log part --------------
##            index_datalog = index_datalog  + 1
##            timestamp = time.time
##            if not os.path.exists(logDirectory):
##                os.makedirs(logDirectory)
##            # Filename is "dataLog_ts.txt"
##            Filename = "dataLog_" + str(time.strftime("%Y%m%d" , time.localtime() ) ) +'.txt'
##            f = open(logDirectory + Filename, 'a')     # open(filename, mode).
##            #datalog_str = str(index_datalog) + ' ' +  str(timestamp)  + ' ' + str(tagid_str) + '\r\n' # Format data 1. timeStamp(UTC) epc_tag
##            datalog_str = yatta_lib.getQLog()
##            f.write(datalog_str) 
##            #print "logThread>>" + datalog_str
##            f.close()
except KeyboardInterrupt: # press Ctrl + c
    print "Exit program press F5 to run again"
        
    



