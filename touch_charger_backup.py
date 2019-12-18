import pymysql
import json

# 충전기 설정
class TouchCharger:

    # 데이터 수집 장치 접속 정보
    MYSQL_HOST = "192.168.0.222"
    MYSQL_USER = "pi"
    MYSQL_PWD = "1234"
    MYSQL_DB = "db_datacollect"

    # device_type_number
    SELF = 0
    AIR = 1
    MATE = 2
    RS_CHARGER = 3
    COIN = 4
    BILL = 5
    TOUCH = 6
    KIOSK = 7
    POS = 8
    READER = 9

    DEFAULT_BONUS = 2

    # 터치 충전기 접속 정보
    PI_MYSQL_USER = "pi"
    PI_MYSQL_PWD = "1234"
    PI_MYSQL_DB = "glstech"

    # 충전기 설정 ( POS -> DB -> TouchCharger)
    def set_touch_config(self, args):

        res = 1  # return 값

        # 데이터 추출
        device_addr = args['device_addr']
        shop_pw = args['shop_pw']
        card_price = args['card_price']
        card_min_price = args['card_min_price']
        bonus1 = args['bonus1']
        bonus2 = args['bonus2']
        bonus3 = args['bonus3']
        bonus4 = args['bonus4']
        bonus5 = args['bonus5']
        bonus6 = args['bonus6']
        bonus7 = args['bonus7']
        bonus8 = args['bonus8']
        bonus9 = args['bonus9']
        bonus10 = args['bonus10']
        auto_charge_enable = args['auto_charge_enable']
        auto_charge_price = args['auto_charge_price']
        rf_reader_type = args['rf_reader_type']
        shop_no = args['shop_no']
        name = args['name']

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=self.MYSQL_HOST, user=self.MYSQL_USER, password=self.MYSQL_PWD, charset='utf8mb4',
                               db=self.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # IP , Device_no 추출
                ip_query = "SELECT `no`, `ip` FROM gl_device_list WHERE `type` = %s AND `addr` = %s "
                curs.execute(ip_query, (self.TOUCH, device_addr))
                res_ip = curs.fetchall()
                device_no = res_ip[0]['no']
                ip = res_ip[0]['ip']

                # UPDATE gl_charger_config
                query = "UPDATE gl_charger_config SET `shop_pw` = %s, `card_price` = %s, " \
                        "`card_min_price` = %s, `auto_charge_enable` = %s, `auto_charge_price` = %s, " \
                        "`rf_reader_type` = %s, `shop_no` = %s WHERE `device_no` = %s"
                curs.execute(query, (shop_pw, card_price, card_min_price, auto_charge_enable, auto_charge_price,
                                     rf_reader_type, shop_no, device_no))
                conn.commit()

                # UPDATE gl_charger_bonus
                bonus_query = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, " \
                              "`bonus4` = %s, `bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, " \
                              "`bonus9` = %s, `bonus10` = %s WHERE `no` = %s"
                curs.execute(bonus_query, (bonus1, bonus2, bonus3, bonus4, bonus5, bonus6, bonus7, bonus8,
                                           bonus9, bonus10, self.DEFAULT_BONUS))
                conn.commit()
        except Exception as e:
            print(e)
            res = 0
        finally:
            conn.close()

        # 터치 충전기 접속 설정
        pi_conn = pymysql.connect(host=ip, user=self.PI_MYSQL_USER, password=self.PI_MYSQL_PWD, charset='utf8mb4',
                                  db=self.PI_MYSQL_DB)
        pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)
        try:
            with pi_conn.cursor():
                ch_query = "UPDATE config SET `device_addr` = %s, `admin_password` = %s, `card_price` =%s, " \
                           "`min_card_price` = %s, `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, `bonus4` = %s," \
                           "`bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, `bonus9` = %s, " \
                           "`bonus10` = %s, `auto_charge_state` = %s, `auto_charge_price` = %s, " \
                           "`rf_reader_type` = %s, `id` = %s, `shop_name` = %s WHERE `no` = '1'"

                # 금액 자릿수 조정
                pi_card_price = int(card_price) * 100
                pi_card_min_price = int(card_min_price) * 100
                pi_bonus1 = int(bonus1) * 100
                pi_bonus2 = int(bonus2) * 100
                pi_bonus3 = int(bonus3) * 100
                pi_bonus4 = int(bonus4) * 100
                pi_bonus5 = int(bonus5) * 100
                pi_bonus6 = int(bonus6) * 100
                pi_bonus7 = int(bonus7) * 100
                pi_bonus8 = int(bonus8) * 100
                pi_bonus9 = int(bonus9) * 100
                pi_bonus10 = int(bonus10) * 100
                pi_auto_charge_price = int(auto_charge_price) * 100

                # Update config
                pi_curs.execute(ch_query, (device_addr, shop_pw, pi_card_price, pi_card_min_price, pi_bonus1,
                                           pi_bonus2, pi_bonus3, pi_bonus4, pi_bonus5, pi_bonus6, pi_bonus7, pi_bonus8,
                                           pi_bonus9, pi_bonus10, auto_charge_enable, pi_auto_charge_price,
                                           rf_reader_type, shop_no, name))
                pi_conn.commit()
        except Exception as e:
            print(e)
            res = 0
        finally:
            pi_conn.close()
        return res

    # 충전기 설정 ( TouchCharger -> DB _-> POS )
    def get_touch_config(self):
        # 데이터 수집 장치 DB
        conn = pymysql.connect(host=self.MYSQL_HOST, user=self.MYSQL_USER, password=self.MYSQL_PWD, charset='utf8mb4',
                               db=self.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # 데이터 수집 장치에서 터치 충전기 정보 가져오기
            with conn.cursor():
                # 터치 충전기 수량 파악
                c_query = "SELECT count(*) FROM gl_charger_config AS config " \
                          "INNER JOIN gl_device_list AS d_list " \
                          "ON config.`device_no` = d_list.`no` " \
                          "WHERE d_list.`type`= %s"
                curs.execute(c_query, self.TOUCH)
                device_count = curs.fetchone()
                count = device_count['count(*)'] + 1

                # 각 터치 충전기 설정 값 가져오기(From. 데이터수집장치)
                config = []  # 설정 값을 담을 배열
                query = "SELECT d_list.`addr`, `admin_pw`, `manager_pw`, `shop_pw`, `card_price`, `card_min_price`, " \
                        "`bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, `bonus6`, `bonus7`, `bonus8`, `bonus9`, " \
                        "`bonus10`,	`auto_charge_enable`, `auto_charge_price`, `rf_reader_type`, `shop_no`, `name`, " \
                        "`manager_key` " \
                        "FROM gl_charger_config AS config " \
                        "INNER JOIN gl_device_list AS d_list ON config.device_no = d_list.`no` " \
                        "INNER JOIN gl_charger_bonus AS bonus ON config.default_bonus_no = bonus.`no` " \
                        "INNER JOIN gl_shop_info AS shop ON config.shop_no = shop.`no` " \
                        "WHERE	d_list.type = %s " \
                        "ORDER BY d_list.`addr` ASC;"
                curs.execute(query, self.TOUCH)
                for i in range(1, count):
                    rows = curs.fetchone()
                    temp = []
                    j = 0
                    for row in rows.values():
                        j = j + 1
                        temp.insert(j-1, row)
                    config.insert(i-1, temp)

                # 터치 충전기 IP 주소 가져오기
                ip = []  # ip 주소를 담을 배열
                ch_config = []  # 각 충전기의 설정값을 담을 배열
                ip_query = "SELECT `ip` FROM gl_device_list AS d_list WHERE d_list.`type` = %s ORDER BY `addr` ASC"
                curs.execute(ip_query, self.TOUCH)

                # 터치 충전기 설정 값 가져오기
                for i in range(1, count):
                    ip_rows = curs.fetchone()
                    ip.insert(i-1, ip_rows)
                    pi_conn = pymysql.connect(host=ip[i-1]['ip'], user=self.PI_MYSQL_USER, password=self.PI_MYSQL_PWD,
                                              charset='utf8mb4', db=self.PI_MYSQL_DB)
                    pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)
                    try:
                        with pi_conn.cursor():
                            ch_query = "SELECT `device_addr` AS 'addr', `master_password` AS 'admin_pw', " \
                                       "`gil_password` AS 'manager_pw', `admin_password` AS 'shop_pw', `card_price`, " \
                                       "`min_card_price` AS 'card_min_price', `bonus1`, `bonus2`, `bonus3`, " \
                                       "`bonus4`, `bonus5`, `bonus6`, `bonus7`, `bonus8`, `bonus9`, `bonus10`, " \
                                       "`auto_charge_state` AS 'auto_charge_enable', `auto_charge_price`, " \
                                       "`rf_reader_type`, `id` AS 'shop_no', `shop_name` AS 'name', " \
                                       "`shop_id` AS 'manager_key' FROM config"
                            pi_curs.execute(ch_query)
                            ch_rows = pi_curs.fetchone()
                            k = 0
                            ch_temp = []
                            for row in ch_rows.values():
                                k = k + 1
                                # 금액 부분 자릿수 조정
                                if k == 5 or k == 6 or k == 7 or k == 8 or k == 9 or k == 10 or k == 11 or k == 12 \
                                        or k == 13 or k == 14 or k == 15 or k == 16 or k == 18:
                                    temp_row = int(int(row) / 100)
                                    row = str(temp_row).rjust(3, '0')
                                ch_temp.insert(k-1, row)
                            ch_config.insert(i-1, ch_temp)

                    finally:
                        pi_conn.close()

                conf_len = len(config[0]) + 1  # 배열 원소 개수

                # DB  - Charger 설정 값 비교
                diff = 0  # 설정 이상 확인 플래그
                diff_set = []  # 설정 이상 정보 저장 배열
                for i in range(1, count):
                    k = 0
                    for j in range(1, conf_len):
                        if config[i-1][j-1] != ch_config[i-1][j-1]:
                            diff = 1
                            k = k + 1
                            # addr
                            if j-1 == 0:
                                diff_set.insert(k-1, {"addr : ", ch_config[i-1][0], "db_addr : ", config[i-1][j-1],
                                                      "ch_addr : ", ch_config[i-1][j-1]})
                            # admin_pw
                            elif j-1 == 1:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_admin_pw : " + config[i-1][j-1],
                                                        "ch_admin_pw : " + ch_config[i - 1][j - 1]})
                            # manager_pw
                            elif j-1 == 2:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_manager_pw : " + config[i-1][j-1],
                                                        "ch_manager_pw : " + ch_config[i - 1][j - 1]})
                            # shop_pw
                            elif j-1 == 3:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_shop_pw : " + config[i-1][j-1],
                                                        "ch_shop_pw : " + ch_config[i - 1][j - 1]})
                            # card_price
                            elif j-1 == 4:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_card_price : " + config[i-1][j-1],
                                                        "ch_card_price : " + ch_config[i - 1][j - 1]})
                            # card_min_price
                            elif j-1 == 5:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_card_min_price : " + config[i-1][j-1],
                                                        "db_card_min_price : " + ch_config[i - 1][j - 1]})
                            # bonus1
                            elif j-1 == 6:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus1 : " + config[i-1][j-1],
                                                        "ch_bonus1 : " + ch_config[i - 1][j - 1]})
                            # bonus2
                            elif j-1 == 7:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus2 : " + config[i-1][j-1],
                                                        "ch_bonus2 : " + ch_config[i - 1][j - 1]})
                            # bonus3
                            elif j-1 == 8:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus3 : " + config[i-1][j-1],
                                                        "ch_bonus3 : " + ch_config[i - 1][j - 1]})
                            # bonus4
                            elif j-1 == 9:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus4 : " + config[i-1][j-1],
                                                        "ch_bonus4 : " + ch_config[i - 1][j - 1]})
                            # bonus5
                            elif j-1 == 10:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus5 : " + config[i-1][j-1],
                                                        "ch_bonus5 : " + ch_config[i - 1][j - 1]})
                            # bonus6
                            elif j-1 == 11:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus6 : " + config[i-1][j-1],
                                                        "ch_bonus6 : " + ch_config[i - 1][j - 1]})
                            # bonus7
                            elif j-1 == 12:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus7 : " + config[i-1][j-1],
                                                        "ch_bonus7 : " + ch_config[i - 1][j - 1]})
                            # bonus8
                            elif j-1 == 13:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus8 : " + config[i-1][j-1],
                                                        "ch_bonus8 : " + ch_config[i - 1][j - 1]})
                            # bonus9
                            elif j-1 == 14:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus9 : " + config[i-1][j-1],
                                                        "ch_bonus9 : " + ch_config[i - 1][j - 1]})
                            # bonus10
                            elif j-1 == 15:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_bonus10 : " + config[i-1][j-1],
                                                        "ch_bonus10 : " + ch_config[i - 1][j - 1]})
                            # auto_charge_enable
                            elif j-1 == 16:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_auto_charge_enable : " + config[i-1][j-1],
                                                        "ch_auto_charge_enable : " + ch_config[i - 1][j - 1]})
                            # auto_charge_price
                            elif j-1 == 17:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_auto_charge_price : " + config[i-1][j-1],
                                                        "ch_charge_price : " + ch_config[i - 1][j - 1]})
                            # rf_reader_type
                            elif j-1 == 18:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_rf_reader_type : " + config[i-1][j-1],
                                                        "ch_rf_reader_type : " + ch_config[i - 1][j - 1]})
                            # shop_no
                            elif j-1 == 19:
                                diff_set.insert(k - 1, {'addr\' : \'' + ch_config[i-1][0], 'db_shop_no\' :  \'' + config[i-1][j-1],
                                                        'ch_shop_no\' :  \'' + ch_config[i - 1][j - 1]})
                            # name
                            elif j-1 == 20:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_name : " + config[i-1][j-1],
                                                        "ch_name : " + ch_config[i - 1][j - 1]})
                            # manager_key
                            elif j-1 == 21:
                                diff_set.insert(k - 1, {"addr : " + ch_config[i-1][0], "db_manager_key : " + config[i-1][j-1],
                                                        "ch_manager_key : " + ch_config[i - 1][j - 1]})

                # 오류 발생 시 리턴
                if diff == 1:
                    print({'diff': diff_set})
                    return {'diif': diff_set}
                # 정상 리턴
                else:
                    res_q = "SELECT d_list.`addr`, `admin_pw`, `manager_pw`, `shop_pw`, `card_price`, " \
                            "`card_min_price`, `bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, `bonus6`, `bonus7`, " \
                            "`bonus8`, `bonus9`, `bonus10`,	`auto_charge_enable`, `auto_charge_price`, " \
                            "`rf_reader_type`, `shop_no`, `name`, `manager_key` " \
                            "FROM gl_charger_config AS config " \
                            "INNER JOIN gl_device_list AS d_list ON config.device_no = d_list.`no` " \
                            "INNER JOIN gl_charger_bonus AS bonus ON config.default_bonus_no = bonus.`no` " \
                            "INNER JOIN gl_shop_info AS shop ON config.shop_no = shop.`no` " \
                            "WHERE	d_list.type = %s " \
                            "ORDER BY d_list.`addr` ASC;"
                    curs.execute(res_q, self.TOUCH)
                    res = curs.fetchall()
                    return {'result': res}
        finally:
            conn.close()

# # 충전 기록 가져오기
# class TouchChargerThread:
#
#     # 데이터 수집 장치 접속 정보
#     MYSQL_HOST = "192.168.0.222"
#     MYSQL_USER = "pi"
#     MYSQL_PWD = "1234"
#     MYSQL_DB = "db_datacollect"
#
#     # device_type_number
#     SELF = 0
#     AIR = 1
#     MATE = 2
#     RS_CHARGER = 3
#     COIN = 4
#     MONEY = 5
#     TOUCH = 6
#     KIOSK = 7
#     POS = 8
#     READER = 9
#
#     DEFAULT_BONUS = 2
#
#     # 터치 충전기 접속 정보
#     PI_MYSQL_USER = "pi"
#     PI_MYSQL_PWD = "1234"
#     PI_MYSQL_DB = "glstech"
#
#     # 데이터 수집 장치 접속 설정
#     conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD, charset='utf8mb4', db=MYSQL_DB)
#     curs = conn.cursor(pymysql.cursors.DictCursor)
#
#     try:
#         with conn.cursor():
#             # IP , Device_no 추출
#             ip_query = "SELECT `no`, `ip` FROM gl_device_list WHERE `type` = %s AND `addr` = %s "
#             curs.execute(ip_query, (self.TOUCH, device_addr))
#             res_ip = curs.fetchall()
#             device_no = res_ip[0]['no']
#             ip = res_ip[0]['ip']
