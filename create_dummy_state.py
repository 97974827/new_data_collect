import pymysql
import random
import datetime


MYSQL_HOST = "192.168.0.222"
MYSQL_USER = "pi"
MYSQL_PWD = "1234"
MYSQL_DB = "db_datacollect"

random.random()

self_time = 0
self_cash = 0
self_card = 0
remain_card = 0

a = 0

conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD, charset='utf8mb4',
                               db=MYSQL_DB)

start = datetime.datetime.now()


for i in range(1, 51):

    self_time += 60
    self_cash += 10
    self_card += 10
    remain_card += 10

    res = 0
    a = a + 1
    time = str(self_time).rjust(4, '0')
    cash = str(self_cash).rjust(4, '0')
    card = str(self_card).rjust(4, '0')
    recard = str(remain_card).rjust(5, '0')

    start = start + datetime.timedelta(seconds=self_time)
    end = start+datetime.timedelta(seconds=self_time)

    temp_start = str(start)
    temp_end = str(end)

    s_start = temp_start[:19]
    s_end = temp_end[:19]

    print("시작 : " + s_start + "   종료 : " + s_end)

    curs = conn.cursor(pymysql.cursors.Cursor)
    query = "SELECT `card_num` FROM dummy_card AS dc WHERE dc.`no`= %s "
    curs.execute(query, a)
    res = curs.fetchone()

    # self_self_dummy
    # query = "INSERT INTO gl_self_state(`device_addr`, `card_num`, `self_time`, `self_cash`, `self_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # self_under_dummy
    # query = "INSERT INTO gl_self_state(`device_addr`, `card_num`, `under_time`, `under_cash`, `under_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # self_foam_dummy
    # query = "INSERT INTO gl_self_state(`device_addr`, `card_num`, `foam_time`, `foam_cash`, `foam_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # self_coating_dummy
    # query = "INSERT INTO gl_self_state(`device_addr`, `card_num`, `coating_time`, `coating_cash`, `coating_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # air_dummy
    # query = "INSERT INTO gl_air_state(`device_addr`, `card_num`, `air_time`, `air_cash`, `air_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # mate_dummy
    # query = "INSERT INTO gl_mate_state(`device_addr`, `card_num`, `mate_time`, `mate_cash`, `mate_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    # curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    # reader_dummy
    query = "INSERT INTO gl_reader_state(`device_addr`, `card_num`, `reader_time`, `reader_cash`, `reader_card`,`remain_card`, `start_time`, `end_time`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
    curs.execute(query, ("02", res[0], time, cash, card, recard, s_start, s_end))

    conn.commit()

conn.close()
