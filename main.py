import requests
import time


ethernet_serial_number = open("/sys/class/net/eth0/address").read()

timestamp = str(time.time())
tagid = "2"

server_url = "http://chaichana.org/yatta/?sn=" + ethernet_serial_number + "&tag_id=" + tagid + "&dev_time=" + timestamp
print server_url 

r = requests.get(server_url)
print r.status_code
print r.headers
print r.text[0:1000]
