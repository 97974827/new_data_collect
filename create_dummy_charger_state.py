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

a = 30

conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD, charset='utf8mb4',
                               db=MYSQL_DB)

start = datetime.datetime.now()


for i in range(1, 16):

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

    curs = conn.cursor(pymysql.cursors.Cursor)
    query = "SELECT `card_num` FROM dummy_card AS dc WHERE dc.`no`= %s "
    curs.execute(query, a)
    res = curs.fetchone()

    # charger_dummy
    query = "INSERT INTO gl_charger_state(`device_no`, `kind`, `exhaust_money`, `charger_type`, `sales_type`, `current_money`, `current_bonus`, `current_charge`, `total_money`, `card_num`, `input_date`) VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    curs.execute(query, ('9', '1', '0000', '0', '0', '0100', '0010', '00110', '00210', res[0], s_start))

    conn.commit()

conn.close()
