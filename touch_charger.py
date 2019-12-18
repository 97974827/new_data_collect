import pymysql
import base64
import threading
import os
import gls_config
from datetime import datetime
from collections import OrderedDict


# TouchCharger 기능 목록
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
1. 충전기 설정                 # set_touch_config 
2. 충전기 설정 불러오기        # get_touch_config
3. 충전 기록 가져오기          # get_charger_state
4. 충전 기록(Total) 가져오기   # get_charger_total
5. 충전기 통신 상태 테스트     # get_connect
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class TouchCharger:

    # 터치 충전기 접속 정보
    PI_MYSQL_USER = "pi"
    PI_MYSQL_PWD = "1234"
    PI_MYSQL_DB = "glstech"

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    1. 충전기 설정 ( POS -> DB -> TouchCharger)
    포스로부터 데이터를 전송받아 저장형식에 맞게 데이터 파싱 후
    데이터 수집장치에 설정 값을 저장하고
    데이터 수집 장치에서 해당 터치 충전기의 IP를 구한 후
    터치 충전기에 접속하여 설정값을 업데이트 함
    * 보너스 설정은 기본 보너스 설정 값을 업데이트 함으로 다른 기기에 영향을 미침
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_touch_config(self, args):

        res = 1  # return 값

        # 데이터 추출
        device_addr = args['device_addr']                           # 터치 충전기 주소
        orgin_shop_pw = str(args['shop_pw'])                        # 암호화 전 비밀번호
        shop_pw = base64.b64encode(orgin_shop_pw.encode('utf-8'))   # 암호화 이후 비밀번호
        card_price = args['card_price']                             # 카드 가격
        card_min_price = args['card_min_price']                     # 카드 발급 진행 최소 금액
        bonus1 = args['bonus1']                                     # 보너스 1
        bonus2 = args['bonus2']                                     # 보너스 2
        bonus3 = args['bonus3']                                     # 보너스 3
        bonus4 = args['bonus4']                                     # 보너스 4
        bonus5 = args['bonus5']                                     # 보너스 5
        bonus6 = args['bonus6']                                     # 보너스 6
        bonus7 = args['bonus7']                                     # 보너스 7
        bonus8 = args['bonus8']                                     # 보너스 8
        bonus9 = args['bonus9']                                     # 보너스 9
        bonus10 = args['bonus10']                                   # 보너스 10
        auto_charge_enable = args['auto_charge_enable']             # 자동 충전 기능 사용 여부
        auto_charge_price = args['auto_charge_price']               # 자동 충전 금액
        rf_reader_type = args['rf_reader_type']                     # rf 리더기 타입 ( 터치 충전기의 경우 신형)
        shop_no = args['shop_no']                                   # 상점 번호( 카드에 입력되는 매장 ID)
        name = args['name']                                         # 세차장 상호명

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 데이터 수집 장치 정보 업데이트
        try:
            with conn.cursor():
                # IP , Device_no 추출
                ip_query = "SELECT `no`, `ip` FROM gl_device_list WHERE `type` = %s AND `addr` = %s "
                curs.execute(ip_query, (gls_config.TOUCH, device_addr))
                res_ip = curs.fetchall()
                device_no = res_ip[0]['no']
                ip = res_ip[0]['ip']

                # 금액 자릿수 조절
                db_bonus1 = str(int(int(bonus1) / 100)).rjust(3, '0')
                db_bonus2 = str(int(int(bonus2) / 100)).rjust(3, '0')
                db_bonus3 = str(int(int(bonus3) / 100)).rjust(3, '0')
                db_bonus4 = str(int(int(bonus4) / 100)).rjust(3, '0')
                db_bonus5 = str(int(int(bonus5) / 100)).rjust(3, '0')
                db_bonus6 = str(int(int(bonus6) / 100)).rjust(3, '0')
                db_bonus7 = str(int(int(bonus7) / 100)).rjust(3, '0')
                db_bonus8 = str(int(int(bonus8) / 100)).rjust(3, '0')
                db_bonus9 = str(int(int(bonus9) / 100)).rjust(3, '0')
                db_bonus10 = str(int(int(bonus10) / 100)).rjust(3, '0')
                db_card_price = str(int(int(card_price) / 100)).rjust(3, '0')
                db_card_min_price = str(int(int(card_min_price) / 100)).rjust(3, '0')
                db_auto_charge_price = str(int(int(auto_charge_price) / 100)).rjust(3, '0')

                # 터치 충전기 설정 업데이트
                query = "UPDATE gl_charger_config SET `shop_pw` = %s, `card_price` = %s, " \
                        "`card_min_price` = %s, `auto_charge_enable` = %s, `auto_charge_price` = %s, " \
                        "`rf_reader_type` = %s, `shop_no` = %s , `admin_pw` = %s, `manager_pw` = %s " \
                        "WHERE `device_no` = %s"
                curs.execute(query, (shop_pw, db_card_price, db_card_min_price, auto_charge_enable,
                                     db_auto_charge_price, rf_reader_type, shop_no, gls_config.ADMIN_PW,
                                     gls_config.MANAGER_PW, device_no))
                conn.commit()

                # 보너스 설정 값 업데이트
                bonus_query = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, " \
                              "`bonus4` = %s, `bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, " \
                              "`bonus9` = %s, `bonus10` = %s WHERE `no` = %s"
                curs.execute(bonus_query, (db_bonus1, db_bonus2, db_bonus3, db_bonus4, db_bonus5, db_bonus6,
                                           db_bonus7, db_bonus8, db_bonus9, db_bonus10, gls_config.DEFAULT_BONUS))
                conn.commit()
        except Exception as e:
            print("From touch_charger.py gl_charger_config / gl_charger_bonus Update except : ", e)
            res = 0  # 작업 실패 반환값
        finally:
            conn.close()

        # 터치 충전기 통신 테스트
        connect = self.get_connect(ip)

        if connect == 1:
            # 터치 충전기 접속 설정
            pi_conn = pymysql.connect(host=ip, user=self.PI_MYSQL_USER, password=self.PI_MYSQL_PWD,
                                      charset=gls_config.MYSQL_SET, db=self.PI_MYSQL_DB)
            pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

            # 터치 충전기 설정 업데이트
            try:
                with pi_conn.cursor():
                    ch_query = "UPDATE config SET `device_addr` = %s, `admin_password` = %s, `card_price` =%s, " \
                               "`min_card_price` = %s, `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, `bonus4` = %s," \
                               "`bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, `bonus9` = %s, " \
                               "`bonus10` = %s, `auto_charge_state` = %s, `auto_charge_price` = %s, " \
                               "`rf_reader_type` = %s, `id` = %s, `shop_name` = %s, `master_password` = %s, " \
                               "`gil_password` = %s " \
                               "WHERE `no` = '1'"

                    pi_curs.execute(ch_query, (device_addr, shop_pw, card_price, card_min_price, bonus1,
                                               bonus2, bonus3, bonus4, bonus5, bonus6, bonus7, bonus8,
                                               bonus9, bonus10, auto_charge_enable, auto_charge_price,
                                               rf_reader_type, shop_no, name, gls_config.ADMIN_PW,
                                               gls_config.MANAGER_PW))
                    pi_conn.commit()
            except Exception as e:
                print("From touch_charger.py touch_config Update except : ", e)
                res = 0  # 작업 실패 반환값
            finally:
                pi_conn.close()
        else:
            print("touch is not connected")
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    2. 충전기 설정 불러오기 (TouchCharger -> DB _-> POS )
    전체 터치 충전기의 설정을 불러오는 기능
    터치 충전기에 접속하여 설정 정보를 불러오고
    데이터 수집 장치에서 해당 터치 충전기와 설정을 비교한 후
    이상이 있으면 데이터 수집장치에 새로운 config를 insert한 후 
    설정값 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_touch_config(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():

                # 데이터 수집 장치에서 터치 충전기 정보 가져오기
                get_touch_qry = "SELECT `no`, `addr`, `ip` FROM gl_device_list WHERE `type` = %s"
                curs.execute(get_touch_qry, gls_config.TOUCH)
                get_touch_res = curs.fetchall()

                # 반환 리스트 생성
                touch_config_list = []

                # 암호 저장
                shop_pw = ''

                for get_touch in get_touch_res:

                    # 반환 딕셔너리 생성
                    touch_config = OrderedDict()
                    touch_config['device_addr'] = get_touch['addr']

                    # 설정 값 비교를 위한 임시 딕셔너리
                    temp_config = OrderedDict()
                    temp_config['device_addr'] = get_touch['addr']
                    # temp_config['device_no'] = get_touch['no']

                    # 설정 이상 값 저장 플래그
                    diff = '0'

                    # 터치 충전기 통신 상태 테스트
                    connect = self.get_connect(get_touch['ip'])

                    # 통신에 이상이 없을 경우
                    if connect == 1:
                        print("통신 이상 없음 접속 주소 : ", get_touch['ip'])
                        touch_config['state'] = '1'
                        # 터치 충전기 접속 설정
                        pi_conn = pymysql.connect(host=get_touch['ip'], user=self.PI_MYSQL_USER,
                                                  password=self.PI_MYSQL_PWD, charset=gls_config.MYSQL_SET,
                                                  db=self.PI_MYSQL_DB)
                        pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

                        # 터치충전기 설정 정보 추출
                        try:
                            with pi_conn.cursor():
                                get_config_qry = "SELECT `device_addr` AS 'addr', " \
                                                 "`master_password` AS 'admin_pw', " \
                                                 "`gil_password` AS 'manager_pw', `admin_password` AS 'shop_pw', " \
                                                 "`card_price`, `min_card_price` AS 'card_min_price', " \
                                                 "`bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, `bonus6`, " \
                                                 "`bonus7`, `bonus8`, `bonus9`, `bonus10`, " \
                                                 "`auto_charge_state` AS 'auto_charge_enable', `auto_charge_price`," \
                                                 " `rf_reader_type`, `id` AS 'shop_no', `shop_name` AS 'name', " \
                                                 "`shop_id` AS 'manager_key' FROM config"
                                pi_curs.execute(get_config_qry)
                                get_config_res = pi_curs.fetchall()

                                # 금액 자릿수 조절 및 딕셔너리 저장
                                for get_config in get_config_res:
                                    if get_config['shop_pw']:
                                        shop_pw = get_config['shop_pw']
                                        touch_config['shop_pw'] = base64.b64decode(str(get_config['shop_pw'])).decode('utf-8')
                                        temp_config['shop_pw'] = base64.b64decode(str(get_config['shop_pw'])).decode('utf-8')
                                    if get_config['card_price']:
                                        touch_config['card_price'] = get_config['card_price']
                                        temp_config['card_price'] = str(int(get_config['card_price']) // 100).rjust(3, '0')
                                    if get_config['card_min_price']:
                                        touch_config['card_min_price'] = get_config['card_min_price']
                                        temp_config['card_min_price'] = str(int(get_config['card_min_price']) // 100).rjust(3, '0')
                                    if get_config['bonus1']:
                                        touch_config['bonus1'] = get_config['bonus1']
                                        temp_config['bonus1'] = str(int(get_config['bonus1']) // 100).rjust(3, '0')
                                    if get_config['bonus2']:
                                        touch_config['bonus2'] = get_config['bonus2']
                                        temp_config['bonus2'] = str(int(get_config['bonus2']) // 100).rjust(3, '0')
                                    if get_config['bonus3']:
                                        touch_config['bonus3'] = get_config['bonus3']
                                        temp_config['bonus3'] = str(int(get_config['bonus3']) // 100).rjust(3, '0')
                                    if get_config['bonus4']:
                                        touch_config['bonus4'] = get_config['bonus4']
                                        temp_config['bonus4'] = str(int(get_config['bonus4']) // 100).rjust(3, '0')
                                    if get_config['bonus5']:
                                        touch_config['bonus5'] = get_config['bonus5']
                                        temp_config['bonus5'] = str(int(get_config['bonus5']) // 100).rjust(3, '0')
                                    if get_config['bonus6']:
                                        touch_config['bonus6'] = get_config['bonus6']
                                        temp_config['bonus6'] = str(int(get_config['bonus6']) // 100).rjust(3, '0')
                                    if get_config['bonus7']:
                                        touch_config['bonus7'] = get_config['bonus7']
                                        temp_config['bonus7'] = str(int(get_config['bonus7']) // 100).rjust(3, '0')
                                    if get_config['bonus8']:
                                        touch_config['bonus8'] = get_config['bonus8']
                                        temp_config['bonus8'] = str(int(get_config['bonus8']) // 100).rjust(3, '0')
                                    if get_config['bonus9']:
                                        touch_config['bonus9'] = get_config['bonus9']
                                        temp_config['bonus9'] = str(int(get_config['bonus9']) // 100).rjust(3, '0')
                                    if get_config['bonus10']:
                                        touch_config['bonus10'] = get_config['bonus10']
                                        temp_config['bonus10'] = str(int(get_config['bonus10']) // 100).rjust(3, '0')
                                    if get_config['auto_charge_enable']:
                                        touch_config['auto_charge_enable'] = get_config['auto_charge_enable']
                                        temp_config['auto_charge_enable'] = get_config['auto_charge_enable']
                                    if get_config['auto_charge_price']:
                                        touch_config['auto_charge_price'] = get_config['auto_charge_price']
                                        temp_config['auto_charge_price'] = str(int(get_config['auto_charge_price']) // 100).rjust(3, '0')
                                    if get_config['rf_reader_type']:
                                        touch_config['rf_reader_type'] = get_config['rf_reader_type']
                                        temp_config['rf_reader_type'] = get_config['rf_reader_type']
                                    if get_config['shop_no']:
                                        touch_config['shop_no'] = str(get_config['shop_no']).rjust(4, '0')
                                        temp_config['shop_no'] = str(get_config['shop_no']).rjust(4, '0')
                                    if get_config['name']:
                                        touch_config['name'] = get_config['name']
                                        temp_config['name'] = get_config['name']
                                    if get_config['manager_key']:
                                        touch_config['manager_key'] = get_config['manager_key']
                                        temp_config['manager_key'] = get_config['manager_key']
                                    # 반환 리스트 저장
                                    touch_config_list.append(touch_config)

                        # except Exception as e:
                        #     print("From get_touch_config for touch_device except : ", e)
                        finally:
                            pi_conn.close()

                        # 터치 충전기 설정 정보 추출(From. 데이터수집장치)
                        get_db_config_qry = "SELECT d_list.`addr` AS 'device_addr', `shop_pw`, `card_price`, " \
                                            "`card_min_price`, `bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, " \
                                            "`bonus6`, `bonus7`, `bonus8`, `bonus9`, `bonus10`, `default_bonus_no`," \
                                            "`auto_charge_enable`, `auto_charge_price`, `rf_reader_type`, " \
                                            "`shop_no`, `name`, `manager_key` " \
                                            "FROM gl_charger_config AS config " \
                                            "INNER JOIN gl_device_list AS d_list " \
                                            "ON config.device_no = d_list.`no` " \
                                            "INNER JOIN gl_charger_bonus AS bonus " \
                                            "ON config.default_bonus_no = bonus.`no` " \
                                            "INNER JOIN gl_shop_info AS shop " \
                                            "ON config.shop_no = shop.`no` " \
                                            "WHERE d_list.type = %s AND d_list.addr = %s " \
                                            "ORDER BY config.input_date DESC LIMIT 1"
                        curs.execute(get_db_config_qry, (gls_config.TOUCH, get_touch['addr']))
                        get_db_config_res = curs.fetchall()

                        for get_db_config in get_db_config_res:
                            db_config = OrderedDict()
                            if get_db_config['device_addr']:
                                db_config['device_addr'] = get_db_config['device_addr']
                            if get_db_config['shop_pw']:
                                db_config['shop_pw'] = base64.b64decode(str(get_db_config['shop_pw'])).decode('utf-8')
                            if get_db_config['card_price']:
                                db_config['card_price'] = get_db_config['card_price']
                            if get_db_config['card_min_price']:
                                db_config['card_min_price'] = get_db_config['card_min_price']
                            if get_db_config['bonus1']:
                                db_config['bonus1'] = get_db_config['bonus1']
                            if get_db_config['bonus2']:
                                db_config['bonus2'] = get_db_config['bonus2']
                            if get_db_config['bonus3']:
                                db_config['bonus3'] = get_db_config['bonus3']
                            if get_db_config['bonus4']:
                                db_config['bonus4'] = get_db_config['bonus4']
                            if get_db_config['bonus5']:
                                db_config['bonus5'] = get_db_config['bonus5']
                            if get_db_config['bonus6']:
                                db_config['bonus6'] = get_db_config['bonus6']
                            if get_db_config['bonus7']:
                                db_config['bonus7'] = get_db_config['bonus7']
                            if get_db_config['bonus8']:
                                db_config['bonus8'] = get_db_config['bonus8']
                            if get_db_config['bonus9']:
                                db_config['bonus9'] = get_db_config['bonus9']
                            if get_db_config['bonus1']:
                                db_config['bonus10'] = get_db_config['bonus10']
                            if get_db_config['default_bonus_no']:
                                db_config['default_bonus_no'] = get_db_config['default_bonus_no']
                            if get_db_config['auto_charge_enable']:
                                db_config['auto_charge_enable'] = get_db_config['auto_charge_enable']
                            if get_db_config['auto_charge_price']:
                                db_config['auto_charge_price'] = get_db_config['auto_charge_price']
                            if get_db_config['rf_reader_type']:
                                db_config['rf_reader_type'] = get_db_config['rf_reader_type']
                            if get_db_config['shop_no']:
                                db_config['shop_no'] = get_db_config['shop_no']
                            if get_db_config['name']:
                                db_config['name'] = get_db_config['name']
                            if get_db_config['manager_key']:
                                db_config['manager_key'] = get_db_config['manager_key']

                        # 설정 이상 비교
                        if temp_config['device_addr'] != db_config['device_addr']:
                            diff = '1'
                        if temp_config['shop_pw'] != db_config['shop_pw']:
                            diff = '1'
                        if temp_config['card_price'] != db_config['card_price']:
                            diff = '1'
                        if temp_config['card_min_price'] != db_config['card_min_price']:
                            diff = '1'
                        if temp_config['auto_charge_enable'] != db_config['auto_charge_enable']:
                            diff = '1'
                        if temp_config['auto_charge_price'] != db_config['auto_charge_price']:
                            diff = '1'
                        if temp_config['shop_no'] != db_config['shop_no']:
                            diff = '1'
                        if temp_config['bonus1'] != db_config['bonus1']:
                            diff = '2'
                        if temp_config['bonus2'] != db_config['bonus2']:
                            diff = '2'
                        if temp_config['bonus3'] != db_config['bonus3']:
                            diff = '2'
                        if temp_config['bonus4'] != db_config['bonus4']:
                            diff = '2'
                        if temp_config['bonus5'] != db_config['bonus5']:
                            diff = '2'
                        if temp_config['bonus6'] != db_config['bonus6']:
                            diff = '2'
                        if temp_config['bonus7'] != db_config['bonus7']:
                            diff = '2'
                        if temp_config['bonus8'] != db_config['bonus8']:
                            diff = '2'
                        if temp_config['bonus9'] != db_config['bonus9']:
                            diff = '2'
                        if temp_config['bonus10'] != db_config['bonus10']:
                            diff = '2'
                    else:
                        touch_config['state'] = '0'
                        touch_config_list.append(touch_config)

                    # 설정 변경 값 저장

                    # input_date
                    input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                    print(temp_config)
                    print(db_config)

                    if diff == '1':
                        print("설정이상 diff 1 ")
                        update_config_qry = "INSERT INTO gl_charger_config(`device_no`, `shop_pw`, `card_price`, " \
                                            "`card_min_price`, `auto_charge_price`, `auto_charge_enable`, " \
                                            "`shop_no`, `input_date`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                        curs.execute(update_config_qry, (get_touch['no'], shop_pw,
                                                         temp_config['card_price'] , temp_config['card_min_price'] ,
                                                         temp_config['auto_charge_price'],
                                                         temp_config['auto_charge_enable'] , temp_config['shop_no'],
                                                         input_date))
                        conn.commit()
                    if diff == '2':
                        print("설정이상 diff 2 ")
                        update_bonus_qry = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, " \
                                           "`bonus3` = %s, `bonus4` = %s, `bonus5` = %s, `bonus6` = %s, " \
                                           "`bonus7` = %s, `bonus8` = %s, `bonus9` = %s, `bonus10` = %s " \
                                           "WHERE `no` = %s"
                        curs.execute(update_bonus_qry, (temp_config['bonus1'], temp_config['bonus2'],
                                                        temp_config['bonus3'], temp_config['bonus4'],
                                                        temp_config['bonus5'], temp_config['bonus6'],
                                                        temp_config['bonus7'], temp_config['bonus8'],
                                                        temp_config['bonus9'], temp_config['bonus10'],
                                                        db_config['default_bonus_no']))
                        conn.commit()

        # except Exception as e:
        #     print("From get_touch_config except : ", e)
        finally:
            conn.close()
        return touch_config_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    3. 충전 기록 가져오기
    터치 충전기의 데이터베이스에 접속하여 충전 기록을 가져오는 쓰레드 
    터치 충전기의 충전기록 테이블에서 'state'가 '0'인 레코드를 검색하여
    가져와서 데이터 수집장치에 저장하고 'state'를 '1'로 변경하여 
    해당 레코드를 가져갔음을 알림
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_charger_state(self, second=30):
        print("get_charger_state")  # 쓰레드가 작동이 중지되었을 경우를 확인하기 위해 프린트를 찍음

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # device_no, IP 추출
                d_no_qry = "SELECT `no`, `ip` FROM gl_device_list WHERE `type` = %s "
                curs.execute(d_no_qry, gls_config.TOUCH)
                res = curs.fetchall()

                # 데이터 수집 장치에서 추출한 터치 충전기의 수량만큼 반복문 실행
                for row in res:
                    # 터치 충전기 통신 테스트
                    connect = self.get_connect(row['ip'])
                    print("연결 상태 : ",  connect)

                    if connect == 1:
                        # 터치 충전기 접속 설정
                        pi_conn = pymysql.connect(host=row['ip'], user=self.PI_MYSQL_USER, password=self.PI_MYSQL_PWD,
                                                  charset=gls_config.MYSQL_SET, db=self.PI_MYSQL_DB)
                        pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

                        try:
                            with pi_conn.cursor():
                                # 충전 로그 검색
                                state_get_qry = "SELECT `kind`, `card_price` AS 'exhaust_money', " \
                                              "`current_mny` AS 'current_money', `current_bonus`, " \
                                              "`charge_money` AS 'current_charge',	`total_mny` AS 'total_money', " \
                                              "`card_num`, `datetime` AS 'input_date' " \
                                              "FROM card WHERE	state = '0' "
                                pi_curs.execute(state_get_qry)
                                state = pi_curs.fetchall()

                                # 충전 로그 업데이트
                                state_up_qry = "UPDATE card SET `state` = '1' where `state` = '0' "
                                pi_curs.execute(state_up_qry)
                                pi_conn.commit()

                                for state_row in state:
                                    # 충전 로그 데이터 수집 장치 저장
                                    set_state_qry = "INSERT INTO gl_charger_state(`device_no`, `kind`, " \
                                                    "`exhaust_money`, `charger_type`, `sales_type`, `current_money`, " \
                                                    "`current_bonus`, `current_charge`, `total_money`, `card_num`, " \
                                                    "`input_date`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    # 금액 부분 자릿수 조정
                                    set_exhaust_money = str(int(state_row['exhaust_money']) // 100).rjust(4, '0')
                                    set_current_money = str(int(state_row['current_money']) // 100).rjust(4, '0')
                                    set_current_bonus = str(int(state_row['current_bonus']) // 100).rjust(4, '0')
                                    set_current_charge = str(int(state_row['current_charge']) // 100).rjust(5, '0')
                                    set_total_money = str(int(state_row['total_money']) // 100).rjust(5, '0')

                                    curs.execute(set_state_qry, (row['no'], state_row['kind'],
                                                                 set_exhaust_money, "0", "0",
                                                                 set_current_money, set_current_bonus,
                                                                 set_current_charge,
                                                                 set_total_money, state_row['card_num'],
                                                                 state_row['input_date']))
                                    conn.commit()
                        except pymysql.err.OperationalError as e:
                            print("From touch_charger.py get_charger_state except : ", e)
                            self.get_charger_state(1)
                        finally:
                            pi_conn.close()
                    else:
                        print("touch is not connected")
        finally:
            conn.close()
        threading.Timer(second, self.get_charger_state).start()  # 쓰레드 재귀 호출

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    4. 충전 기록 Total 가져오기
    터치 충전기에 별도로 저장된 누적 충전 기록을 가져오는 쓰레드
    현재 사용되지 않는 정보이기에 메인에서 실행하지 않는 쓰레드임
    기본적인 동작은 터치 충전기의 토탈 정보와 데이터 수집장치의 토탈 정보를 비교 후 
    일치하지 않을 시 가져온다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_charger_total(self, second=600):

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=self.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # device_no, IP, total 추출
                d_total_qry = "SELECT d_list.`no` AS 'no',`ip`, `charge`, `cash`, `bonus`, `card_amount`, " \
                              "`card_count`, total.`no` AS 'total_no' " \
                           "FROM gl_device_list AS d_list " \
                           "INNER JOIN gl_charger_total As total ON d_list.`no` = total.device_no " \
                           "WHERE `type` = %s " \
                           "ORDER BY d_list.`no` ASC "
                curs.execute(d_total_qry, gls_config.TOUCH)
                res = curs.fetchall()

                for row in res:
                    # 터치 충전기 통신 테스트
                    connect = self.get_connect(row['ip'])

                    if connect == 1:
                        # 터치 충전기 접속 설정
                        pi_conn = pymysql.connect(host=row['ip'], user=self.PI_MYSQL_USER, password=self.PI_MYSQL_PWD,
                                                  charset=gls_config.MYSQL_SET, db=self.PI_MYSQL_DB)
                        pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

                        try:
                            with pi_conn.cursor():
                                # 충전기 토탈 검색
                                total_get_qry = "SELECT `total` AS 'charge', `charge` AS 'cash', `bonus`, " \
                                                "`card` AS 'card_amount', `card_count` " \
                                                "FROM total"
                                pi_curs.execute(total_get_qry)
                                total = pi_curs.fetchall()

                                for total_row in total:
                                    # 데이터 비교 후 저장
                                    if row['cash'] != total_row['cash']:
                                        total_up_qry = "INSERT INTO gl_charger_total(`no`, `device_no`, `charge`, " \
                                                       "`cash`, `bonus`, `card_amount`, `card_count`) " \
                                                       "VALUES (%s, %s, %s, %s, %s, %s, %s)" \
                                                       "ON DUPLICATE KEY UPDATE `no` = %s, `device_no` = %s, " \
                                                       "`charge` = %s, `cash` = %s, `bonus` = %s, " \
                                                       "`card_amount` = %s, `card_count` = %s "
                                        curs.execute(total_up_qry, (row['total_no'], row['no'], total_row['charge'],
                                                                    total_row['cash'], total_row['bonus'],
                                                                    total_row['card_amount'], total_row['card_count'],
                                                                    row['total_no'], row['no'], total_row['charge'],
                                                                    total_row['cash'], total_row['bonus'],
                                                                    total_row['card_amount'], total_row['card_count']))
                                        conn.commit()
                        finally:
                            pi_conn.close()
                    else:
                        print("touch is not connected")
        except pymysql.err.OperationalError as e:
            print("From touch_config.py get_charger_total except : ", e)
        finally:
            conn.close()
        threading.Timer(second, self.get_charger_state).start()  # 쓰레드 재귀 호출

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    5. 충전기 통신 상태 테스트
    IP를 인자로 받아 해당 IP로 핑을 보내 통신 상태를 체크 후 반환한다.
    * 한개의 핑을 보내며 1초안에 응답이 없으면 통신이 되지 않는 것으로 간주한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_connect(self, ip):
        connect = os.system("timeout 1 ping -c 1 " + ip)
        if connect == 0:
            result = 1
        else:
            result = 0
        return result
