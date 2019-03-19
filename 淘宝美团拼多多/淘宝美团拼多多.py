import configparser
import json
import re
import time

import pymysql
import requests
from lxml import etree

pc_user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'

iphone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'

taobao_headers = {
    'User-Agent': pc_user_agent

}

pinduoduo_headers = {
    'User-Agent': pc_user_agent
}

meituan_headers = {
    'Referer': 'http://h5.waimai.meituan.com/waimai/mindex/home',
    'User-Agent': iphone,
    'Content-Type': 'application/x-www-form-urlencoded'
}

gbk = 'gbk'
utf8 = 'utf-8'
unicode = 'unicode_escape'


class Query:

    def __init__(self) -> None:
        super().__init__()
        cf = configparser.ConfigParser()
        try:
            cf.read('db.ini')
            self.database = cf.get('config', 'database')
            self.host = cf.get('config', 'host')
            self.user = cf.get('config', 'user')
            self.password = cf.get('config', 'password')
            self.port = cf.get('config', 'port')
            if self.database == '' or self.host == '' or self.user == '' or self.password == '' or self.port == '':
                raise Exception("错误配置")
        except Exception as e:
            print('配置不存在')
            raise Exception(e)

    def connect(self):
        # 打开数据库连接
        try:
            return pymysql.connect(host=self.host, port=int(self.port), user=self.user, password=self.password,
                                   db=self.database)
        except Exception as e:
            save_log(e)
            raise Exception('无法连接数据库')

    def getParam(self, param_key, webtype, param_type):
        # 使用cursor()方法获取操作游标
        db = self.connect()
        cursor = None
        try:
            cursor = db.cursor()
            cursor.execute(
                "select param_value from params where param_key='%s' and webtype='%s' and param_type='%s'" % (
                    param_key, webtype, param_type))
            result = cursor.fetchall()
            if  result is not  None and len(result) > 0:
                return result[0][0]
            else:
                raise Exception("找不到参数名:%s,网站类型:%s，参数类型:%s的参数" % (param_key,webtype,param_type))
        except Exception as e:
            save_log(e)
            db.rollback()
        finally:
            if not cursor is None:
                cursor.close()
            db.close()

    def insert(self, sql_list):
        db = self.connect()
        # 使用cursor()方法获取操作游标
        cursor = db.cursor()
        try:
            for sql in sql_list:
                print('执行sql:%s' % sql)
                # 执行sql语句
                cursor.execute(sql)
                # 执行sql语句
                db.commit()
        except Exception as e:
            save_log(e)
            # 发生错误时回滚
            db.rollback()
        finally:
            # 关闭数据库连接
            cursor.close()
            db.close()


query = Query()

# 淘宝cookie
taobao_cookie_str = query.getParam('cookie', '淘宝', 'cookie')
# 美团外卖cookie
meituan_cookie_str = query.getParam('cookie', '美团', 'cookie')

# 经纬度
wm_latitude = query.getParam('wm_latitude', '美团', '表单参数')
wm_longitude = query.getParam('wm_longitude', '美团', '表单参数')


def parse_cookie(cookie_str):
    cookies = {}
    for cookie in cookie_str.split(';'):
        cookies[cookie.split('=')[0]] = cookie.split('=')[1]
    return cookies


def parse_yangkeduo_by_1():
    size = 100
    anti_content = '0alAfxn5HOtoY9EVWNX3Cvm4xPSCLKSS_kpxi_Z1Nfsav1GzgVmFvx-f-exkynHcFfYbukupxliZjOWo_ar90-G5oQWC_X9CQ9X2x5Yww0Wg2a04q3R8bhxCk0DFti76NV6xzo811IZpfeIGLOQzG5XK_2QeE9ua4XwzKEPzYNoVBfj1lOdHa_D34kauedEKo1FtFdnyzb4EwnsQVP9pF0tHmyYxR_vPnT0Kh1-bFcggg1fw7jpBuEXnF9e46z0OuuCB38tbOGI6K_SEcUS7rAmAqtv4BJLmwD-5oOrQmgtUmCbuHklS7uoIxCJmbCR54cek1kUBDCNhfZXII1EaoM09aEUATW8S8-AXOFdf4fKyGTUjrt88HxDa8rI3tf3Y7kGH6DKb4g5Rpc8usAeQA8WVgKfAyn4Xq3i56H-JJlUHeWvhiyWaJe-F9'
    response = requests.get(
        'http://apiv3.yangkeduo.com/operation/1282/groups?opt_type=1&size=%d&offset=0&flip=&anti_content=%s&list_id=1282_rec_list_index_qpumlz&pdduid=0&is_back=1' % (
            size, anti_content), headers=taobao_headers)
    if response.status_code == 200:
        json_data = json.loads(response.content.decode(response.apparent_encoding))
        key = 'goods_list'
        if key in json_data:
            for data in json_data[key]:
                # 商品详情页
                parse_yangkeduo_Detail(data['goods_id'])
    else:
        raise Exception('解析拼多多异常')
    print(response.content)


def parse_yangkeduo(keyword, page):
    anti_content = query.getParam('anti_content', '拼多多', '查询参数')
    url = 'http://apiv3.yangkeduo.com/search?page=%d&size=50&sort=default&requery=0&list_id=tNlvLMrbCA&q=%s&anti_content=%s&pdduid=0' % (
        page, keyword, anti_content)
    response = requests.get(url, headers=pinduoduo_headers)
    if response.status_code == 200:
        html = response.content.decode(utf8)
        data_json = json.loads(html)
        if 'items' in data_json:
            data_json = data_json['items']
            for data in data_json:
                goods_id = data['goods_id']
                parse_yangkeduo_Detail(goods_id)
    else:
        print(response.content.decode(utf8))
        raise Exception("更新anti_content参数")


# id：商品id
# size:评论条数
def parse_yangkeduo_Detail(id, pages=5):
    url = 'http://yangkeduo.com/goods.html?goods_id=%d' % id
    print('开始解析：%s' % url)
    response = requests.get(url, headers=pinduoduo_headers)
    if response.status_code == 200:
        html = response.content.decode(unicode)
        rawData = re.findall('rawData=.*', html)
        if len(rawData) > 0 and str(rawData[0][9:len(rawData[0]) - 1]).startswith('{') and str(
                rawData[0][9:len(rawData[0]) - 1]).endswith('}'):
            detail_data = json.loads(rawData[0][9:len(rawData[0]) - 1])
            if 'initDataObj' in detail_data and 'goods' in detail_data['initDataObj']:
                goods = detail_data['initDataObj']['goods']
                # 商品标题
                goodsName = "".join(goods['goodsName'].split())
                # 单独价格
                minNormalPrice = goods['minNormalPrice']
                # 拼单价格
                minGroupPrice = goods['minGroupPrice']
                # 拼单量
                sideSalesTip = goods['sideSalesTip']
                # 商品详情
                detail_str = ''
                for index in range(len(goods['goodsProperty'])):
                    detail_str += ';' + goods['goodsProperty'][index]['key'] + ';' + \
                                  goods['goodsProperty'][index]['values'][0]
                detail_str = detail_str[1:]
                print('商品标题:%s\n单独价格:%s\n拼单价格:%s\n拼单量:%s\n商品详情:%s' % (
                    goodsName, minNormalPrice, minGroupPrice, sideSalesTip, detail_str))
                sql_list = [
                    "insert into goods (goodsId,goodsName,minNormalPrice,minGroupPrice,sideSalesTip,goodsProperty) values(%d,'%s',%s,%s,'%s','%s')" % (
                        id, str(goodsName), minNormalPrice, minGroupPrice, re.findall('\d+', sideSalesTip)[0],
                        detail_str)]

                for page in range(1, pages):
                    response = requests.get(
                        'http://apiv3.yangkeduo.com/reviews/%d/list?page=%d&size=20&pdduid=0' % (id, page),
                        headers=taobao_headers)
                    if response.status_code == 200:
                        comment_data = json.loads(response.content.decode(response.apparent_encoding))
                        if 'data' in comment_data:
                            for comment in comment_data['data']:
                                print('评论时间:%s\n评论类容:%s\n' % (comment['time'], comment['comment']))
                                sql_list.append(
                                    "insert into comments (goodsId,comments,comment_time,type) values (%d,'%s','%s',1)" % (
                                        id, comment['comment'],
                                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment['time']))))
                    else:
                        raise Exception("解析拼多多评论异常")
                query.insert(sql_list)
    else:
        raise Exception('请更新拼多多cookie信息')


def parse_taobao(keyword):
    response = requests.get('https://s.taobao.com/search?q=%s' % keyword, headers=taobao_headers,
                            cookies=parse_cookie(taobao_cookie_str))
    if response.status_code == 200:
        html = response.content.decode(response.apparent_encoding)
        if len(re.findall('security-X5', html)) > 0:
            raise Exception("打开浏览器通过验证更新淘宝cookie信息")
        if len(re.findall("<title>\s+\w+", html)) > 0 and (re.findall("<title>\s+\w+", html)[0]).index('淘宝网') != -1:
            raise Exception("打开浏览器通过验证更新淘宝cookie信息")
        if len(re.findall('g_page_config.*', html)) > 0:
            str = re.findall('g_page_config.*', html)[0][16:len(re.findall('g_page_config.*', html)[0]) - 1]
            if str.startswith('{') and str.endswith('}'):
                json_data = json.loads(str)
                if 'mods' in json_data and 'itemlist' in json_data['mods'] and 'data' in json_data['mods'][
                    'itemlist'] and 'auctions' in json_data['mods']['itemlist']['data']:
                    json_data = json_data['mods']['itemlist']['data']['auctions']
                    for data in json_data:
                        parse_taobao_detail(data)
    else:
        print('解析淘宝商品列表信息异常')


def parse_taobao_detail(data, pages=5):
    url = 'https://detail.tmall.com/item.htm?id=%s' % data['nid']
    print('解析商品:%s\n详情链接:%s' % (data['raw_title'], url))
    response = requests.get(url, headers=taobao_headers, cookies=parse_cookie(taobao_cookie_str))
    if response.status_code == 200:
        try:
            html = response.content.decode(gbk)
        except:
            html = response.content.decode(unicode)
        html_tree = etree.HTML(html)

        detail_json = {'厂名': '', '厂址': '', '厂家联系方式': '', '品牌': '', '产地': '', '省份': '', '城市': '', '净含量': ''}
        if len(html_tree.xpath('//ul[@id="J_AttrUL"]/li')) > 0:
            li_tree = html_tree.xpath('//ul[@id="J_AttrUL"]/li')
            for key in detail_json:
                for index in range(len(li_tree)):
                    if key in li_tree[index].text:
                        if len(li_tree[index].text.split(':')) > 1:
                            detail_json[key] = li_tree[index].text.split(':')[1]
                        elif len(li_tree[index].text.split('：')) > 1:
                            detail_json[key] = li_tree[index].text.split('：')[1]
                        else:
                            detail_json[key] = li_tree[index].text
                        detail_json[key] = detail_json[key].replace('\xa0', '')
                        print('%s' % (detail_json[key]))
        print('商品名:%s\n价格:%s\n付款数:%s\n评论数:%s\n' % (
            data['raw_title'], data['view_price'], data['view_sales'], data['comment_count']))
        params = (data['nid'], data['raw_title'], data['view_price'], re.findall('\d+', data['view_sales'])[0],
                  data['comment_count']) + tuple(detail_json.values())
        sql_list = [
            "insert into taobao (id,goodsname,price,payment,comments,factory_name,factory_addr,phone,brand,origin,province,city,net_content) values (%s,'%s',%s,'%s',%s,'%s','%s','%s','%s','%s','%s','%s','%s')" % params]
        lastPage = 0
        for page in range(1, pages):
            url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=%s&sellerId=%s&order=3&currentPage=%s&append=0&content=1' % (
                data['nid'], data['user_id'], page)
            print('评论接口:%s' % url)
            response = requests.get(url, headers=taobao_headers, cookies=parse_cookie(taobao_cookie_str))
            if response.status_code == 200:
                comments = response.content.decode(utf8)
                comments = comments[comments.index('(') + 1:len(comments) - 1]
                if comments.startswith('{') and comments.endswith('}'):
                    comments = json.loads(comments)
                    if 'rateDetail' in comments and 'rateList' in comments['rateDetail']:
                        if lastPage == 0:
                            lastPage = comments['rateDetail']['paginator']['lastPage']
                        comments = comments['rateDetail']['rateList']
                        for comment in comments:
                            comment_time = comment['rateDate']
                            content = comment['rateContent']
                            print('评论时间:%s\n评论内容:%s' % (comment_time, content))
                            sql_list.append(
                                "insert into comments (goodsId, comments, comment_time, type) VALUES (%s,'%s','%s',2)" % (
                                    data['nid'], content, comment_time))
            else:
                raise Exception('解析评论异常')
            if page == lastPage:
                break
        query.insert(sql_list)
    else:
        print(response.status_code)
        raise Exception("解析:商品%s详情失败" % data['raw_title'])


def meituan():
    X_FOR_WITH = query.getParam('X_FOR_WITH', '美团', '查询参数')
    _Param = query.getParam('_', '美团', '查询参数')

    data = 'startIndex=0&sortId=&navigateType=910&firstCategoryId=910&secondCategoryId=910&multiFilterIds=&sliderSelectCode=&sliderSelectMin=&sliderSelectMax=&actualLat=23.099643&actualLng=113.313734&initialLat=23.096943&initialLng=113.329596&geoType=2&rankTraceId=&wm_latitude=%s&wm_longitude=%s&wm_actual_latitude=23099643&wm_actual_longitude=113313734&_token=' % (
        wm_latitude, wm_longitude)
    url = 'http://i.waimai.meituan.com/openh5/channel/kingkongshoplist?_=%s&X-FOR-WITH=%s' % (_Param, X_FOR_WITH)
    cookies = parse_cookie(meituan_cookie_str)
    response = requests.post(url, data=data, headers=meituan_headers, cookies=cookies)
    if response.status_code == 200:
        json_data = json.loads(response.content.decode(utf8))
        if 'data' in json_data and 'shopList' in json_data['data']:
            # print(json_data)
            json_data = json_data['data']['shopList']
            for shop in json_data:
                mtWmPoiId = shop['mtWmPoiId']
                shopName = shop['shopName']
                monthSalesTip = re.findall('\d+', shop['monthSalesTip'])[0]
                deliveryTimeTip = shop['deliveryTimeTip']
                minPriceTip = re.findall('\d+', shop['minPriceTip'])[0]
                shippingFeeTip = re.findall('\d+', shop['shippingFeeTip'])[0]
                distance = shop['distance']
                recommendReason = ''
                if 'recommendInfo' in shop and 'recommendReason' in shop['recommendInfo']:
                    recommendReason = shop['recommendInfo']['recommendReason']
                address = shop['address']
                shipping_time = shop['shipping_time']
                print(
                    'shopName:%s\nmonthSalesTip:%s\nminPriceTip:%s\nshippingFeeTip:%s\ndistance:%s\nrecommendReason:%s\naddresss:%s\nshipping_time:%s' % (
                        shopName, monthSalesTip, minPriceTip, shippingFeeTip, distance, recommendReason, address,
                        shipping_time))
                url = 'http://i.waimai.meituan.com/openh5/poi/food?_=%s&X-FOR-WITH=%s' % (_Param, X_FOR_WITH)
                form_data = 'geoType=2&mtWmPoiId=1060561747188861&dpShopId=-1&source=shoplist&skuId=&wm_latitude=0&wm_longitude=0&wm_actual_latitude=23099832&wm_actual_longitude=113312682&_token='
                response = requests.post(url, data=form_data, headers=meituan_headers, cookies=cookies)
                if response.status_code == 200:
                    json_data = json.loads(response.content.decode(utf8))
                    if 'data' in json_data and 'shopInfo' in json_data['data']:
                        shopInfo = json_data['data']['shopInfo']
                        deliveryFee = shopInfo['deliveryFee']
                        deliveryType = shopInfo['deliveryType']
                        deliveryTime = shopInfo['deliveryTime']
                        deliveryMsg = shopInfo['deliveryMsg']
                        minFee = shopInfo['minFee']
                        print('deliveryFee:%s\ndeliveryType:%s\ndeliveryTime:%s\ndeliveryMsg:%s\nminFee:%s' % (
                            deliveryFee, deliveryType, deliveryTime, deliveryMsg, minFee))
                        sql_list = [
                            "insert into shop_info(mtWmPoiId, shopName, monthSalesTip, deliveryTimeTip, minPriceTip, shippingFeeTip, distance, recommendReason, address, shipping_time,deliveryFee,deliveryType,deliveryTime,deliveryMsg,minFee) VALUES (%s,'%s',%s,'%s',%s,%s,'%s','%s','%s','%s',%s,%s,%s,'%s',%s)" % (
                                mtWmPoiId, shopName, monthSalesTip, deliveryTimeTip, minPriceTip, shippingFeeTip,
                                distance,
                                recommendReason, address, shipping_time, deliveryFee, deliveryType, deliveryTime,
                                deliveryMsg, minFee)]
                    else:
                        raise Exception('解析美团商品店铺详情异常')
                    if 'data' in json_data and 'categoryList' in json_data['data']:
                        categoryList = json_data['data']['categoryList']
                        food_list = {}
                        for category in categoryList:
                            food = {'categoryName': category['categoryName']}
                            categoryName = food['categoryName']
                            # print('categoryName:%s\n' % categoryName)
                            spuList = category['spuList']
                            for spu in spuList:
                                food['spuId'] = spu['spuId']
                                food['spuName'] = spu['spuName']
                                food['unit'] = spu['unit']
                                food['saleVolume'] = spu['saleVolume']
                                food['originPrice'] = spu['originPrice']
                                food['currentPrice'] = spu['currentPrice']
                                food['spuDesc'] = spu['spuDesc']
                                # print(
                                #     'spuName:%s\nunit:%s\nsaleVolume:%s\noriginPrice:%s\ncurrentPrice:%s\nspuDesc:%s' % (
                                #         spuName, unit, saleVolume, originPrice, currentPrice, spuDesc))
                                # sql_list.append(
                                #     "insert into food (spuId, categoryName, spuName, unit, saleVolume, originPrice, currentPrice, spuDesc) VALUES (%s,'%s','%s','%s',%s,%s,%s,'%s')" % (
                                #         spuId, categoryName, spuName, unit, saleVolume, originPrice, currentPrice,
                                #         spuDesc))
                                # if food['spuId'] in food_list:
                                #     food_list[]
                                if str(food['spuId']) in food_list:
                                    _food = food_list[str(food['spuId'])]
                                    _food['categoryName'] += ',' + categoryName
                                    food_list[str(food['spuId'])] = _food
                                else:
                                    food_list[str(food['spuId'])] = food
                        for food_data in food_list:
                            _data = food_list[food_data]
                            sql_list.append(
                                "insert into food (spuId, categoryName, spuName, unit, saleVolume, originPrice, currentPrice, spuDesc) VALUES (%s,'%s','%s','%s',%s,%s,%s,'%s')" % (
                                    _data['spuId'], _data['categoryName'], _data['spuName'],
                                    _data['unit'], _data['saleVolume'], _data['originPrice'],
                                    _data['currentPrice'],
                                    _data['spuDesc']))
                        query.insert(sql_list)
                    else:
                        raise Exception("解析美团店铺详情异常")
                else:
                    raise Exception("解析美团商品详情异常")
        else:
            raise Exception("解析美团店铺详情异常")
    else:
        print(response.content.decode(utf8))
        raise Exception("美团参数过期，需要更新")


def save_log(msg, type='数据库'):
    if not msg is str:
        msg = str(msg).replace('\'', "")
    print(msg)
    now = time.localtime(int(time.time()))
    datetime = time.strftime('%Y-%m-%d %H:%M:%S', now)
    query.insert(["insert into log (log_time, log_msg, log_type) VALUES ('%s','%s','%s')" % (datetime, msg, type)])


if __name__ == '__main__':
    meituan()
