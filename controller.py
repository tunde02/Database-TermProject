import pymysql
import folium
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread, QUrl
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

#비밀번호 문자열 검사 시 사용. 정규표현식
import re

# conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
# curs = conn.cursor()

class Signals(QObject):
    map_refreshed = pyqtSignal()
    board_added = pyqtSignal()
    recommends_updated = pyqtSignal()
    reply_added = pyqtSignal()

#쿼리를 DB에 날려 원하는 투플만 뽑아오는 것이 모든 투플을 뽑아 파이썬에서 탐색하는 것 보다 성능이 훨씬 좋다. (log(n) 과 n 타임 차이)
def loginSearch(id, pw):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "select * from user where user_id=%s and password=%s"
    curs.execute(sql, (id, pw))
    user_rows = curs.fetchone()

    if user_rows == None:
        conn.close()
        return {"result" : "fail", "data" : None}
    else:
        sql = "select nickname from userinfo where user_id=%s"
        curs.execute(sql, (user_rows[0]))
        userinfo_rows = curs.fetchone()

        conn.close()

        return {"result" : "success", "nickname" : userinfo_rows[0]}


def findIdSearch(email, nickname):

    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "select user_id from userinfo where email=%s and nickname=%s"

    curs.execute(sql, (email, nickname))
    userinfo_rows = curs.fetchone()

    conn.close()

    if userinfo_rows == None:
        return {"result": "fail", "data": None}
    else:
        return {"result": "success", "data": userinfo_rows[0]}

def findPwSearch(id, phone_number):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "select password, phone_number from phonenumber p, user u where p.user_id=u.user_id and p.user_id=%s"

    curs.execute(sql, id)
    phone_rows = curs.fetchall()

    conn.close()

    if phone_rows == None:
        return {"result": "fail", "data": None}
    else:
        for pn in phone_rows:
            if pn[1] == phone_number:
                return {"result": "success", "data": pn[0]}


#flag는 id 검사인지, nickname 검사인지를 구별하기 위해 사용됨
#flag == 0이면 id검사, 1이면 nickname 검사
def checkDuplication(userstr, flag):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    if flag == 0:
        sql = "select * from user where user_id=%s"
        curs.execute(sql, (userstr))
        userinfo_rows = curs.fetchone()

    else:
        sql = "select * from userinfo where nickname=%s"
        curs.execute(sql, (userstr))
        userinfo_rows = curs.fetchone()

    conn.close()

    if userinfo_rows == None:
        return True
    else:
        return False

#id, password, email, phone_number 유효한 형태인지 확인
# -1 : id 길이 오류
# -2 : pw 길이 오류
# -3 : pw 조합 오류
# -4 : email 형식 오류
# -5 : 전화번호 길이 오류
# -6 : 전화번호 형식 오류
def checkUserInfo(id, password, email, phone_number):
    #id확인
    if len(id) > 15 or len(id) == 0:
        return (False, -1)

    #password길이 확인
    if len(password) > 16 or len(password) == 0:
        return (False, -2)

    #password문자 + 숫자 조합인지 확인
    if not re.search(r'\d', password) or not re.search(r'\D', password):
        return (False, -3)

    #이메일 형식 확인
    if '@' not in email:
        return (False, -4)

    #전화번호 길이 확인
    if len(phone_number) != 11:
        return (False, -5)

    #전화번호 형식 확인
    if not re.search(r'\d', phone_number):
        return (False, -6)

    return (True, 0)

def signUp(user_id, password, nickname, name, email, phone_number):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "insert into user(user_id, password)" \
          "values(%s, %s)"

    curs.execute(sql, (user_id, password))

    sql = "insert into userinfo(user_id, nickname, name, email)" \
          "values(%s, %s, %s, %s)"

    curs.execute(sql, (user_id, nickname, name, email))

    sql = "insert into phonenumber(user_id, phone_number)" \
          "values(%s, %s)"

    curs.execute(sql, (user_id, phone_number))

    conn.commit()

    conn.close()

def signOut(user_id):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "delete from user where user_id=%s"

    curs.execute(sql, (user_id))

    conn.commit()

    conn.close()

def getLocation(signals):

    options = Options()
    # options.add_argument("start-maximized")
    # options.add_argument("--disable-infobars")
    # options.add_argument("--disable-extensions")
    # options.add_argument('--headless')

    options.add_argument("--use--fake-ui-for-media-stream")
    options.binary_location = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=options)  # Edit path of chromedriver accordingly
    timeout = 20
    driver.get("https://mycurrentlocation.net/")

    wait = WebDriverWait(driver, timeout)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    parsed = soup.find_all('td')

    driver.quit()

    map_osm = folium.Map(location=[parsed[0].text, parsed[1].text], zoom_start=17)
    folium.Marker([parsed[0].text, parsed[1].text]).add_to(map_osm)

    makeBoardPing(parsed, map_osm, signals)

    return {'latitude' : float(parsed[0].text), 'longitude' : float(parsed[1].text)}


def makeBoardPing(parsed, map_osm, signals):
    loc = {'latitude' : float(parsed[0].text), 'longitude' : float(parsed[1].text)}

    boardList = searchSurroundingBoards(loc)

    for item in boardList:
        icon = None
        if item[4] == "연애":
            icon = folium.Icon(color="pink", icon="star")
        elif item[4] == "고민":
            icon = folium.Icon(color="lightgray", icon="star")
        elif item[4] == "취미":
            icon = folium.Icon(color="lightgreen", icon="star")
        else:
            icon = folium.Icon(color="blue", icon="star")
        folium.Marker((item[-2], item[-1]), icon=icon).add_to(map_osm)

    map_osm.save("./map.html")

    signals.map_refreshed.emit()


def enrollBoard(user_id, title, contents, category, loc, signals):

    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "INSERT board (user_id, title, category, contents, recommends, longitude, latitude) " \
          "VALUE (%s, %s, %s, %s, %s, %s, %s)"

    curs.execute(sql, (user_id, title, category, contents, 0, loc["longitude"], loc["latitude"]))
    conn.commit()

    conn.close()

    signals.board_added.emit()


def searchSurroundingBoards(loc):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    # 정상게시물 추출
    sql = "SELECT b.board_id, b.title, u.nickname, b.recommends, b.category, b.latitude, b.longitude " \
          "FROM userinfo u, " \
               "(SELECT * " \
                "FROM board " \
                "WHERE (6371*acos(cos(radians(%s))*cos(radians(latitude))*cos(radians(longitude)-radians(%s))+sin(radians(%s))*sin(radians(latitude)))) <= %s " \
               ") b " \
          "WHERE b.user_id = u.user_id " \
          "ORDER BY b.board_id"

    default_distance = 15
    curs.execute(sql, (loc["latitude"], loc["longitude"], loc["latitude"], "15"))
    boardList = list(curs.fetchall())

    sql = "SELECT b.board_id, b.title, '알수없음' AS nickname, b.recommends, b.category, b.latitude, b.longitude " \
          "FROM (SELECT * " \
                "FROM board " \
                "WHERE (6371*acos(cos(radians(%s))*cos(radians(latitude))*cos(radians(longitude)-radians(%s))+sin(radians(%s))*sin(radians(latitude)))) <= %s " \
               ") b " \
          "WHERE b.user_id is NULL" \

    curs.execute(sql, (loc["latitude"], loc["longitude"], loc["latitude"], default_distance))
    boardList += list(curs.fetchall())

    conn.close()

    return boardList


def searchBoards(loc, searchKeyword, category, distance, searchType):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql1 = "SELECT b.board_id, b.title, u.nickname, b.recommends, b.category " \
          "FROM userinfo u, " \
               "(SELECT * " \
                "FROM board " \
                "WHERE (6371*acos(cos(radians(%s))*cos(radians(latitude))*cos(radians(longitude)-radians(%s))+sin(radians(%s))*sin(radians(latitude)))) <= %s" \
               ") b " \
          "WHERE b.user_id = u.user_id AND " \

    sql2 = "SELECT b.board_id, b.title, '알수없음' AS nickname, b.recommends, b.category " \
          "FROM (SELECT * " \
                "FROM board " \
                "WHERE (6371*acos(cos(radians(%s))*cos(radians(latitude))*cos(radians(longitude)-radians(%s))+sin(radians(%s))*sin(radians(latitude)))) <= %s " \
               ") b " \
          "WHERE b.user_id is NULL AND "

    categorized = False
    writer_type = False
    if category != "자유":
        sql1 += "b.category = %s AND "
        sql2 += "b.category = %s AND "
        categorized = True

    if searchType == "제목":
        sql1 += "b.title LIKE %s "
        sql2 += "b.title LIKE %s "
    elif searchType == "작성자":
        sql1 += "u.nickname LIKE %s "
        writer_type = True
    elif searchType == "내용":
        sql1 += "b.contents LIKE %s "
        sql2 += "b.contents LIKE %s "

    if categorized:
        curs.execute(sql1, (loc["latitude"], loc["longitude"], loc["latitude"], distance, category, ("%" + searchKeyword + "%")))
        boardList = list(curs.fetchall())
        if not writer_type:
            curs.execute(sql2, (loc["latitude"], loc["longitude"], loc["latitude"], distance, category, ("%" + searchKeyword + "%")))
            boardList += list(curs.fetchall())
    else:
        curs.execute(sql1, (loc["latitude"], loc["longitude"], loc["latitude"], distance, ("%" + searchKeyword + "%")))
        boardList = list(curs.fetchall())
        if not writer_type:
            curs.execute(sql2, (loc["latitude"], loc["longitude"], loc["latitude"], distance, ("%" + searchKeyword + "%")))
            boardList += list(curs.fetchall())

    conn.close()

    return boardList


def getBoardInfo(board_id):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "SELECT board_id, user_id, title, category, contents, recommends FROM board WHERE board_id = %s"
    curs.execute(sql, (board_id))
    boardInfos = list(curs.fetchone())
    user_id = boardInfos[1]

    if user_id == None:
        boardInfos[1] = "알수없음"
    else:
        sql = "SELECT nickname FROM userinfo WHERE user_id = %s"
        curs.execute(sql, (user_id))
        boardInfos[1] = curs.fetchone()[0]

    conn.close()

    return boardInfos


def getReplies(board_id):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "SELECT user_id, contents " \
          "FROM reply " \
          "WHERE board_id = %s " \
          "ORDER BY date ASC"

    curs.execute(sql, (board_id))
    replies = list(curs.fetchall())

    for i in range(len(replies)):
        id = replies[i][0]
        if id == None:
            pass
        else:
            sql = "SELECT nickname FROM userinfo WHERE user_id = %s"
            curs.execute(sql, (id))
            nickname = curs.fetchone()[0]
            newReply = (nickname, replies[i][1])
            replies[i] = newReply

    conn.close()

    return replies


def plusRecommendCount(board_id, signals):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "UPDATE board SET recommends = recommends + 1 WHERE board_id = %s"

    curs.execute(sql, (board_id))
    conn.commit()

    signals.recommends_updated.emit()

    conn.close()


def addReply(board_id, user_id, contents, signals):
    conn = pymysql.connect(host='localhost', user='supervisor', password='1234', db='db_teamproject')
    curs = conn.cursor()

    sql = "INSERT INTO reply (user_id, board_id, contents, date) " \
          "VALUE(%s, %s, %s, now())"
    curs.execute(sql, (user_id, board_id, contents))
    conn.commit()

    signals.reply_added.emit()

    conn.close()