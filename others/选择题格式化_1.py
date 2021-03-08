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

res = ""
all_list = []

for data in indata:
	data_temp = data
	if data_temp == "":
		continue
	try:
		num = data_temp.split("、")[0]
		num = int(num)
		all_list.append(res)
		res = data_temp
	except:
		res = res+data_temp

all_list.append(res)

all_list = my_function(all_list)

for li in all_list:
	fileout.write(li)
filein.close()
fileout.close()
