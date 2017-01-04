#Cyclic Redundancy Check (CRC) computation includes all data from Len. A reference CRC computation program is presented as follow:
def CheckSum(uBuff, uBuffLen):
	i = 0
	uSum=0
	for i in range (0,uBuffLen):
	    uSum = uSum + uBuff[i]
	
	uSum = (~uSum) + 1
	return uSum%256

uBuff = [0xA0 , 0x04 , 0x01 , 0x74 , 0x00]
checksum_ans =  CheckSum(uBuff, 5)
print format(checksum_ans,'#04X')
