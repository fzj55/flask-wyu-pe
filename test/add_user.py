import requests
import xlrd as xlrd

txt=open('./data/名单.txt',encoding='utf-8')
excel_file = xlrd.open_workbook('./data/data.xls')  # 打开Excel文件
table = excel_file.sheets()[0]  # 通过索引打开
# print(table.cell(1,3).value)
for i in txt.readlines():
    data={}
    for j in range(1, table.nrows):
        s=i.split('\n')[0]
        if s==str(table.cell(j,2).value):
            data['name']=s
            data['password']=table.cell(j,5).value
            resp=requests.post('http://127.0.0.1:5000/private/user/add',data=data)
            if resp.status_code!=200:
                print(s)
                exit()
            else:
                break
    else:
        print(i)
        exit()
