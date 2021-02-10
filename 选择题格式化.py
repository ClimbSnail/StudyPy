import re
import codecs
from xpinyin import Pinyin

def my_function(lis):  # 输入一个名字的列表
	pin = Pinyin()
	tmp = []
	for item in lis:
		if item.strip() == "" or item.strip() == None:
			continue
		head = item.split('、')[1][:2]
		tmp.append((pin.get_pinyin(head), item))
	tmp.sort()

	result = []
	for res in tmp:
		result.append(res[1])
	return result

filein = codecs.open("./src.txt","r","utf-8")
fileout = codecs.open("./dst.txt","a","utf-8")

indata = filein.readlines()

lis = [ "" for pos in range(5)] 
cnt = 0
all_list = []

for data in indata:
	data_temp = data.strip()
	if data_temp == "":
		continue
	try:
		num = int(data_temp)
		res = lis[0] + "\r\n"
		str_cnt = lis[1]+" "+lis[2]+" "+lis[3]+" "+lis[4]
		if len(str_cnt) <= 45:
			res = res + str_cnt + "\r\n"
		else:
			res = res + lis[1] + " "+lis[2] + "\r\n"
			res = res + lis[3] + " "+lis[4] + "\r\n"
		all_list.append(res)
		lis = [ "" for pos in range(5)] 
		cnt = 0
		lis[cnt] = str(num)+"、"
	except:
		if len(data_temp) == 1:
			lis[cnt] = data_temp+"."
		else:
			lis[cnt] += data_temp
			cnt += 1

res = lis[0] + "\r\n"
str_cnt = lis[1] + " " + lis[2] + " " + lis[3] + " " + lis[4]
if len(str_cnt) <= 45:
	res = res + str_cnt + "\r\n"
else:
	res = res + lis[1] + " " + lis[2] + "\r\n"
	res = res + lis[3] + " " + lis[4] + "\r\n"
all_list.append(res)

all_list = my_function(all_list)

for li in all_list:
	fileout.write(li)
filein.close()
fileout.close()
