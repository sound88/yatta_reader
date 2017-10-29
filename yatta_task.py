def vTask_yatta():
    while True:
        if(yatta_st== 0):  #set timer
            print "setTimer"
            mainTimeout_start(scaning_time_sec)
            yatta_st = 1
            print ("Scaning start " + str(scaning_time_sec) +" sec")
        
        elif(yatta_st == 1):  #set scan
            if(antEnabled[antId] == True):
                yatta_lib.setWorkAntenna(antId)
                if(yatta_lib.get_inventory() == False):
                    antEnabled[antId] = False
                    print str(antId) + " False"
                else:
                    if(antInit[antId] == False):
                        antInit[antId] = True;
                        print (str(antId) + " init success")
##            antId++
                    
                if(mainTimeoutFlag):
                    yatta_st = 2
                    print ("Sending data " + str(yatta_lib.numQHTTP())+ " ...")
            elif (yatta_st == 2):   #
                if not (yatta_lib.qHttp_Empty()):
                    #------------ Local data log part --------------
                    tmpHTTPYatta = yatta_lib.getQHttp()
                    if (0):
                        print ("httpThread>> peekQHttp=" + tmpHTTPYatta)
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
                            print ("network fail")

def vTask_report(threadName, q):
    while True:
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
            print ("Data flushed " + str(sendingCnt))
            sendingCnt = 0
        
