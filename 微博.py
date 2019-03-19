import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pymysql.cursors


def crawlDetailPage(url, page, i):
    # 读取微博网页的JSON信息
    req = requests.get(url)
    jsondata = req.text
    data = json.loads(jsondata)

    # 评论数
    # print(data)
    # for i,value in data["data"].items():
    #     print(type(i),i,value)

    commentCounts = data["data"]['total_number']
    print("第{}页第{}条微博的评论数为{}".format(page, i + 1, commentCounts))

    # 循环输出每一页的微博信息
    for i in data["data"]["data"]:
        print(i)
    for comment in data['data']["data"]:
        userId = comment['user']['id']
        userName = comment['user']['screen_name']
        commentTime = comment['created_at']
        commentText = comment['text']
        print()
        userProfileUrl = comment['user']['profile_url']

        print("用户{}创建于:{}".format(userName, commentTime))
        print("评论内容为:{}".format(commentText))
        print("用户详情链接为:{}".format(userProfileUrl))


        '''
        数据库操作
        '''

        # # 获取数据库链接
        # connection = pymysql.connect(host='localhost',
        #                              user='root',
        #                              password='123456',
        #                              db='weibo',
        #                              charset='utf8mb4')
        # try:
        #     # 获取会话指针
        #     with connection.cursor() as cursor:
        #         # 创建sql语句
        #         # sql = "insert into `comment` (`commentUrl`,`commentCounts`,`userId`,`userName`,`commentTime`,`commentText`,`userProfileUrl`) values (%s,%s,%s,%s,%s,%s,%s)"
        #         #
        #         # # 执行sql语句
        #         # cursor.execute(sql, (url, commentCounts, userId, userName, commentTime, commentText, userProfileUrl))
        #
        #         # 提交数据库
        #         connection.commit()
        # finally:
        #     connection.close()


def crawl(url, page):
    # 读取微博网页的JSON信息
    req = requests.get(url)
    jsondata = req.text
    data = json.loads(jsondata)

    print(data["data"]['cards'][5]['scheme'])
    # #获取每一页的数据
    content = data['data']["cards"]
    print(content[6]['scheme'])

    # 循环输出每一页微博的详情链接
    for i in range(2, 11):
        contentId = content[i]['mblog']['id']
        # contentUrl = "https://m.weibo.cn/status/" + contentId
        commentUrl = "https://m.weibo.cn/api/comments/show?id=" + str(contentId)
        # print("第{}条微博的详情链接为:{}".format(i+1,commentUrl))
        crawlDetailPage(commentUrl, page, i)
        t = random.randint(11, 13)
        print("休眠时间为:{}s".format(t))
        time.sleep(t)


for i in range(1, 2):
    print("正在获取第{}页微博数据:".format(i))
    # 知乎官方微博数据的JSON链接
    url = "https://m.weibo.cn/api/container/getIndex?uid=1939498534&type=uid&value=1939498534&containerid=1076031939498534&page=" + str(
        i)
    crawl(url, i)
    # 设置休眠时间
    time.sleep(60)
