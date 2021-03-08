# 查找缺失的文件编号

import os
import re

# prefix_str = input("请输入文件公有的前缀：")
max_num = input("请输入最大的编号：").strip()
num_len = len(max_num)

re_str = "\d"*num_len
re_obj = re.compile(r'\d+')

max_num = int(max_num)

flag = [ 0 for pos in range(max_num) ]

path = "./" #文件夹目录

filelist= os.listdir(path) #得到文件夹下的所有文件名称

cnt = 0

for filestr in filelist:
    filename = filestr.split(".")[0]
    lis = re_obj.findall(filename)
    if lis != []:
        flag[ int(re_obj.findall(filename)[0].strip())-1 ] = 1

print("\n\n缺少的编号为")
for pos in range(max_num):
    if flag[pos] == 0:
        if cnt%5 == 0:
            print()
        cnt += 1
        print(pos+1, end="\t")
print("\n\n合计缺失 %d 项文件"%cnt)

input("\n\n回车关闭窗口！！！")
