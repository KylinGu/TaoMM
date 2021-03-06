#!/usr/bin/env python
# -*- coding: <utf-8> -*-


from urllib import request, parse, error
import json
import re
import os
import random
import csv
from bs4 import BeautifulSoup

URL_PAGE = r'https://mm.taobao.com/tstar/search/tstar_model.do?_input_charset=utf-8'

useragent_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    ]

def get_user(writer):
    req = request.Request(URL_PAGE)

    for n in range(1, 166):
        req.add_header('User-Agent', random.choice(useragent_list))
        with request.urlopen(req, data=('q&viewFlag=A&sortType=default&searchStyle=&searchRegion=city%3A&searchFansNum=&currentPage='+ str(n) + '&pageSize=100Name').encode('utf-8')) as f:
            print('status', f.status, f.reason)
            # for k, v in f.getheaders():
            #     print('%s: %s' % (k, v))

            # print('data: ', f.read().decode('gbk'))
            info = json.loads(f.read().decode('gbk'))

            # print(info['data']['searchDOList'])
            for user in info['data']['searchDOList']:
                print('%s: %s, %s, %s, %d, %s' % (user['realName'], user['city'], str(user['height']),
                                                str(user['weight']), user['totalFavorNum'], str(user['userId'])))

                # save useful info into csv
                save2csv(user['realName'], user['city'], str(user['height']), str(user['weight']),
                          user['totalFavorNum'], get_order_num(str(user['userId'])), str(user['userId']))
                # 爬取照片
                # get_albums(str(user['userId']))


URL_USER = 'https://mm.taobao.com/self/album/open_album_list.htm?_charset=utf-8&user_id%20='


def get_albums(uid):
    req = request.Request(URL_USER+uid)
    req.add_header('User-Agent', random.choice(useragent_list))
    with request.urlopen(req) as f:
        print('get albums status: ', f.status, f.reason)
        info = f.read().decode('gbk')

        reg = r'a class="mm-first" href="//.*?"'
        albums = re.findall(reg, info)
        for line in albums[::2]:
            album_id = re.split('&album_id=', line)[1].split('&')[0]
            get_photo_list(uid, album_id)


URL_PHOTOS = 'https://mm.taobao.com/album/json/get_album_photo_list.htm'
# ?user_id=176817195&album_id=10000962815


def get_photo_list(user_id, album_id):
    params = {'user_id': user_id, 'album_id': album_id}
    data = parse.urlencode(params)
    url = URL_PHOTOS + '?' + data
    req = request.Request(url)
    req.add_header('User-Agent', random.choice(useragent_list))

    with request.urlopen(req) as f:
        print('get photo list: status ', f.status, f.reason)
        info = f.read().decode('gbk')
        info_json= json.loads(info)
        # print(info_json['picList'])
        index = 0
        for img in info_json['picList']:
            imgUrl = 'http:' + re.split('_\d{1,3}x\d{3,5}', img['picUrl'])[0]
            save_photo(user_id, album_id, index, imgUrl)
            index = index + 1


def save_photo(user_id, album_id, index, picUrl):
    d = os.path.dirname('./tmm/'+user_id+'/')
    if not os.path.exists(d):
        os.mkdir(d)
    try:

        img_type = picUrl.split('.')[-1]
        file = os.path.join(d, str(album_id) + '_' + str(index) + '.' + img_type)

        if not os.path.exists(file):
            with request.urlopen(picUrl) as f:
                img = f.read()
                with open(file, 'wb') as f:
                    f.write(img)
    except error.HTTPError as e:
        print(e)


URL_PERSONAL = 'https://mm.taobao.com/self/aiShow.htm?&userId='


def get_order_num(user_id):
    with request.urlopen(URL_PERSONAL+user_id) as res:
        print('get order num status:', res.status, res.reason)
        if res.status == 200:
            html = res.read().decode('gbk')
            bshtml = BeautifulSoup(html, 'lxml')
            result = bshtml.find_all('a', target='_blank',
                                     href='//mm.taobao.com/self/model_card.htm?user_id=' + user_id + '&sub_tab=LI_2')

            return result[0].string if len(result) > 0 else 0
    return 0


def save2csv(name, city, height, weight, favors, orders, user_id):
    writer.writerow([name, city, height, weight, favors, orders, user_id])


def init_csv():
    mcsv_file = open('./tmm/tmm.csv', 'w', newline='')  # Adding newline will not produce a empty line.
    mwriter = csv.writer(mcsv_file)
    file_header = ['name', 'city', 'height', 'weight', 'favors', 'orders', 'userId']  # 本来想把img路径存入进去的, 'imgs'，想想还是算了。
    mwriter.writerow(file_header)
    return mwriter, mcsv_file

writer, csv_file = init_csv()
get_user(writer)
# 关闭csv writer
csv_file.close()


