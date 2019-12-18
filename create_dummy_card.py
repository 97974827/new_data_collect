import pymysql
import random


MYSQL_HOST = "192.168.0.222"
MYSQL_USER = "pi"
MYSQL_PWD = "1234"
MYSQL_DB = "db_datacollect"

random.random()

for i in range(1, 100):
    a = random.randrange(0, 255)
    b = random.randrange(0, 255)
    c = random.randrange(0, 255)
    d = random.randrange(0, 255)
    hex_a = format(a, '02x')
    hex_b = format(b, '02x')
    hex_c = format(c, '02x')
    hex_d = format(d, '02x')
    card_num = str(hex_a) + str(hex_b) + str(hex_c) + str(hex_d)

    print(card_num)

    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD, charset='utf8mb4',
                               db=MYSQL_DB)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    query = "INSERT INTO dummy_card(`card_num`) VALUE (%s)"

    curs.execute(query, card_num)

    conn.commit()

conn.close()

