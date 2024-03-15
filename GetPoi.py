from urllib.parse import quote
from urllib import request
import json
import os
import pandas as pd
import numpy as np

amap_web_key = ''# 高德api_key
poi_search_url = "http://restapi.amap.com/v3/place/text"
poi_boundary_url = "https://ditu.amap.com/detail/get/detail"


# 根据城市名称和分类关键字获取poi数据
def getpois(city, keywords):
    i = 1
    poi_list = pd.DataFrame(columns = ['x','y','name','id','pname','adcode','rating','heat','cost','time'])
    while True:  # 使用while循环不断分页获取数据
    
        result = getpoi_page(city, keywords, i)
        print(result)
        result = json.loads(result)  # 将字符串转换为json
        if result['count'] == '0':
            break
            # pass
        poi_list = pd.concat([poi_list, formatPoi(result)], axis=0,ignore_index=True)
        # print(poi_list)
        i = i + 1
    return poi_list


# 处理获取到的poi数据
def formatPoi(result):
    # 取出json数据中pois字段并拆分
    data = pd.json_normalize(result,record_path=['pois'])
    # 这里是需要的拆分出来的字段名
    columns_to_keep = ['location','name','id','pname','adcode','biz_ext.rating','biz_ext.cost']
    df = data[columns_to_keep]
    df.rename(columns={'biz_ext.cost': 'cost', 'biz_ext.rating': 'rating'}, inplace=True)
    # 处理可能出错的函数
    df['cost'] = df.cost.map(lambda x: x if x !=[] else 0)
    df['rating'] = df.rating.map(lambda x: x if x !=[] else 0)
    # 分割经纬度为x和y
    df[['x','y']]=df['location'].str.split(',',expand=True)
    new_order = ['x','y'] + [col for col in df.columns if col not in ('x','y')]
    df = df[new_order]
    df.drop('location', axis=1, inplace=True)
    # 新增haet列和time列，这两列的数据不好获取，使用的api没有提供，所以暂时用随机数。
    df['heat'] = np.random.randint(0,1000,df.shape[0])
    df.insert(loc=df.columns.get_loc('cost'), column='heat', value=df.pop('heat'))
    df['time'] = np.random.randint(0,24,df.shape[0])
    # poi_list = poi_list.append(df,ignore_index=True)
    # poi_list.loc[len(poi_list)] = df
    return df 

def write_to_csv(poilist, cityname, city_id):
    # 判断当前是否已经创建了对应文件夹，如果已经创建则跳过，未创建则新建
    if os.path.isdir('pois\\'+city_id):
        pass
    else:
        os.makedirs('pois\\'+city_id)
    # 将爬下来的数据以csv格式存储
    poilist.to_csv('pois\\'+city_id+'\\'+city_id+'.csv',mode='a',encoding='utf8',header=False, index=False)
    print("写入csv文件成功")


def write_poiname_to_txt(cityname, city_id):
    with open('pois\\'+'list.txt', 'a+') as f:
        print(cityname)
        f.write(cityname+' '+city_id+'\n')
        print("写入城市列表文件成功")


# 单页获取pois
def getpoi_page(cityname, keywords, page):
    req_url = poi_search_url + "?key=" + amap_web_key + '&extensions=all&keywords=' + quote(
        keywords) + '&city=' + quote(cityname) + '&citylimit=true&children=1' + '&offset=25' + '&page=' + str(
        page) + '&output=json'
    data = str()
    # print(req_url)
    with request.urlopen(req_url) as f:
        data = f.read()
        data = data.decode('utf-8')
    return data

# 获取城市list
def getcity_list():
    city_list = []
    with open('pois/list.txt','r') as f:
        line = f.readline()
        while line:
            city_list.append(line.strip().split('\t'))
            line = f.readline()
    return city_list

if __name__ == '__main__':
    classes = '风景名胜'
    # 添加城市方法：向poi/list.txt中加入城市及其代码，具体参考 https://lbs.amap.com/api/webservice/guide/api/search
    city_list = getcity_list()
    for i in city_list:
        pois_area = getpois(i[0], classes)
        write_to_csv(pois_area, i[0], i[1])
        print("写入csv文件成功")
