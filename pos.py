import pymysql
import base64
import threading
import os
import gls_config
import device
from datetime import datetime
from collections import OrderedDict

# Pos 기능 목록
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
1. POS 설정                 # set_pos_config
2. POS 설정 불러오기        # get_pos_config
3. Kiosk 설정               # set_kiosk_config
4. Kiosk 설정 불러오기      # get_kiosk_config
5. 월간 매출 조회           # get_monthly_sales
6. 일간 매출 조회           # get_days_sales
7. 기기별 매출 조회         # get_device_sales
8. 금일 세차 매출 조회      # get_today_device_sales
9. 금일 충전 매출 조회      # get_today_charger_sales
10. 금일 매출 총계          # get_today_sales_total
11. 장비 이력 조회          # get_use_device
12. 장비 세부 이력 조회     # get_use_device_detail
13. 카드 등록               # set_card
14. 카드 정보 읽기          # read_card
15. 카드 사용 이력 조회     # get_card_history
16. 카드 이력 상세 조회     # get_card_history_detail
17. 정지 카드 조회          # get_black_card
18. 정지 카드 등록          # set_black_card
19. 정지 카드 해제          # delete_black_card
20. 회원 조회               # get_member_list
21. 회원 레벨 조회          # get_member_level
22. 회원 상세 조회          # get_member_detail
23. 회원 등록               # set_member
24. 회원 삭제               # delete_member
25. 회원 이력               # get_member_history
26. 회원 상세 이력          # get_member_history_detail
27. 회원 검색               # search_member
28. 카드 충전               # set_charge
29. 카드 검색               # search_card
30. 카드 이력 초기화        # reset_card_history
31. 장비 전체 이력 초기화   # reset_device_history
32. 관리업체 정보 불러오기  # get_manager_info
33. CRC 테이블 불러오기     # get_crc
34. 장비 목록 불러오기      # get_device_list
35. 실시간 모니터링(LAN)    # get_lan_device_state
36. 우수회원 보너스         # get_vip_bonus
37. 우수회원 갱신           # update_vip
38. 회원 보너스 설정 조회   # get_member_bonus
39. 회원 보너스 설정        # set_member_bonus 
40. 마스터 카드 이력        # get_master_card_history
41. 관리 업체 리스트        # get_manager_list
42. 마스터 설정 불러오기    # get_master_config
43. 마스터 설정             # set_master_config
44. 히든 설정 불러오기      # get_hidden_config
45. 히든 설정               # set_hidden_config
46. 셀프 주소 추출          # get_self_list
47. 셀프 사용 내역 추출     # get_self_detail
48. 신용 카드 월간 매출     # get_credit_sales
49. 신용 카드 일간 매출     # get_credit_days_sales
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Pos:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    1. 포스 설정 (POS -> DB)
    포스로부터 데이터(각 장비 수량, 상점 정보, 기타 설정 정보)를 전송 받아서 저장.
    상점 정보와 기타 설정 정보는 바로 저장하며
    각 장비의 수량은 현재 DB와 비교 
    추가분이 있을 경우 가장 큰 주소에 +1 하여 등록하며,
    삭제분이 있을 경우 가장 큰 주소의 디바이스를 삭제한다.
    (이 때, 셀프, 진공, 매트, 리더(매트)는 gl_wash_total 테이블에도 등록 및 삭제)
    * 참고 : 사용되지 않는 COIN과 BILL의 경우 별도의 config 테이블이 없기 때문에
             gl_coin_config / gl_bill_config 로 저장하도록 작성하고 주석처리 하였음
    * 참고 2 : 터치 충전기 및 키오스크는 IP 규칙에 따라 IP를 gl_device_list에 등록
    * 참고 3 : 우수회원 시스템 사용여부로 인해 터치충전기에 접속하는 부분이 추가되었음
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_pos_config(self, args):

        print(args)

        result = 1  # return 값

        # 데이터 추출
        self_count = args['self_count']  # 셀프 수량
        air_count = args['air_count']  # 진공 수량
        mate_count = args['mate_count']  # 매트 수량
        charger_count = args['charger_count']  # 충전기 수량
        coin_count = args['coin_count']  # 동전 수량
        bill_count = args['bill_count']  # 지폐 수량
        touch_count = args['touch_count']  # 터치 수량
        kiosk_count = args['kiosk_count']  # 키오스크 수량
        reader_count = args['reader_count']  # 리더(매트) 수량
        garage_count = args['garage_count']  # 게러지 수량
        shop_id = args['shop_id']  # POS 로그인 ID
        orgin_shop_pw = str(args['shop_pw'])
        shop_pw = base64.b64encode(orgin_shop_pw.encode('utf-8'))  # POS 로그인 PW
        shop_no = str(args['shop_no']).rjust(4, '0')  # 상점 번호(매장 ID)
        shop_name = args['shop_name']  # 세차장 상호명
        shop_tel = args['shop_tel']  # 세차장 전화번호
        encry = args['encry']  # 매출자료 암호화 여부
        list_enable = args['list_enable']  # 매출계 표시 여부
        weather_area = args['weather_area']  # 일기예보 지역
        weather_url = args['weather_url']  # 일기예보 정보 URL
        master_card_num = args['master_card_num']  # 마스터 카드 번호
        manager_no = args['manager_no']  # 관리 업체 번호
        ceo = args['ceo']  # 세차장 대표자
        addr = args['addr']  # 세차장 주소
        business_number = args['business_number']  # 세차장 사업자 번호
        set_vip = args['set_vip']  # 우수회원 시스템 사용 여부

        print(args)

        # 기본, 기타 설정 저장
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 상점 정보 업데이트
                set_shop_query = "UPDATE gl_shop_info SET `no` = %s, `name` = %s, `tel` = %s, `addr` = %s, " \
                                 "`ceo` = %s, `business_number` = %s "
                curs.execute(set_shop_query, (shop_no, shop_name, shop_tel, addr, ceo, business_number))
                conn.commit()

                # 포스 정보 업데이트
                set_pos_query = "UPDATE gl_pos_config SET `shop_id` = %s, `shop_pw` = %s, `sales_list_enable` = %s, " \
                                "`sales_list_encryption` = %s, `weather_area` = %s, `weather_url` = %s, " \
                                "`master_card_num` = %s, `manager_no` = %s, `set_vip` = %s "
                curs.execute(set_pos_query, (shop_id, shop_pw, list_enable, encry, weather_area, weather_url,
                                             master_card_num, manager_no, set_vip))
                conn.commit()
        except Exception as e:
            print("From set_pos_config shop_info / pos_config Update except : ", e)
        finally:
            conn.close()

        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 기기 수량 검색 쿼리
        d_count_qry = "SELECT count(*) FROM gl_device_list WHERE `type` = %s"

        try:
            with conn.cursor():
                # 기기 수량 가져오기

                # SELF count
                curs.execute(d_count_qry, gls_config.SELF)
                self_res = curs.fetchone()
                db_self_count = self_res['count(*)']

                # AIR count
                curs.execute(d_count_qry, gls_config.AIR)
                air_res = curs.fetchone()
                db_air_count = air_res['count(*)']

                # MATE count
                curs.execute(d_count_qry, gls_config.MATE)
                mate_res = curs.fetchone()
                db_mate_count = mate_res['count(*)']

                # CHARGER count
                curs.execute(d_count_qry, gls_config.CHARGER)
                rsc_res = curs.fetchone()
                db_charger_count = rsc_res['count(*)']

                # COIN count
                curs.execute(d_count_qry, gls_config.COIN)
                coin_res = curs.fetchone()
                db_coin_count = coin_res['count(*)']

                # BILL count
                curs.execute(d_count_qry, gls_config.BILL)
                bill_res = curs.fetchone()
                db_bill_count = bill_res['count(*)']

                # TOUCH count
                curs.execute(d_count_qry, gls_config.TOUCH)
                touch_res = curs.fetchone()
                db_touch_count = touch_res['count(*)']

                # KIOSK count
                curs.execute(d_count_qry, gls_config.KIOSK)
                kiosk_res = curs.fetchone()
                db_kiosk_count = kiosk_res['count(*)']

                # READER count9
                curs.execute(d_count_qry, gls_config.READER)
                reader_res = curs.fetchone()
                db_reader_count = reader_res['count(*)']

                # GARAGE count
                curs.execute(d_count_qry, gls_config.GARAGE)
                garage_res = curs.fetchone()
                db_garage_count = garage_res['count(*)']

        except Exception as e:
            result = 0
            print("From set_pos_config Select device count except : ", e)
        finally:
            conn.close()

        # Device 수량 체크 및 추가, 부족 분에 대한 처리

        # LAN 통신 장비 ip 설정
        touch_ip_list = ["192.168.0.221", "192.168.0.222", "192.168.0.223", "192.168.0.224", "192.168.0.225"]
        kiosk_ip_list = ["192.168.0.226", "192.168.0.227", "192.168.0.228", "192.168.0.229", "192.168.0.230"]

        # MAX addr 검색
        max_query = "SELECT MAX(`addr`) FROM gl_device_list WHERE type = %s"
        # device_no 검색
        device_no_qry = "SELECT `no` FROM gl_device_list WHERE `addr` = %s AND `type` = %s"
        # gl_device_list 레코드 추가
        d_insert_qry = "INSERT INTO gl_device_list(`addr`, `type`, `ip`) VALUES (%s, %s, %s)"
        # gl_device_list 레코드 삭제
        d_delete_qry = "DELETE FROM gl_device_list WHERE `addr` = %s AND `type` = %s"
        # gl_wash_total 레코드 추가
        w_insert_qry = "INSERT INTO gl_wash_total(`addr`, `type`) VALUES (%s, %s)"
        # gl_wash_total 레코드 삭제
        w_delete_qry = "DELETE FROM gl_wash_total WHERE `addr` = %s AND `type` = %s"

        # self compare
        # 장비 수량의 변동이 없을 때
        if int(self_count) == int(db_self_count):
            pass
        # 장비 추가
        elif int(self_count) > int(db_self_count):
            # 장비 추가 수량
            self_add_count = (int(self_count) - int(db_self_count)) + 1  # for 문 진입을 위해 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.SELF)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 장비 최초 추가( 기존 수량 : 0 )
                    if temp is None:
                        self_max_addr = -1
                    # 장비 추가( 기존 수량이 1 이상)
                    elif temp is not None:
                        self_max_addr = int(temp) - 1  # for 문 진입을 위해 -1 카운트

                    for i in range(1, self_add_count):
                        # addr 생성
                        self_max_addr = self_max_addr + 1
                        add_addr = str(self_max_addr + 1).rjust(2, '0')

                        # gl_device_list 레코드 추가
                        curs.execute(d_insert_qry, (add_addr, gls_config.SELF, '0'))
                        conn.commit()

                        # gl_wash_total 레코드 추가
                        curs.execute(w_insert_qry, (add_addr, gls_config.SELF))
                        conn.commit()

                        # gl_self_config 레코드 추가
                        self_c_insert_q = "INSERT INTO gl_self_config(`device_addr`) VALUES (%s)"
                        curs.execute(self_c_insert_q, add_addr)
                        conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add self except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(self_count) < int(db_self_count):
            # 장비 삭제 수향
            self_remove_count = (int(db_self_count) - int(self_count)) + 1  # for 문 진입을 위해 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.SELF)
                    res = curs.fetchone()
                    self_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위해 +1 count

                    for i in range(1, self_remove_count):
                        # 삭제 addr 추출
                        self_max_addr = self_max_addr - 1
                        remove_addr = str(self_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.SELF))
                        conn.commit()

                        # gl_wash_total 레코드 삭제
                        curs.execute(w_delete_qry, (remove_addr, gls_config.SELF))
                        conn.commit()

                        # # gl_self_config 레코드 삭제
                        # self_c_delete_q = "DELETE FROM gl_self_config WHERE `device_addr` = %s"
                        # curs.execute(self_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete self except : ", e)
            finally:
                conn.close()

        # air compare
        # 장비 수량의 변동이 없을 때
        if int(air_count) == int(db_air_count):
            pass
        # 장비 추가
        elif int(air_count) > int(db_air_count):
            # 장비 추가 수량
            air_add_count = (int(air_count) - int(db_air_count)) + 1  # for 문 진입을 위해 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.AIR)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가(기존 수량 : 0)
                    if temp is None:
                        air_max_addr = -1
                    # 장비 추가( 기존 수량 1 이상)
                    elif temp is not None:
                        air_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                    for i in range(1, air_add_count):
                        # addr 생성
                        air_max_addr = air_max_addr + 1
                        add_addr = str(air_max_addr + 1).rjust(2, '0')

                        # gl_device_list 레코드 추가
                        curs.execute(d_insert_qry, (add_addr, gls_config.AIR, '0'))
                        conn.commit()

                        # gl_wash_total 레코드 추가
                        curs.execute(w_insert_qry, (add_addr, gls_config.AIR))
                        conn.commit()

                        # gl_air_config 레코드 추가
                        air_c_insert_q = "INSERT INTO gl_air_config(`device_addr`) VALUES (%s)"
                        curs.execute(air_c_insert_q, add_addr)
                        conn.commit()
            except Exception as e:
                result = 0
                # print("From set_pos_config Add Air except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(air_count) < int(db_air_count):
            # 삭제 수량
            air_remove_count = (int(db_air_count) - int(air_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.AIR)
                    res = curs.fetchone()
                    air_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, air_remove_count):
                        # 삭제 addr 추출
                        air_max_addr = air_max_addr - 1
                        remove_addr = str(air_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.AIR))
                        conn.commit()

                        # gl_wash_total 레코드 삭제
                        curs.execute(w_delete_qry, (remove_addr, gls_config.AIR))
                        conn.commit()

                        # # gl_self_config 레코드 삭제
                        # air_c_delete_q = "DELETE FROM gl_air_config WHERE `device_addr` = %s"
                        # curs.execute(air_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Air except : ", e)
            finally:
                conn.close()

        # mate compare
        # 장비 수량의 변동이 없을 때
        if int(mate_count) == int(db_mate_count):
            pass
        # 장비 추가
        elif int(mate_count) > int(db_mate_count):
            # 추가 수량
            mate_add_count = (int(mate_count) - int(db_mate_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.MATE)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가( 기존 수량 : 0)
                    if temp is None:
                        mate_max_addr = -1
                    # 장비 추가 (기존 수량 1 이상)
                    elif temp is not None:
                        mate_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                    for i in range(1, mate_add_count):
                        # addr 생성
                        mate_max_addr = mate_max_addr + 1
                        add_addr = str(mate_max_addr + 1).rjust(2, '0')

                        # gl_device_list 레코드 추가
                        curs.execute(d_insert_qry, (add_addr, gls_config.MATE, '0'))
                        conn.commit()

                        # gl_wash_total 레코드 추가
                        curs.execute(w_insert_qry, (add_addr, gls_config.MATE))
                        conn.commit()

                        # gl_mate_config 레코드 추가
                        mate_c_insert_q = "INSERT INTO gl_mate_config(`device_addr`) VALUES (%s)"
                        curs.execute(mate_c_insert_q, add_addr)
                        conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Mate except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(mate_count) < int(db_mate_count):
            # 삭제 수량
            mate_remove_count = (int(db_mate_count) - int(mate_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.MATE)
                    res = curs.fetchone()
                    mate_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, mate_remove_count):
                        # addr 생성
                        mate_max_addr = mate_max_addr - 1
                        remove_addr = str(mate_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.MATE))
                        conn.commit()

                        # gl_wash_total 레코드 삭제
                        curs.execute(w_delete_qry, (remove_addr, gls_config.MATE))
                        conn.commit()

                        # # gl_mate_config 레코드 삭제
                        # mate_c_delete_q = "DELETE FROM gl_mate_config WHERE `device_addr` = %s"
                        # curs.execute(mate_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Mate except : ", e)
            finally:
                conn.close()

        # charger compare
        # 장비 수량의 변동이 없을 때
        if int(charger_count) == int(db_charger_count):
            pass
        # 장비 추가
        elif int(charger_count) > int(db_charger_count):
            # 추가 수량
            charger_add_count = (int(charger_count) - int(db_charger_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.CHARGER)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가 (기존 수량 : 0)
                    if temp is None:
                        charger_max_addr = -1
                    # 장비 추가(기존 수량 1 이상)
                    elif temp is not None:
                        charger_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                    for i in range(1, charger_add_count):
                        # addr 생성
                        charger_max_addr = charger_max_addr + 1
                        add_addr = str(charger_max_addr + 1).rjust(2, '0')

                        # gl_device_list 레코드 추가
                        curs.execute(d_insert_qry, (add_addr, gls_config.CHARGER, '0'))
                        conn.commit()

                        # device_no 검색
                        curs.execute(device_no_qry, (add_addr, gls_config.CHARGER))
                        res = curs.fetchone()
                        device_no = res['no']

                        # gl_charger_config 레코드 추가
                        charger_c_insert_q = "INSERT INTO gl_charger_config(`device_no`, `admin_pw`, `manager_pw`, " \
                                             "`shop_pw`, `shop_no`) " \
                                             "VALUES (%s, %s, %s, %s, %s)"
                        curs.execute(charger_c_insert_q, (device_no, gls_config.ADMIN_PW, gls_config.MANAGER_PW,
                                                          shop_pw, shop_no))
                        conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Charger except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(charger_count) < int(db_charger_count):
            # 삭제 수량
            charger_remove_count = (int(db_charger_count) - int(charger_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.CHARGER)
                    res = curs.fetchone()
                    charger_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, charger_remove_count):
                        # 삭제 addr 추출
                        charger_max_addr = charger_max_addr - 1
                        remove_addr = str(charger_max_addr).rjust(2, '0')

                        # # device_no 검색
                        # curs.execute(device_no_qry, (remove_addr, gls_config.CHARGER))
                        # res = curs.fetchone()
                        # device_no = res['no']
                        #
                        # # gl_charger_config 레코드 삭제
                        # charger_c_delete_q = "DELETE FROM gl_charger_config WHERE `device_no` = %s"
                        # curs.execute(charger_c_delete_q, device_no)
                        # conn.commit()

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.CHARGER))
                        conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Charger except : ", e)
            finally:
                conn.close()

        # coin compare
        # 장비 수량의 변동이 없을 때
        if int(coin_count) == int(db_coin_count):
            pass
        # 장비 추가
        elif int(coin_count) > int(db_coin_count):
            # 추가 수량
            coin_add_count = (int(coin_count) - int(db_coin_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)
            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.COIN)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가 (기존 수량 : 0)
                    if temp is None:
                        coin_max_addr = -1
                    # 장비 추가 (기존 수량 1 이상)
                    elif temp is not None:
                        coin_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                    for i in range(1, coin_add_count):
                        # addr 생성
                        coin_max_addr = coin_max_addr + 1
                        add_addr = str(coin_max_addr + 1).rjust(2, '0')

                        # gl_device_list 레코드 추가
                        curs.execute(d_insert_qry, (add_addr, gls_config.COIN, '0'))
                        conn.commit()

                        # gl_coin_config 레코드 추가 ( 현재 호환 가능한 테이블 없음
                        # coin_c_insert_q = "INSERT INTO gl_coin_config(`device_addr`) VALUES (%s)"
                        # curs.execute(coin_c_insert_q, add_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Coin except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(coin_count) < int(db_coin_count):
            # 삭제 수량
            coin_remove_count = (int(db_coin_count) - int(coin_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.COIN)
                    res = curs.fetchone()
                    coin_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, coin_remove_count):
                        # 삭제 addr 추출
                        coin_max_addr = coin_max_addr - 1
                        remove_addr = str(coin_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.COIN))
                        conn.commit()

                        # gl_coin_config 레코드 삭제
                        # coin_c_delete_q = "DELETE FROM gl_coin_config WHERE `device_addr` = %s"
                        # curs.execute(coin_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Coin except : ", e)
            finally:
                conn.close()

        # bill compare
        # 장비 수량의 변동이 없을 때
        if int(bill_count) == int(db_bill_count):
            pass
        # 장비 추가
        elif int(bill_count) > int(db_bill_count):
            # 추가 수량
            bill_add_count = (int(bill_count) - int(db_bill_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.BILL)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가 (기존 수량 : 0)
                    if temp is None:
                        bill_max_addr = -1
                    # 장비 추가 (기존 수량 1 이상)
                    elif temp is not None:
                        bill_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                for i in range(1, bill_add_count):
                    # addr 생성
                    bill_max_addr = bill_max_addr + 1
                    add_addr = str(bill_max_addr + 1).rjust(2, '0')

                    # gl_device_list 레코드 추가
                    curs.execute(d_insert_qry, (add_addr, gls_config.BILL, '0'))
                    conn.commit()

                    # gl_bill_config 레코드 추가
                    # bill_c_insert_q = "INSERT INTO gl_bill_config(`device_addr`) VALUES (%s)"
                    # bill.execute(bill_c_insert_q, add_addr)
                    # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Bill except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(bill_count) < int(db_bill_count):
            # 삭제 수량
            bill_remove_count = (int(db_bill_count) - int(bill_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.BILL)
                    res = curs.fetchone()
                    bill_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, bill_remove_count):
                        # 삭제 addr 추출
                        bill_max_addr = bill_max_addr - 1
                        remove_addr = str(bill_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.BILL))
                        conn.commit()

                        # gl_bill_config 레코드 삭제
                        # bill_c_delete_q = "DELETE FROM gl_bill_config WHERE `device_addr` = %s"
                        # curs.execute(bill_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Bill except : ", e)
            finally:
                conn.close()

        # touch compare
        # 장비 수량의 변동이 없을 때
        if int(touch_count) == int(db_touch_count):
            pass
        # 장비 추가
        elif int(touch_count) > int(db_touch_count):
            # 추가 수량
            touch_add_count = (int(touch_count) - int(db_touch_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.TOUCH)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가 (기존 수량 : 0)
                    if temp is None:
                        touch_max_addr = -1
                    # 장비 추가(기존 수량 1 이상)
                    elif temp is not None:
                        touch_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                for i in range(1, touch_add_count):
                    # addr 생성
                    touch_max_addr = touch_max_addr + 1
                    add_addr = str(touch_max_addr + 1).rjust(2, '0')

                    # gl_device_list 레코드 추가
                    curs.execute(d_insert_qry, (add_addr, gls_config.TOUCH, touch_ip_list[touch_max_addr]))
                    conn.commit()

                    # device_no 검색
                    curs.execute(device_no_qry, (add_addr, gls_config.TOUCH))
                    res = curs.fetchone()
                    device_no = res['no']

                    # gl_charger_config 레코드 추가
                    touch_c_insert_q = "INSERT INTO gl_charger_config(`device_no`, `admin_pw`, `manager_pw`, " \
                                       "`shop_pw`, `exhaust_charge_enable`, `shop_no`) " \
                                       "VALUES (%s, %s, %s, %s, %s, %s)"
                    curs.execute(touch_c_insert_q, (device_no, gls_config.ADMIN_PW, gls_config.MANAGER_PW,
                                                    shop_pw, "1", shop_no))
                    conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add touch except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(touch_count) < int(db_touch_count):
            # 삭제 수량
            touch_remove_count = (int(db_touch_count) - int(touch_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.TOUCH)
                    res = curs.fetchone()
                    touch_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, touch_remove_count):
                        # 삭제 addr 추출
                        touch_max_addr = touch_max_addr - 1
                        remove_addr = str(touch_max_addr).rjust(2, '0')

                        # # device_no 검색
                        # curs.execute(device_no_qry, (remove_addr, gls_config.TOUCH))
                        # res = curs.fetchone()
                        # device_no = res['no']
                        #
                        # # gl_charger_config 레코드 삭제
                        # touch_c_delete_q = "DELETE FROM gl_charger_config WHERE `device_no` = %s"
                        # curs.execute(touch_c_delete_q, device_no)
                        # conn.commit()

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.TOUCH))
                        conn.commit()

            except Exception as e:
                result = 0
                print("From set_pos_config Delete touch except : ", e)
            finally:
                conn.close()

        # kiosk compare
        # 장비 수량의 변동이 없을 때
        if int(kiosk_count) == int(db_kiosk_count):
            pass
        # 장비 추가
        elif int(kiosk_count) > int(db_kiosk_count):
            # 추가 수량
            kiosk_add_count = (int(kiosk_count) - int(db_kiosk_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.KIOSK)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가 (기존 수량 : 0)
                    if temp is None:
                        kiosk_max_addr = -1
                    # 장비 추가 ( 기존 수량 1 이상)
                    elif temp is not None:
                        kiosk_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                for i in range(1, kiosk_add_count):
                    # addr 생성
                    kiosk_max_addr = kiosk_max_addr + 1
                    add_addr = str(kiosk_max_addr + 1).rjust(2, '0')

                    # gl_device_list 레코드 추가
                    curs.execute(d_insert_qry, (add_addr, gls_config.KIOSK, kiosk_ip_list[kiosk_max_addr]))
                    conn.commit()

                    # device_no 검색
                    curs.execute(device_no_qry, (add_addr, gls_config.KIOSK))
                    res = curs.fetchone()
                    device_no = res['no']

                    # gl_charger_config 레코드 추가
                    kiosk_c_insert_q = "INSERT INTO gl_charger_config(`device_no`, `admin_pw`, `manager_pw`, " \
                                       "`shop_pw`, `shop_no`) " \
                                       "VALUES (%s, %s, %s, %s, %s)"
                    curs.execute(kiosk_c_insert_q, (device_no, gls_config.ADMIN_PW, gls_config.MANAGER_PW,
                                                    shop_pw, shop_no))
                    conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Kiosk except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(kiosk_count) < int(db_kiosk_count):
            # 삭제 수량
            kiosk_remove_count = (int(db_kiosk_count) - int(kiosk_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.KIOSK)
                    res = curs.fetchone()
                    kiosk_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, kiosk_remove_count):
                        # 삭제 addr 추출
                        kiosk_max_addr = kiosk_max_addr - 1
                        remove_addr = str(kiosk_max_addr).rjust(2, '0')

                        # # device_no 검색
                        # curs.execute(device_no_qry, (remove_addr, gls_config.KIOSK))
                        # res = curs.fetchone()
                        # device_no = res['no']
                        #
                        # # gl_charger_config 레코드 삭제
                        # kiosk_c_delete_q = "DELETE FROM gl_charger_config WHERE `device_no` = %s"
                        # curs.execute(kiosk_c_delete_q, device_no)
                        # conn.commit()

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.KIOSK))
                        conn.commit()

            except Exception as e:
                result = 0
                print("From set_pos_config Delete Kiosk except : ", e)
            finally:
                conn.close()

        # reader compare
        # 장비 수량의 변동이 없을 때
        if int(reader_count) == int(db_reader_count):
            pass
        # 장비 추가
        elif int(reader_count) > int(db_reader_count):
            # 추가 수량
            reader_add_count = (int(reader_count) - int(db_reader_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.READER)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가( 기존 수량 : 0)
                    if temp is None:
                        reader_max_addr = -1
                    # 장비 추가 (기존 수량 1 이상)
                    elif temp is not None:
                        reader_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                for i in range(1, reader_add_count):
                    # addr 생성
                    reader_max_addr = reader_max_addr + 1
                    add_addr = str(reader_max_addr + 1).rjust(2, '0')

                    # gl_device_list 레코드 추가
                    curs.execute(d_insert_qry, (add_addr, gls_config.READER, '0'))
                    conn.commit()

                    # gl_wash_total 레코드 추가
                    curs.execute(w_insert_qry, (add_addr, gls_config.READER))
                    conn.commit()

                    # gl_reader_config 레코드 추가
                    reader_c_insert_q = "INSERT INTO gl_reader_config(`device_addr`) VALUES (%s)"
                    curs.execute(reader_c_insert_q, add_addr)
                    conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Reader except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(reader_count) < int(db_reader_count):
            # 삭제 수량
            reader_remove_count = (int(db_reader_count) - int(reader_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.READER)
                    res = curs.fetchone()
                    reader_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, reader_remove_count):
                        # 삭제 addr 추출
                        reader_max_addr = reader_max_addr - 1
                        remove_addr = str(reader_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.READER))
                        conn.commit()

                        # gl_wash_total 레코드 삭제
                        curs.execute(w_delete_qry, (remove_addr, gls_config.READER))
                        conn.commit()

                        # # gl_reader_config 레코드 삭제
                        # reader_c_delete_q = "DELETE FROM gl_reader_config WHERE `device_addr` = %s"
                        # curs.execute(reader_c_delete_q, remove_addr)
                        # conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Reader except : ", e)
            finally:
                conn.close()

        # garage compare
        # 장비 수량의 변동이 없을 때
        if int(garage_count) == int(db_garage_count):
            pass
        # 장비 추가
        elif int(garage_count) > int(db_garage_count):
            # 추가 수량
            garage_add_count = (int(garage_count) - int(db_garage_count)) + 1  # for 문 진입을 위한 +1 카운트

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.GARAGE)
                    res = curs.fetchone()
                    temp = res['MAX(`addr`)']

                    # 최초 장비 추가( 기존 수량 : 0)
                    if temp is None:
                        garage_max_addr = -1
                    # 장비 추가 (기존 수량 1 이상)
                    elif temp is not None:
                        garage_max_addr = int(temp) - 1  # for 문 진입을 위한 -1 카운트

                for i in range(1, garage_add_count):
                    # addr 생성
                    garage_max_addr = garage_max_addr + 1
                    add_addr = str(garage_max_addr + 1).rjust(2, '0')

                    # gl_device_list 레코드 추가
                    curs.execute(d_insert_qry, (add_addr, gls_config.GARAGE, '0'))
                    conn.commit()

                    # gl_wash_total 레코드 추가
                    curs.execute(w_insert_qry, (add_addr, gls_config.GARAGE))
                    conn.commit()

                    # gl_garage_config 레코드 추가
                    garage_c_insert_q = "INSERT INTO gl_garage_config(`device_addr`) VALUES (%s)"
                    curs.execute(garage_c_insert_q, add_addr)
                    conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Add Garage except : ", e)
            finally:
                conn.close()
        # 장비 삭제
        elif int(garage_count) < int(db_garage_count):
            # 삭제 수량
            garage_remove_count = (int(db_garage_count) - int(garage_count)) + 1

            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # MAX addr 검색
                    curs.execute(max_query, gls_config.GARAGE)
                    res = curs.fetchone()
                    garage_max_addr = int(res['MAX(`addr`)']) + 1  # for 문 진입을 위한 +1 카운트

                    for i in range(1, garage_remove_count):
                        # 삭제 addr 추출
                        garage_max_addr = garage_max_addr - 1
                        remove_addr = str(garage_max_addr).rjust(2, '0')

                        # gl_device_list 레코드 삭제
                        curs.execute(d_delete_qry, (remove_addr, gls_config.GARAGE))
                        conn.commit()

                        # gl_wash_total 레코드 삭제
                        curs.execute(w_delete_qry, (remove_addr, gls_config.GARAGE))
                        conn.commit()

                        # gl_garage_config 레코드 삭제
                        garage_c_delete_q = "DELETE FROM gl_garage_config WHERE `device_addr` = %s"
                        curs.execute(garage_c_delete_q, remove_addr)
                        conn.commit()
            except Exception as e:
                result = 0
                print("From set_pos_config Delete Garage except : ", e)
            finally:
                conn.close()

        # 터치 충전기 우수회원 시스템 사용 여부 설정
        # 데이터 베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                               password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_touch_ip_q = "SELECT `ip` FROM gl_device_list WHERE `type`=%s"
                curs.execute(get_touch_ip_q, gls_config.TOUCH)
                get_touch_ip_res = curs.fetchall()

                for touch in get_touch_ip_res:
                    pi_conn = pymysql.connect(host=touch['ip'], user=gls_config.PI_MYSQL_USER,
                                              password=gls_config.PI_MYSQL_PWD, charset=gls_config.MYSQL_SET,
                                              db=gls_config.PI_MYSQL_DB)
                    pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

                    try:
                        with pi_conn.cursor():
                            update_vip_set_q = "UPDATE config SET `data_collect_state` = %s"
                            pi_curs.execute(update_vip_set_q, set_vip)
                            pi_conn.commit()
                    except Exception as e:
                        print(e)
                    finally:
                        pi_conn.close()
        except Exception as e:
            print(e)
        finally:
            conn.close()
        return result

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    2. 포스 설정 정보 불러오기(DB-> POS)
    gl_device_list ->  각 장비의 수량
    gl_shop_info -> 상점 설정 값
    gl_pos_config ->  포스에 관련된 설정 값
    * 참고 : 개발 초기에 작성된 함수라 리스트가 아닌 딕셔너리를 반환하고 있음 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_pos_config(self):
        res = OrderedDict()  # 반환 딕셔너리

        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 장비 수량 추출 쿼리
        d_count_qry = "SELECT count(*) FROM gl_device_list WHERE `type` = %s "

        try:
            with conn.cursor():
                # 기기 수량 및 우선 순위 가져오기

                # SELF count
                curs.execute(d_count_qry, gls_config.SELF)
                self_res = curs.fetchone()
                self_count = self_res['count(*)']
                res['self_count'] = str(self_count)

                # AIR count
                curs.execute(d_count_qry, gls_config.AIR)
                air_res = curs.fetchone()
                air_count = air_res['count(*)']
                res['air_count'] = str(air_count)

                # MATE count
                curs.execute(d_count_qry, gls_config.MATE)
                mate_res = curs.fetchone()
                mate_count = mate_res['count(*)']
                res['mate_count'] = str(mate_count)

                # CHARGER count
                curs.execute(d_count_qry, gls_config.CHARGER)
                rsc_res = curs.fetchone()
                rsc_count = rsc_res['count(*)']
                res['charger_count'] = str(rsc_count)

                # COIN count
                curs.execute(d_count_qry, gls_config.COIN)
                coin_res = curs.fetchone()
                coin_count = coin_res['count(*)']
                res['coin_count'] = str(coin_count)

                # BILL count
                curs.execute(d_count_qry, gls_config.BILL)
                bill_res = curs.fetchone()
                bill_count = bill_res['count(*)']
                res['bill_count'] = str(bill_count)

                # TOUCH count
                curs.execute(d_count_qry, gls_config.TOUCH)
                touch_res = curs.fetchone()
                touch_count = touch_res['count(*)']
                res['touch_count'] = str(touch_count)

                # KIOSK count
                curs.execute(d_count_qry, gls_config.KIOSK)
                kiosk_res = curs.fetchone()
                kiosk_count = kiosk_res['count(*)']
                res['kiosk_count'] = str(kiosk_count)

                # READER count
                curs.execute(d_count_qry, gls_config.READER)
                reader_res = curs.fetchone()
                reader_count = reader_res['count(*)']
                res['reader_count'] = str(reader_count)

                # GARAGE count
                curs.execute(d_count_qry, gls_config.GARAGE)
                garage_res = curs.fetchone()
                garage_count = garage_res['count(*)']
                res['garage_count'] = str(garage_count)

                # 기본 설정, 기타 설정
                query = "SELECT `shop_id`, `shop_pw`, `shop_no`, shop.`name` AS 'shop_name', `tel`AS 'shop_tel', " \
                        "`sales_list_encryption` AS 'encry', `sales_list_enable`AS 'list_enable', `weather_area`, " \
                        "`weather_url`, `master_card_num`, `manager_no`, `addr`, `ceo`, `business_number`, `admin_pw`, `set_vip`," \
                        "`dc_version`, config.`auth_code` AS 'card_binary' " \
                        "FROM gl_pos_config AS config " \
                        "INNER JOIN gl_shop_info AS shop ON config.`shop_no` = shop.`no`"
                curs.execute(query)
                temp_res = curs.fetchone()

                for key, val in temp_res.items():
                    if key == 'shop_pw':
                        val = base64.b64decode(val).decode('utf-8')
                    res[key] = val
                    if key == 'admin_pw':
                        val = base64.b64decode(val).decode('utf-8')
                    res[key] = val
        except Exception as e:
            print("From get_pos_config except : ", e)
        finally:
            conn.close()
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    3. 키오스크 설정 (POS -> DB)
    포스로부터 데이터를 전송받아 저장형식에 맞게 데이터 파싱 후
    데이터 수집장치에 설정 값을 저장함.
    * 참고 : 1. 키오스크에서 주기적으로 수집장치로부터 설정값을 가져가기때문에
                키오스크에 별도로 작업할 내용은 없음
             2. 보너스 설정은 기본 보너스 설정값을 업데이트 함으로 
                다른 기기에 영향을 미침 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_kiosk_config(self, args):
        res = '1'  # 리턴값 (성공여부)

        print(args)

        # 데이터 추출
        device_addr = args['device_addr']  # 키오스크 주소
        orgin_shop_pw = str(args['shop_pw'])
        shop_pw = base64.b64encode(orgin_shop_pw.encode('utf-8'))  # 관리자 로그인 암호
        card_price = str(int(int(args['card_price']) / 100)).rjust(3, '0')  # 카드 가격
        card_min_price = str(int(int(args['card_min_price']) / 100)).rjust(3, '0')  # 카드 발급 진행 최소 금액
        bonus1 = str(int(int(args['bonus1']) / 100)).rjust(3, '0')  # 보너스 1
        bonus2 = str(int(int(args['bonus2']) / 100)).rjust(3, '0')  # 보너스 2
        bonus3 = str(int(int(args['bonus3']) / 100)).rjust(3, '0')  # 보너스 3
        bonus4 = str(int(int(args['bonus4']) / 100)).rjust(3, '0')  # 보너스 4
        bonus5 = str(int(int(args['bonus5']) / 100)).rjust(3, '0')  # 보너스 5
        bonus6 = str(int(int(args['bonus6']) / 100)).rjust(3, '0')  # 보너스 6
        bonus7 = str(int(int(args['bonus7']) / 100)).rjust(3, '0')  # 보너스 7
        bonus8 = str(int(int(args['bonus8']) / 100)).rjust(3, '0')  # 보너스 8
        bonus9 = str(int(int(args['bonus9']) / 100)).rjust(3, '0')  # 보너스 9
        bonus10 = str(int(int(args['bonus10']) / 100)).rjust(3, '0')  # 보너스 10
        credit_bonus1 = str(int(int(args['credit_bonus1']) / 100)).rjust(3, '0')  # 신용카드 보너스 1
        credit_bonus2 = str(int(int(args['credit_bonus2']) / 100)).rjust(3, '0')  # 신용카드 보너스 2
        credit_bonus3 = str(int(int(args['credit_bonus3']) / 100)).rjust(3, '0')  # 신용카드 보너스 3
        credit_bonus4 = str(int(int(args['credit_bonus4']) / 100)).rjust(3, '0')  # 신용카드 보너스 4
        credit_bonus5 = str(int(int(args['credit_bonus5']) / 100)).rjust(3, '0')  # 신용카드 보너스 5
        credit_bonus6 = str(int(int(args['credit_bonus6']) / 100)).rjust(3, '0')  # 신용카드 보너스 6
        credit_bonus7 = str(int(int(args['credit_bonus7']) / 100)).rjust(3, '0')  # 신용카드 보너스 7
        credit_bonus8 = str(int(int(args['credit_bonus8']) / 100)).rjust(3, '0')  # 신용카드 보너스 8
        credit_bonus9 = str(int(int(args['credit_bonus9']) / 100)).rjust(3, '0')  # 신용카드 보너스 9
        credit_bonus10 = str(int(int(args['credit_bonus10']) / 100)).rjust(3, '0')  # 신용카드 보너스 10
        auto_charge_enable = args['auto_charge_enable']  # 자동 충전 기능 사용 여부
        auto_charge_price = str(int(int(args['auto_charge_price']) / 100)).rjust(3, '0')  # 자동 충전 금액
        exhaust_charge_enable = args['exhaust_charge_enable']  # 발급 시 충전 여부
        rf_reader_type = args['rf_reader_type']  # rf 리더기 타입
        shop_no = args['shop_no']  # 상점번호(카드 매장 ID)
        name = args['name']  # 세차장 상호명

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # device_no 추출
                d_no_qry = "SELECT `no` FROM gl_device_list WHERE `addr` = %s AND `type` = %s"
                curs.execute(d_no_qry, (device_addr, gls_config.KIOSK))
                d_no_res = curs.fetchall()

                for row in d_no_res:
                    device_no = row['no']

                # 키오스크 설정 업데이트
                kiosk_query = "UPDATE gl_charger_config SET `shop_pw` = %s, `card_price` = %s, " \
                              "`card_min_price` = %s, `auto_charge_enable` = %s, `auto_charge_price` = %s, " \
                              "`exhaust_charge_enable` = %s, `rf_reader_type` = %s, `shop_no` = %s, " \
                              "`admin_pw` = %s, `manager_pw` = %s WHERE `device_no` = %s"
                curs.execute(kiosk_query,
                             (shop_pw, card_price, card_min_price, auto_charge_enable, auto_charge_price,
                              exhaust_charge_enable, rf_reader_type, shop_no,
                              gls_config.ADMIN_PW, gls_config.MANAGER_PW, device_no))
                conn.commit()

                # 현금 보너스 설정 값 업데이트
                bonus_query = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, " \
                              "`bonus4` = %s, `bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, " \
                              "`bonus9` = %s, `bonus10` = %s WHERE `no` = %s"
                curs.execute(bonus_query, (bonus1, bonus2, bonus3, bonus4, bonus5, bonus6, bonus7, bonus8,
                                           bonus9, bonus10, gls_config.DEFAULT_BONUS))
                conn.commit()

                # 신용카드 보너스 설정 값 없데이트
                curs.execute(bonus_query, (credit_bonus1, credit_bonus2, credit_bonus3, credit_bonus4, credit_bonus5,
                                           credit_bonus6, credit_bonus7, credit_bonus8, credit_bonus9, credit_bonus10,
                                           gls_config.CREDIT_BONUS))
                conn.commit()

        except Exception as e:
            print("From set_kiosk_config except : ", e)
            res = 0
        finally:
            conn.close()
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    4. 키오스크 설정 불러오기 (DB -> POS)
    gl_device_list / gl_charger_config / gl_charger_bonus / gl_shop_info 
    위의 4개의 테이블을 조인해서 필요한 데이터를 가져온 후 
    포스에서 읽을 수 있는 형식으로 데이터를 파싱 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_kiosk_config(self):
        # 데이터 수집 장치 DB 접속
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 반환 리스트
        kiosk_list = []

        try:
            with conn.cursor():
                query = "SELECT d_list.`addr` AS 'device_addr', d_list.`ip`, `shop_pw`, `card_price`, `card_min_price`, " \
                        "`bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, `bonus6`, `bonus7`, `bonus8`, " \
                        "`bonus9`, `bonus10`, `auto_charge_enable`, `auto_charge_price`, `exhaust_charge_enable`, " \
                        "`rf_reader_type`, `shop_no`, `name`, `manager_key`," \
                        "(SELECT `bonus1` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus1', " \
                        "(SELECT `bonus2` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus2', "\
                        "(SELECT `bonus3` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus3', " \
                        "(SELECT `bonus4` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus4', " \
                        "(SELECT `bonus5` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus5', " \
                        "(SELECT `bonus6` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus6', " \
                        "(SELECT `bonus7` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus7', " \
                        "(SELECT `bonus8` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus8', " \
                        "(SELECT `bonus9` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus9', " \
                        "(SELECT `bonus10` FROM gl_charger_bonus WHERE `no` = '1') AS 'credit_bonus10' " \
                        "FROM gl_charger_config AS config " \
                        "INNER JOIN gl_device_list AS d_list ON config.device_no = d_list.`no` " \
                        "INNER JOIN gl_charger_bonus AS bonus ON config.default_bonus_no = bonus.`no` " \
                        "INNER JOIN gl_shop_info AS shop ON config.shop_no = shop.`no` " \
                        "WHERE	d_list.type = %s ORDER BY 	d_list.`addr` ASC"
                curs.execute(query, gls_config.KIOSK)
                res = curs.fetchall()

                for row in res:
                    # 임시 저장 딕셔너리
                    temp_kiosk = OrderedDict()

                    # 통신 테스트
                    con_res = os.system("timeout 1 ping -c 1 " + row['ip'])
                    if con_res == 0:
                        temp_kiosk['state'] = '1'
                    else:
                        temp_kiosk['state'] = '0'

                    temp_kiosk['device_addr'] = row['device_addr']

                    # 암호 복호화
                    if row['shop_pw']:
                        temp_kiosk['shop_pw'] = base64.b64decode(str(row['shop_pw'])).decode('utf-8')

                    # 금액 자릿수 조절
                    if row['card_price']:
                        temp_kiosk['card_price'] = int(int(row['card_price']) * 100)
                    if row['card_min_price']:
                        temp_kiosk['card_min_price'] = int(int(row['card_min_price']) * 100)
                    if row['bonus1']:
                        temp_kiosk['bonus1'] = int(int(row['bonus1']) * 100)
                    if row['bonus2']:
                        temp_kiosk['bonus2'] = int(int(row['bonus2']) * 100)
                    if row['bonus3']:
                        temp_kiosk['bonus3'] = int(int(row['bonus3']) * 100)
                    if row['bonus4']:
                        temp_kiosk['bonus4'] = int(int(row['bonus4']) * 100)
                    if row['bonus5']:
                        temp_kiosk['bonus5'] = int(int(row['bonus5']) * 100)
                    if row['bonus6']:
                        temp_kiosk['bonus6'] = int(int(row['bonus6']) * 100)
                    if row['bonus7']:
                        temp_kiosk['bonus7'] = int(int(row['bonus7']) * 100)
                    if row['bonus8']:
                        temp_kiosk['bonus8'] = int(int(row['bonus8']) * 100)
                    if row['bonus9']:
                        temp_kiosk['bonus9'] = int(int(row['bonus9']) * 100)
                    if row['bonus10']:
                        temp_kiosk['bonus10'] = int(int(row['bonus10']) * 100)

                    if row['credit_bonus1']:
                        temp_kiosk['credit_bonus1'] = int(int(row['credit_bonus1']) * 100)
                    if row['credit_bonus2']:
                        temp_kiosk['credit_bonus2'] = int(int(row['credit_bonus2']) * 100)
                    if row['credit_bonus3']:
                        temp_kiosk['credit_bonus3'] = int(int(row['credit_bonus3']) * 100)
                    if row['credit_bonus4']:
                        temp_kiosk['credit_bonus4'] = int(int(row['credit_bonus4']) * 100)
                    if row['credit_bonus5']:
                        temp_kiosk['credit_bonus5'] = int(int(row['credit_bonus5']) * 100)
                    if row['credit_bonus6']:
                        temp_kiosk['credit_bonus6'] = int(int(row['credit_bonus6']) * 100)
                    if row['credit_bonus7']:
                        temp_kiosk['credit_bonus7'] = int(int(row['credit_bonus7']) * 100)
                    if row['credit_bonus8']:
                        temp_kiosk['credit_bonus8'] = int(int(row['credit_bonus8']) * 100)
                    if row['credit_bonus9']:
                        temp_kiosk['credit_bonus9'] = int(int(row['credit_bonus9']) * 100)
                    if row['credit_bonus10']:
                        temp_kiosk['credit_bonus10'] = int(int(row['credit_bonus10']) * 100)
                    if row['auto_charge_price']:
                        temp_kiosk['auto_charge_price'] = int(int(row['auto_charge_price']) * 100)
                    if row['auto_charge_enable']:
                        temp_kiosk['auto_charge_enable'] = row['auto_charge_enable']
                    if row['exhaust_charge_enable']:
                        temp_kiosk['exhaust_charge_enable'] = row['exhaust_charge_enable']
                    if row['rf_reader_type']:
                        temp_kiosk['rf_reader_type'] = row['rf_reader_type']
                    if row['shop_no']:
                        temp_kiosk['shop_no'] = row['shop_no']
                    if row['name']:
                        temp_kiosk['name'] = row['name']
                    if row['manager_key']:
                        temp_kiosk['manager_key'] = row['manager_key']

                    kiosk_list.append(temp_kiosk)
        except Exception as e:
            print("From get_kiosk_config except : ", e)
        finally:
            conn.close()
            print(kiosk_list)

        return kiosk_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    5. 월간 매출 자료 불러오기(DB -> POS)
    1~31일까지 반복문을 돌며
    gl_self_state / gl_air_state / gl_mate_state / gl_reader_state / gl_charger_state
    위의 5개의 테이블에 각각 접속하여 매출에 관한 정보를 가져온 후
    일별로 딕셔너리에 데이터를 저장하고 해당 딕셔너리를 리스트에 추가해서  
    월별 매출 리스트를 생성 후 반환한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_monthly_sales(self, year, month):
        sales_list = []  # 월간 매출 저장 레코드
        total_card = "0"  # 카드 누계 초기화
        total_cash = "0"  # 현금 누계 초기화
        total_credit = "0" # 신용카드 누계 초기화
        total_money = "0" # 신용카드 누계 초기화

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 월간 매출 리스트 추출(레코드 : 일간 매출)
                for i in range(1, 32):
                    days = str(i)

                    # 일간 매출 저장 레코드 초기화
                    temp_list = OrderedDict()  # 일간 매출 저장 레코드
                    temp_list['days'] = '0'  # 일자 초기화
                    temp_list['card'] = '0'  # 카드 매출
                    temp_list['cash'] = '0'  # 현금 매출
                    temp_list['credit_money'] = '0'  # 신용카드 매출
                    temp_list['current_money'] = '0'  # 현금 매출
                    temp_list['charge'] = '0'  # 충전 합계
                    temp_list['bonus'] = '0'  # 보너스 합계
                    temp_list['card_total'] = '0'  # 카드 매출 누계
                    temp_list['cash_total'] = '0'  # 현금 매출 누계
                    temp_list['credit_total'] = '0'  # 신용카드 매출 누계
                    temp_list['money_total'] = '0'  # 현금 매출 누계

                    # 셀프 매출 추출
                    temp_self = OrderedDict()
                    temp_self['card'] = '0'
                    temp_self['cash'] = '0'
                    self_total_qry = "SELECT SUM(`use_card`) * '100' AS 'self_card', " \
                                     " SUM(`use_cash`) * '100' AS 'self_cash' " \
                                     " FROM	gl_self_state WHERE	 end_time " \
                                     " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(self_total_qry)
                    self_res = curs.fetchall()

                    # 소수점 절삭
                    for row in self_res:
                        if row['self_card']:
                            temp_self['card'] = int(row['self_card'])
                        if row['self_cash']:
                            temp_self['cash'] = int(row['self_cash'])

                    # 진공 매출 추출
                    temp_air = OrderedDict()
                    temp_air['card'] = '0'
                    temp_air['cash'] = '0'
                    air_total_qry = "SELECT SUM(`air_card`) * '100' AS 'air_card', " \
                                    " SUM(`air_cash`) * '100' AS 'air_cash' " \
                                    " FROM	gl_air_state WHERE	 `end_time`" \
                                    " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(air_total_qry)
                    air_res = curs.fetchall()

                    # 소수점 절삭
                    for row in air_res:
                        if row['air_card']:
                            temp_air['card'] = int(row['air_card'])
                        if row['air_cash']:
                            temp_air['cash'] = int(row['air_cash'])

                    # 매트 매출 추출
                    temp_mate = OrderedDict()
                    temp_mate['card'] = '0'
                    temp_mate['cash'] = '0'
                    mate_total_qry = "SELECT SUM(`mate_card`) * '100' AS 'mate_card', " \
                                     " SUM(`mate_cash`) * '100' AS 'mate_cash' " \
                                     " FROM	gl_mate_state WHERE	 `end_time`" \
                                     " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(mate_total_qry)
                    mate_res = curs.fetchall()

                    # 소수점 절삭
                    for row in mate_res:
                        if row['mate_card']:
                            temp_mate['card'] = int(row['mate_card'])
                        if row['mate_cash']:
                            temp_mate['cash'] = int(row['mate_cash'])

                    # 리더 매출 추출
                    temp_reader = OrderedDict()
                    temp_reader['card'] = '0'
                    temp_reader['cash'] = '0'
                    reader_total_qry = "SELECT SUM(`reader_card`) * '100' AS 'reader_card', " \
                                       " SUM(`reader_cash`) * '100' AS 'reader_cash' " \
                                       " FROM	gl_reader_state WHERE `end_time`" \
                                       " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(reader_total_qry)
                    reader_res = curs.fetchall()

                    # 소수점 절삭
                    for row in reader_res:
                        if row['reader_card']:
                            temp_reader['card'] = int(row['reader_card'])
                        if row['reader_cash']:
                            temp_reader['cash'] = int(row['reader_cash'])

                    # garage 매출 추출
                    temp_garage = OrderedDict()
                    temp_garage['card'] = '0'
                    temp_garage['cash'] = '0'
                    garage_total_qry = "SELECT SUM(`use_card`) * '100' AS 'garage_card', " \
                                       " SUM(`use_cash`) * '100' AS 'garage_cash' " \
                                       " FROM	gl_garage_state WHERE `end_time`" \
                                       " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(garage_total_qry)
                    garage_res = curs.fetchall()

                    # 소수점 절삭
                    for row in garage_res:
                        if row['garage_card']:
                            temp_garage['card'] = int(row['garage_card'])
                        if row['garage_cash']:
                            temp_garage['cash'] = int(row['garage_cash'])

                    # 충전 데이터 추출
                    temp_charger = OrderedDict()
                    temp_charger['charge'] = '0'
                    temp_charger['bonus'] = '0'
                    temp_charger['credit_money'] = '0'
                    temp_charger['current_money'] = '0'
                    charger_total_qry = "SELECT SUM(`current_charge`) * '100' AS 'charge', " \
                                        " SUM(`current_bonus`) * '100' AS 'bonus', " \
                                        " SUM(`current_credit_money`) * 100 AS 'credit_money', " \
                                        " SUM(`current_money`) * 100 AS 'current_money' " \
                                        " FROM	gl_charger_state WHERE `input_date`" \
                                        " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(charger_total_qry)
                    charger_res = curs.fetchall()

                    # 소수점 절삭
                    for row in charger_res:
                        if row['charge']:
                            temp_charger['charge'] = int(row['charge'])
                        if row['bonus']:
                            temp_charger['bonus'] = int(row['bonus'])
                        if row['credit_money']:
                            temp_charger['credit_money'] = int(row['credit_money'])
                        if row['current_money']:
                            temp_charger['current_money'] = int(row['current_money'])

                    # 현금, 카드 누계 저장
                    total_card = (int(total_card) + int(temp_self['card']) + int(temp_air['card'])
                                  + int(temp_mate['card']) + int(temp_reader['card']) + int(temp_garage['card']))
                    total_cash = (int(total_cash) + int(temp_self['cash']) + int(temp_air['cash'])
                                  + int(temp_mate['cash']) + int(temp_reader['cash']) + int(temp_garage['cash']))
                    total_credit = (int(total_credit) + int(temp_charger['credit_money']))
                    total_money = (int(total_money) + int(temp_charger['current_money']))

                    # 일간 매출 저장
                    temp_list['days'] = days
                    temp_list['card'] = (int(temp_self['card']) + int(temp_air['card']) + int(temp_mate['card'])
                                         + int(temp_reader['card']) + int(temp_garage['card']))
                    temp_list['cash'] = (int(temp_self['cash']) + int(temp_air['cash']) + int(temp_mate['cash'])
                                         + int(temp_reader['cash']) + int(temp_garage['cash']))
                    temp_list['charge'] = int(temp_charger['charge'])
                    temp_list['bonus'] = int(temp_charger['bonus'])
                    temp_list['credit_money'] = int(temp_charger['credit_money'])
                    temp_list['current_money'] = int(temp_charger['current_money'])
                    temp_list['card_total'] = total_card
                    temp_list['cash_total'] = total_cash
                    temp_list['credit_total'] = total_credit
                    temp_list['money_total'] = total_money

                    # 월간 매출 리스트 저장
                    sales_list.insert(i - 1, temp_list)
        except Exception as e:
            print("From get_monthly_sales except : ", e)
        finally:
            conn.close()

        return sales_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    6. 일간 매출 자료 불러오기(DB -> POS)
    gl_sales_list(view) 에서 일간 매출 자료를 검색하여 반환한다.
    * 참고 : UNION 으로 구성된 VIEW 라서 세차장비와 충전장비의 필드명이 동일함.
             이는 포스에서 device_type 으로 분기하여 다르게 표기함으로써 해결 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_days_sales(self, year, month, days):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        test_list = []

        try:
            with conn.cursor():
                get_days_total_q = "SELECT `no`, `device_name`, `device_type`, `device_addr`, `card_num`, `time`, " \
                                   "`cash` * 100 AS 'cash', `card` * 100 AS 'card', `credit_money` * 100 AS 'credit_money', " \
                                   "`current_money` * 100 AS 'current_money', " \
                                   "`remain_card` * 100 AS 'remain_card', `master_card` * 100 AS 'master_card', " \
                                   "UNIX_TIMESTAMP(`start_time`) AS 'start_time', " \
                                   "UNIX_TIMESTAMP(`end_time`) AS 'end_time' " \
                                   "FROM gl_sales_list WHERE end_time " \
                                   " LIKE '%" + str(year) + "-" + str(month).rjust(2, '0') + "-" \
                                   + str(days).rjust(2, '0') + "%'" \
                                   + " ORDER BY `end_time` ASC"
                print(get_days_total_q)
                curs.execute(get_days_total_q)
                res = curs.fetchall()



                for row in res:
                    temp_dict = OrderedDict()
                    if str(row['device_type']) == str(gls_config.SELF):
                        temp_dict['enable_type'] = self.get_self_detail(row['no'], 'self')
                        temp_dict['credit_money'] = '0'
                    elif str(row['device_type']) == str(gls_config.AIR):
                        temp_dict['enable_type'] = '진공'
                        temp_dict['credit_money'] = '0'
                    elif str(row['device_type']) == str(gls_config.MATE):
                        temp_dict['enable_type'] = '매트'
                        temp_dict['credit_money'] = '0'
                    elif str(row['device_type']) == str(gls_config.READER):
                        temp_dict['enable_type'] = '리더'
                        temp_dict['credit_money'] = '0'
                    elif str(row['device_type']) == str(gls_config.GARAGE):
                        temp_dict['enable_type'] = self.get_self_detail(row['no'], 'garage')
                        temp_dict['credit_money'] = '0'
                    elif str(row['device_type']) == str(gls_config.KIOSK):
                        temp_dict['enable_type'] = ' - '
                        temp_dict['credit_money'] = int(row['credit_money'])
                    elif str(row['device_type']) == str(gls_config.POS):
                        temp_dict['enable_type'] = ' - '
                        temp_dict['credit_money'] = int(row['credit_money'])
                    else:
                        temp_dict['enable_type'] = ' - '
                        temp_dict['credit_money'] = '0'

                    # 소수점 절삭
                    if row['cash']:
                        temp_dict['cash'] = int(row['cash'])
                    if row['card']:
                        temp_dict['card'] = int(row['card'])
                    if row['remain_card']:
                        temp_dict['remain_card'] = int(row['remain_card'])
                    if row['master_card']:
                        temp_dict['master_card'] = int(row['master_card'])
                    if row['current_money']:
                        temp_dict['current_money'] = int(row['current_money'])

                    # 0원에 대한 처리
                    if row['cash'] == 0.0:
                        temp_dict['cash'] = 0
                    if row['card'] == 0.0:
                        temp_dict['card'] = 0
                    if row['remain_card'] == 0.0:
                        temp_dict['remain_card'] = 0
                    if row['master_card'] == 0.0:
                        temp_dict['master_card'] = 0
                    if row['current_money'] == 0.0:
                        temp_dict['current_money'] = 0

                    if row['device_name']:
                        temp_dict['device_name'] = row['device_name']
                    if row['device_type']:
                        temp_dict['device_type'] = row['device_type']
                    if row['device_addr']:
                        temp_dict['device_addr'] = row['device_addr']
                    if row['card_num']:
                        temp_dict['card_num'] = row['card_num']
                    if row['time']:
                        temp_dict['time'] = row['time']
                    if row['start_time']:
                        temp_dict['start_time'] = str(row['start_time'])
                    if row['end_time']:
                        temp_dict['end_time'] = str(row['end_time'])

                    test_list.append(temp_dict)

        except Exception as e:
            print("From get_days_sales except : ", e)
        finally:
            conn.close()

        print(str(test_list))

        return test_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    7. 기기별 매출 자료 불러오기(DB -> POS)
    gl_device_list 에서 각 장비의 수량을 추출하고 해당 장비별로 수량에 맞춰 반복문을
    실행하여 매출 값을 딕셔너리에 저장하고 이를 반환 리스트에 추가함.
    매출은 gl_sales_list(View) 한 곳에서 참조하지만, 세차 장비와 충전장비에서 
    서로 가져와야하는 값이 다르기 때문에 두개의 쿼리로 나눠서 작성함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_device_sales(self, year, month, days):
        device_sales_list = []  # 리턴 값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 장비 이름 추출
        device_name_qry = "SELECT `device_name` AS 'name' FROM gl_device_info WHERE `type` = %s"
        # 장비 번호 카운트
        device_addr_qry = "SELECT `addr` FROM gl_device_list WHERE `type` = %s ORDER BY `addr` ASC"
        # 세차장비 매출 쿼리
        wash_sales_qry = "SELECT SUM(`cash`) * 100 AS 'cash', SUM(`card`) * 100 AS 'card', `device_type` " \
                         " FROM gl_sales_list " \
                         " WHERE `device_type` = %s " \
                         " AND `device_addr` = %s " \
                         " AND `end_time`" \
                         " LIKE '%%" + str(year) + "-" + str(month).rjust(2, '0') + "-" \
                         + str(days).rjust(2, '0') + "%%' "
        # 충전장비 매출 쿼리
        charger_sales_qry = "SELECT SUM(`cash`) * 100 AS 'charge', SUM(`card`) * 100 AS 'bonus', `device_type`, " \
                            "SUM(`master_card`) * 100 AS 'card_amount', SUM(`credit_money`) * 100 AS 'credit_money', " \
                            "SUM(`current_money`) * 100 AS 'current_money', " \
                            "COUNT(CASE WHEN `time` = '0' THEN 1 END) AS 'card_count'" \
                            " FROM gl_sales_list " \
                            " WHERE `device_type` = %s " \
                            " AND `device_addr` = %s " \
                            " AND `end_time`" \
                            " LIKE '%%" + str(year) + "-" + str(month).rjust(2, '0') + "-" \
                            + str(days).rjust(2, '0') + "%%' "
        try:
            with conn.cursor():
                # 셀프
                curs.execute(device_name_qry, gls_config.SELF)
                self_name_temp = curs.fetchall()
                for row in self_name_temp:
                    self_name = row['name']  # 장비명
                # 장비 주소
                curs.execute(device_addr_qry, gls_config.SELF)
                self_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in self_addr:
                    curs.execute(wash_sales_qry, (gls_config.SELF, row['addr']))
                    self_res = curs.fetchall()

                    for self_row in self_res:
                        # 값을 저장할 딕셔너리 초기화
                        self_sales = OrderedDict()
                        self_sales['device_addr'] = '0'
                        self_sales['device_name'] = '0'
                        self_sales['device_type'] = gls_config.SELF
                        self_sales['cash'] = '0'
                        self_sales['card'] = '0'

                        # 실제 값 저장
                        self_sales['device_addr'] = row['addr']
                        self_sales['device_name'] = self_name

                        # 소수점 절삭
                        if self_row['cash']:
                            self_sales['cash'] = int(self_row['cash'])
                        if self_row['card']:
                            self_sales['card'] = int(self_row['card'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(self_sales)

                # 진공
                curs.execute(device_name_qry, gls_config.AIR)
                air_name_temp = curs.fetchall()
                for row in air_name_temp:
                    air_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.AIR)
                air_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in air_addr:
                    curs.execute(wash_sales_qry, (gls_config.AIR, row['addr']))
                    air_res = curs.fetchall()

                    for air_row in air_res:
                        # 값을 저장할 딕셔너리 초기화
                        air_sales = OrderedDict()
                        air_sales['device_addr'] = '0'
                        air_sales['device_name'] = '0'
                        air_sales['device_type'] = gls_config.AIR
                        air_sales['cash'] = '0'
                        air_sales['card'] = '0'

                        # 실제 값 저장
                        air_sales['device_addr'] = row['addr']
                        air_sales['device_name'] = air_name

                        # 소수점 절삭
                        if air_row['cash']:
                            air_sales['cash'] = int(air_row['cash'])
                        if air_row['card']:
                            air_sales['card'] = int(air_row['card'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(air_sales)

                # 매트
                curs.execute(device_name_qry, gls_config.MATE)
                mate_name_temp = curs.fetchall()
                for row in mate_name_temp:
                    mate_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.MATE)
                mate_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in mate_addr:
                    curs.execute(wash_sales_qry, (gls_config.MATE, row['addr']))
                    mate_res = curs.fetchall()

                    for mate_row in mate_res:
                        # 값을 저장할 딕셔너리 초기화
                        mate_sales = OrderedDict()
                        mate_sales['device_addr'] = '0'
                        mate_sales['device_name'] = '0'
                        mate_sales['device_type'] = gls_config.MATE
                        mate_sales['cash'] = '0'
                        mate_sales['card'] = '0'

                        # 실제 값 저장
                        mate_sales['device_addr'] = row['addr']
                        mate_sales['device_name'] = mate_name

                        # 소수점 절삭
                        if mate_row['cash']:
                            mate_sales['cash'] = int(mate_row['cash'])
                        if mate_row['card']:
                            mate_sales['card'] = int(mate_row['card'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(mate_sales)

                # 매트(리더)
                curs.execute(device_name_qry, gls_config.READER)
                reader_name_temp = curs.fetchall()
                for row in reader_name_temp:
                    reader_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.READER)
                reader_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in reader_addr:
                    curs.execute(wash_sales_qry, (gls_config.READER, row['addr']))
                    reader_res = curs.fetchall()

                    for reader_row in reader_res:
                        # 값을 저장할 딕셔너리 초기화
                        reader_sales = OrderedDict()
                        reader_sales['device_addr'] = '0'
                        reader_sales['device_name'] = '0'
                        reader_sales['device_type'] = gls_config.READER
                        reader_sales['cash'] = '0'
                        reader_sales['card'] = '0'

                        # 실제 값 저장
                        reader_sales['device_addr'] = row['addr']
                        reader_sales['device_name'] = reader_name

                        # 소수점 절삭
                        if reader_row['cash']:
                            reader_sales['cash'] = int(reader_row['cash'])
                        if reader_row['card']:
                            reader_sales['card'] = int(reader_row['card'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(reader_sales)

                # Garage
                curs.execute(device_name_qry, gls_config.GARAGE)
                garage_name_temp = curs.fetchall()
                for row in garage_name_temp:
                    garage_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.GARAGE)
                garage_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in garage_addr:
                    curs.execute(wash_sales_qry, (gls_config.GARAGE, row['addr']))
                    garage_res = curs.fetchall()

                    for garage_row in garage_res:
                        # 값을 저장할 딕셔너리 초기화
                        garage_sales = OrderedDict()
                        garage_sales['device_addr'] = '0'
                        garage_sales['device_name'] = '0'
                        garage_sales['device_type'] = gls_config.GARAGE
                        garage_sales['cash'] = '0'
                        garage_sales['card'] = '0'

                        # 실제 값 저장
                        garage_sales['device_addr'] = row['addr']
                        garage_sales['device_name'] = garage_name

                        # 소수점 절삭
                        if garage_row['cash']:
                            garage_sales['cash'] = int(garage_row['cash'])
                        if garage_row['card']:
                            garage_sales['card'] = int(garage_row['card'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(garage_sales)

                # 충전기
                curs.execute(device_name_qry, gls_config.CHARGER)
                charger_name_temp = curs.fetchall()
                for row in charger_name_temp:
                    charger_name = row['name']  # 장비명
                # 장비 주소
                curs.execute(device_addr_qry, gls_config.CHARGER)
                charger_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in charger_addr:
                    curs.execute(charger_sales_qry, (gls_config.CHARGER, row['addr']))
                    charger_res = curs.fetchall()

                    for charger_row in charger_res:
                        # 값을 저장할 딕셔너리 초기화
                        charger_sales = OrderedDict()
                        charger_sales['device_addr'] = '0'
                        charger_sales['device_name'] = '0'
                        charger_sales['device_type'] = gls_config.CHARGER
                        charger_sales['charge'] = '0'
                        charger_sales['bonus'] = '0'
                        charger_sales['card_amount'] = '0'
                        charger_sales['card_count'] = '0'

                        # 실제 값 저장
                        charger_sales['device_addr'] = row['addr']
                        charger_sales['device_name'] = charger_name
                        charger_sales['credit_money'] = '0'
                        charger_sales['current_money'] = '0'
                        charger_sales['card_count'] = charger_row['card_count']

                        # 소수점 절삭
                        if charger_row['charge']:
                            charger_sales['charge'] = int(charger_row['charge'])
                        if charger_row['bonus']:
                            charger_sales['bonus'] = int(charger_row['bonus'])
                        if charger_row['card_amount']:
                            charger_sales['card_amount'] = int(charger_row['card_amount'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(charger_sales)

                # 터치
                curs.execute(device_name_qry, gls_config.TOUCH)
                touch_name_temp = curs.fetchall()
                for row in touch_name_temp:
                    touch_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.TOUCH)
                touch_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in touch_addr:
                    curs.execute(charger_sales_qry, (gls_config.TOUCH, row['addr']))
                    touch_res = curs.fetchall()

                    for touch_row in touch_res:
                        # 값을 저장할 딕셔너리 초기화
                        touch_sales = OrderedDict()
                        touch_sales['device_addr'] = '0'
                        touch_sales['device_name'] = '0'
                        touch_sales['device_type'] = gls_config.TOUCH
                        touch_sales['charge'] = '0'
                        touch_sales['bonus'] = '0'
                        touch_sales['card_amount'] = '0'
                        touch_sales['card_count'] = '0'

                        # 실제 값 저장
                        touch_sales['device_addr'] = row['addr']
                        touch_sales['device_name'] = touch_name
                        touch_sales['card_count'] = touch_row['card_count']
                        touch_sales['credit_money'] = '0'
                        touch_sales['current_money'] = '0'

                        # 소수점 절삭
                        if touch_row['charge']:
                            touch_sales['charge'] = int(touch_row['charge'])
                        if touch_row['bonus']:
                            touch_sales['bonus'] = int(touch_row['bonus'])
                        if touch_row['card_amount']:
                            touch_sales['card_amount'] = int(touch_row['card_amount'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(touch_sales)

                # 키오스크
                curs.execute(device_name_qry, gls_config.KIOSK)
                kiosk_name_temp = curs.fetchall()
                for row in kiosk_name_temp:
                    kiosk_name = row['name']  # 장비명

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.KIOSK)
                kiosk_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in kiosk_addr:
                    curs.execute(charger_sales_qry, (gls_config.KIOSK, row['addr']))
                    kiosk_res = curs.fetchall()

                    for kiosk_row in kiosk_res:
                        # 값을 저장할 딕셔너리 초기화
                        kiosk_sales = OrderedDict()
                        kiosk_sales['device_addr'] = '0'
                        kiosk_sales['device_name'] = '0'
                        kiosk_sales['device_type'] = gls_config.KIOSK
                        kiosk_sales['charge'] = '0'
                        kiosk_sales['bonus'] = '0'
                        kiosk_sales['card_amount'] = '0'
                        kiosk_sales['card_count'] = '0'
                        kiosk_sales['credit_money'] = '0'
                        kiosk_sales['current_money'] = '0'

                        # 실제 값 저장
                        kiosk_sales['device_addr'] = row['addr']
                        kiosk_sales['device_name'] = kiosk_name
                        kiosk_sales['card_count'] = kiosk_row['card_count']
                        kiosk_sales['credit_money'] = kiosk_row['credit_money']
                        kiosk_sales['current_money'] = kiosk_row['current_money']

                        # 소수점 절삭
                        if kiosk_row['charge']:
                            kiosk_sales['charge'] = int(kiosk_row['charge'])
                        if kiosk_row['bonus']:
                            kiosk_sales['bonus'] = int(kiosk_row['bonus'])
                        if kiosk_row['credit_money']:
                            kiosk_sales['credit_money'] = int(kiosk_row['credit_money'])
                        if kiosk_row['current_money']:
                            kiosk_sales['current_money'] = int(kiosk_row['current_money'])
                        if kiosk_row['card_amount']:
                            kiosk_sales['card_amount'] = int(kiosk_row['card_amount'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(kiosk_sales)
        except Exception as e:
            print("From get_device_sales except : ", e)
        finally:
            conn.close()
        return device_sales_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    8. 메인화면 세차장비 매출
    today 함수로 금일 날짜를 구하여 gl_sales_list(View)에서 날짜로 세차장비의 매출을
    검색하여 반환함
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_today_device_sales(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 오늘 날짜 구하기
                today = datetime.today().strftime('%Y-%m-%d')

                # 금일 세차 장비 사용 내역
                get_days_total_q = "SELECT `device_name`, `device_addr`, `card_num`, `time`, " \
                                   "`cash` * 100 AS 'cash', `card` * 100 AS 'card', `master_card` AS 'master', " \
                                   "`remain_card` * 100 AS 'remain_card', " \
                                   "UNIX_TIMESTAMP(`end_time`) AS 'end_time' " \
                                   " FROM gl_sales_list WHERE `end_time` " \
                                   " LIKE '%%" + today + "%%' " \
                                   " AND (`device_type` = %s or `device_type` = %s" \
                                   " or `device_type` = %s or `device_type` = %s or `device_type` = %s)" \
                                   " ORDER BY `end_time` DESC"
                curs.execute(get_days_total_q, (gls_config.SELF, gls_config.AIR, gls_config.MATE, gls_config.READER, gls_config.GARAGE))
                res = curs.fetchall()

                for row in res:
                    # 0원에 대한 처리
                    if row['cash'] == 0.0:
                        row['cash'] = 0
                    if row['card'] == 0.0:
                        row['card'] = 0
                    if row['remain_card'] == 0.0:
                        row['remain_card'] = 0
                    if row['master'] == 0.0:
                        row['master'] = 0

                    # 소수점 절삭
                    if row['cash']:
                        row['cash'] = int(row['cash'])
                    if row['card']:
                        row['card'] = int(row['card'])
                    if row['remain_card']:
                        row['remain_card'] = int(row['remain_card'])
                    if row['master']:
                        row['master'] = int(row['master'])
        except Exception as e:
            print("From get_today_device_sa0les except : ", e)
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    9. 메인화면 충전장비 매출
    gl_charger_state / gl_device_list / gl_device_info 
    위의 3개의 테이블을 조인하고 today 함수로 금일 날짜를 구하여 매출을 검색 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_today_charger_sales(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 오늘 날짜 구하기
                today = datetime.today().strftime('%Y-%m-%d')

                # 금일 충전 장비 사용 내역
                get_days_total_q = "SELECT d_info.`device_name` AS 'device_name', d_list.`addr` AS 'device_addr', " \
                                   "charger.`card_num` AS 'card_num', charger.`current_money` * 100 AS 'money', " \
                                   "charger.`current_bonus` * 100 AS 'bonus', " \
                                   "charger.`current_charge` * 100 AS 'charge', " \
                                   "charger.`total_money` * 100 As 'remain_card', " \
                                   "charger.`current_credit_money` * 100 AS 'credit_money', " \
                                   "UNIX_TIMESTAMP(charger.`input_date`) AS 'input_date' " \
                                   "FROM gl_charger_state AS charger " \
                                   "INNER JOIN gl_device_list AS d_list ON charger.`device_no` = d_list.`no` " \
                                   "INNER JOIN gl_device_info AS d_info ON d_list.`type` = d_info.`type` " \
                                   "WHERE charger.`input_date`" \
                                   " LIKE '%%" + today + "%%' " \
                                                         " ORDER BY `input_date` DESC"
                curs.execute(get_days_total_q)
                res = curs.fetchall()

                for row in res:
                    # 0원에 대한 처리
                    if row['money'] == 0.0:
                        row['money'] = 0
                    if row['credit_money'] == 0.0:
                        row['credit_money'] = 0
                    if row['charge'] == 0.0:
                        row['charge'] = 0
                    if row['bonus'] == 0.0:
                        row['bonus'] = 0
                    if row['remain_card'] == 0.0:
                        row['remain_card'] = 0

                    # 소수점 절삭
                    if row['money']:
                        row['money'] = int(row['money'])
                    if row['credit_money']:
                        row['credit_money'] = int(row['credit_money'])
                    if row['charge']:
                        row['charge'] = int(row['charge'])
                    if row['bonus']:
                        row['bonus'] = int(row['bonus'])
                    if row['remain_card']:
                        row['remain_card'] = int(row['remain_card'])
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    10. 메인화면 매출 총계
    gl_sales_list(View)에서 현금 / 카드 매출을 구하고
    gl_charger_state 에서 카드 충전을 구함.
    매출 합계 -> 현금 매출 + 카드 매출
    수입 함계 -> 현금 매출 + 카드 충전
    * 참고 : 카드 충전 -> 투입금액 - 배출금액
    * 변경 : 카드 충전 -> 투입금액
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_today_sales_total(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 오늘 날짜 구하기
                today = datetime.today().strftime('%Y-%m-%d')

                # 저장 딕셔너리 선언 및 초기화
                total = OrderedDict()
                total['sales'] = '0'  # 매출 합계
                total['income'] = '0'  # 수입 합계
                total['cash_sales'] = '0'  # 현금 매출
                total['card_sales'] = '0'  # 카드 매출
                total['card_charge'] = '0'  # 카드 충전

                # 현금 매출 / 카드 매출
                get_today_sales_q = "SELECT SUM(`cash`) * 100 AS 'cash_sales', " \
                                    "SUM(`card`) * 100 AS 'card_sales' " \
                                    " FROM gl_sales_list WHERE `end_time` " \
                                    " LIKE '%%" + today + "%%' " \
                                                          " AND (`device_type` = %s or `device_type` = %s" \
                                                          " or `device_type` = %s or `device_type` = %s or `device_type` = %s)"
                curs.execute(get_today_sales_q, (gls_config.SELF, gls_config.AIR, gls_config.MATE, gls_config.READER, gls_config.GARAGE))
                res = curs.fetchall()

                for row in res:
                    # 0원에 대한 처리
                    if row['cash_sales'] is None:
                        row['cash_sales'] = 0
                    if row['card_sales'] is None:
                        row['card_sales'] = 0

                    # 소수점 절삭 및 매출 저장
                    if row['cash_sales']:
                        total['cash_sales'] = int(row['cash_sales'])
                    if row['card_sales']:
                        total['card_sales'] = int(row['card_sales'])

                # 카드 충전
                get_today_sales_q = "SELECT SUM(`current_money`) * 100 AS 'current_money', " \
                                    "SUM(`current_credit_money`) * 100 AS 'current_credit_money' " \
                                    " FROM gl_charger_state WHERE `input_date` " \
                                    " LIKE '%%" + today + "%%' "
                curs.execute(get_today_sales_q)
                res = curs.fetchall()

                for row in res:
                    # 0원에 대한 처리
                    if row['current_money'] is None:
                        row['current_money'] = 0
                    if row['current_credit_money'] is None:
                        row['current_credit_money'] = 0

                    # 카드 충전액 저장
                    # total['card_charge'] = int(row['current_money']) - int(row['exhaust_money'])
                    total['card_charge'] = int(row['current_money']) + int(row['current_credit_money'])

                total['sales'] = int(total['cash_sales']) + int(total['card_sales'])
                total['income'] = int(total['cash_sales']) + int(total['card_charge'])

        except Exception as e:
            print("From get_today_sales_total except : ", e)
        finally:
            conn.close()

        return total

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    11. 장비 이력 조회
    get_device_sales를 기반으로 작성된 함수 날짜 조건이 없이 전체 이력을 가져오며,
    충전장비의 경우 리스트외에 별도로 표시될 내용이 없는 관계로 딕셔너리를 0으로
    초기화하여 값을 전달함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_use_device(self):
        device_sales_list = []  # 반환 값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 장비 이름 추출
        device_name_qry = "SELECT `device_name` AS 'name' FROM gl_device_info WHERE `type` = %s"

        # 장비 번호 카운트
        device_addr_qry = "SELECT `addr` FROM gl_device_list WHERE `type` = %s ORDER BY `addr` ASC"

        # 충전 장비 이력 조회 쿼리
        # get_use_device_qry = "SELECT SUM(`cash`) * 100 AS 'cash', SUM(`card`) * 100 AS 'card', `device_type`, " \
        #                      " SUM(`time`) AS 'time', SUM(`master_card`) * 100 AS 'master'" \
        #                      " FROM gl_sales_list " \
        #                      " WHERE `device_type` = %s " \
        #                      " AND `device_addr` = %s "
        get_use_device_qry = "SELECT d_list.addr AS 'device_addr', sum(charger.current_charge) * 100 AS 'cash', " \
                             "sum(charger.exhaust_money) * 100 AS 'master' " \
                             "FROM gl_charger_state AS charger " \
                             "INNER JOIN gl_device_list AS d_list " \
                             "ON charger.device_no = d_list.`no`" \
                             "WHERE d_list.type = %s and d_list.addr = %s"

        try:
            with conn.cursor():
                # 셀프
                # 장비명
                curs.execute(device_name_qry, gls_config.SELF)
                # self_name_temp = curs.fetchall()
                self_name_temp = curs.fetchone()

                self_name = self_name_temp['name']
                # for row in self_name_temp:
                #     self_name = row['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.SELF)
                self_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in self_addr:

                    # 셀프 매출 추출
                    get_self_qry = "SELECT self.`device_addr`, sum(self.`use_cash`) * 100 AS 'cash', " \
                                   "sum(self.`use_card`) * 100 AS 'card', " \
                                   "sum(self.`master_card`) * 100 AS 'master' " \
                                   "FROM gl_self_state AS self WHERE self.device_addr = %s"

                    curs.execute(get_self_qry, row['addr'])
                    self_res = curs.fetchall()

                    for self_row in self_res:
                        # 값을 저장할 딕셔너리 초기화
                        self_sales = OrderedDict()
                        self_sales['device_addr'] = '0'
                        self_sales['device_name'] = '0'
                        self_sales['device_type'] = gls_config.SELF
                        self_sales['time'] = '0'
                        self_sales['cash'] = '0'
                        self_sales['card'] = '0'

                        # 실제 값 저장
                        self_sales['device_addr'] = row['addr']
                        self_sales['device_name'] = self_name

                        # 소수점 절삭
                        if self_row['cash']:
                            self_sales['cash'] = int(self_row['cash'])
                        if self_row['card']:
                            self_sales['card'] = int(self_row['card'])
                        if self_row['master']:
                            self_sales['master'] = int(self_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(self_sales)

                # 진공
                # 장비명
                curs.execute(device_name_qry, gls_config.AIR)
                air_name_temp = curs.fetchone()

                air_name = air_name_temp['name']
                # for row in air_name_temp:
                #     air_name = row['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.AIR)
                air_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in air_addr:

                    get_air_ary = "SELECT air.`device_addr`, sum(air.`air_cash`) * 100 AS 'cash', " \
                                  "sum(air.`air_card`) * 100 AS 'card', " \
                                  "sum(air.`master_card`) * 100 AS 'master' " \
                                  "FROM gl_air_state AS air WHERE air.device_addr = %s"

                    curs.execute(get_air_ary, row['addr'])
                    air_res = curs.fetchall()

                    for air_row in air_res:
                        # 값을 저장할 딕셔너리 초기화
                        air_sales = OrderedDict()
                        air_sales['device_addr'] = '0'
                        air_sales['device_name'] = '0'
                        air_sales['device_type'] = gls_config.AIR
                        air_sales['time'] = '0'
                        air_sales['cash'] = '0'
                        air_sales['card'] = '0'

                        # 실제 값 저장
                        air_sales['device_addr'] = row['addr']
                        air_sales['device_name'] = air_name

                        # 소수점 절삭
                        if air_row['cash']:
                            air_sales['cash'] = int(air_row['cash'])
                        if air_row['card']:
                            air_sales['card'] = int(air_row['card'])
                        if air_row['master']:
                            air_sales['master'] = int(air_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(air_sales)

                # 매트
                # 장비명
                curs.execute(device_name_qry, gls_config.MATE)
                mate_name_temp = curs.fetchone()

                # for row in mate_name_temp:
                #     mate_name = row['name']
                mate_name = mate_name_temp['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.MATE)
                mate_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in mate_addr:

                    get_mate_ary = "SELECT mate.`device_addr`, sum(mate.`mate_cash`) * 100 AS 'cash', " \
                                  "sum(mate.`mate_card`) * 100 AS 'card', " \
                                  "sum(mate.`master_card`) * 100 AS 'master' " \
                                  "FROM gl_mate_state AS mate WHERE mate.device_addr = %s"

                    curs.execute(get_mate_ary, row['addr'])
                    mate_res = curs.fetchall()

                    for mate_row in mate_res:
                        # 값을 저장할 딕셔너리 초기화
                        mate_sales = OrderedDict()
                        mate_sales['device_addr'] = '0'
                        mate_sales['device_name'] = '0'
                        mate_sales['device_type'] = gls_config.MATE
                        mate_sales['time'] = '0'
                        mate_sales['cash'] = '0'
                        mate_sales['card'] = '0'

                        # 실제 값 저장
                        mate_sales['device_addr'] = row['addr']
                        mate_sales['device_name'] = mate_name
                        # 소수점 절삭
                        if mate_row['cash']:
                            mate_sales['cash'] = int(mate_row['cash'])
                        if mate_row['card']:
                            mate_sales['card'] = int(mate_row['card'])
                        if mate_row['master']:
                            mate_sales['master'] = int(mate_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(mate_sales)

                # 매트
                # 장비명
                curs.execute(device_name_qry, gls_config.READER)
                reader_name_temp = curs.fetchone()

                # for row in mate_name_temp:
                #     mate_name = row['name']
                reader_name = reader_name_temp['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.READER)
                reader_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in reader_addr:

                    get_reader_ary = "SELECT reader.`device_addr`, sum(reader.`reader_cash`) * 100 AS 'cash', " \
                                   "sum(reader.`reader_card`) * 100 AS 'card', " \
                                   "sum(reader.`master_card`) * 100 AS 'master' " \
                                   "FROM gl_reader_state AS reader WHERE reader.device_addr = %s"

                    curs.execute(get_reader_ary, row['addr'])
                    reader_res = curs.fetchall()

                    for reader_row in reader_res:
                        # 값을 저장할 딕셔너리 초기화
                        reader_sales = OrderedDict()
                        reader_sales['device_addr'] = '0'
                        reader_sales['device_name'] = '0'
                        reader_sales['device_type'] = gls_config.READER
                        reader_sales['time'] = '0'
                        reader_sales['cash'] = '0'
                        reader_sales['card'] = '0'

                        # 실제 값 저장
                        reader_sales['device_addr'] = row['addr']
                        reader_sales['device_name'] = reader_name
                        # 소수점 절삭
                        if reader_row['cash']:
                            reader_sales['cash'] = int(reader_row['cash'])
                        if reader_row['card']:
                            reader_sales['card'] = int(reader_row['card'])
                        if reader_row['master']:
                            reader_sales['master'] = int(reader_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(reader_sales)

                # Garage
                # 장비명
                curs.execute(device_name_qry, gls_config.GARAGE)
                garage_name_temp = curs.fetchone()

                # for row in garage_name_temp:
                #     garage_name = row['name']
                garage_name = garage_name_temp['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.GARAGE)
                garage_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in garage_addr:

                    get_garage_qry = "SELECT garage.`device_addr`,sum(garage.`use_cash`) * 100 AS 'cash', " \
                                     "sum(garage.`use_card`) * 100 AS 'card', " \
                                     "sum(garage.`use_master`) * 100 AS 'master' " \
                                     "FROM gl_garage_state AS garage WHERE garage.device_addr = %s"

                    curs.execute(get_garage_qry, row['addr'])
                    garage_res = curs.fetchall()

                    for garage_row in garage_res:
                        # 값을 저장할 딕셔너리 초기화
                        garage_sales = OrderedDict()
                        garage_sales['device_addr'] = '0'
                        garage_sales['device_name'] = '0'
                        garage_sales['device_type'] = gls_config.GARAGE
                        garage_sales['time'] = '0'
                        garage_sales['cash'] = '0'
                        garage_sales['card'] = '0'

                        # 실제 값 저장
                        garage_sales['device_addr'] = row['addr']
                        garage_sales['device_name'] = garage_name

                        # 소수점 절삭
                        if garage_row['cash']:
                            garage_sales['cash'] = int(garage_row['cash'])
                        if garage_row['card']:
                            garage_sales['card'] = int(garage_row['card'])
                        if garage_row['master']:
                            garage_sales['master'] = int(garage_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(garage_sales)

                # 충전기
                # 장비명
                curs.execute(device_name_qry, gls_config.CHARGER)
                charger_name_temp = curs.fetchone()

                # for row in charger_name_temp:
                #     charger_name = row['name']
                charger_name = charger_name_temp['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.CHARGER)
                charger_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in charger_addr:

                    curs.execute(get_use_device_qry, (gls_config.CHARGER, row['addr']))
                    charger_res = curs.fetchall()

                    for charger_row in charger_res:
                        # 값을 저장할 딕셔너리 초기화
                        charger_sales = OrderedDict()
                        charger_sales['device_addr'] = row['addr']
                        charger_sales['device_name'] = charger_name
                        charger_sales['device_type'] = gls_config.CHARGER
                        charger_sales['time'] = '0'
                        charger_sales['cash'] = '0'
                        charger_sales['card'] = '0'

                        if charger_row['cash']:
                            charger_sales['cash'] = int(charger_row['cash'])
                        if charger_row['master']:
                            charger_sales['card'] = int(charger_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(charger_sales)

                # 터치
                # 장비명
                curs.execute(device_name_qry, gls_config.TOUCH)
                # touch_name_temp = curs.fetchall()
                touch_name_temp = curs.fetchone()

                # for row in touch_name_temp:
                #     touch_name = row['name']
                touch_name = touch_name_temp['name']
                # 장비 주소
                curs.execute(device_addr_qry, gls_config.TOUCH)
                touch_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in touch_addr:
                    curs.execute(get_use_device_qry, (gls_config.TOUCH, row['addr']))
                    touch_res = curs.fetchall()

                    for touch_row in touch_res:
                        # 값을 저장할 딕셔너리 초기화
                        touch_sales = OrderedDict()
                        touch_sales['device_addr'] = row['addr']
                        touch_sales['device_name'] = touch_name
                        touch_sales['device_type'] = gls_config.TOUCH
                        touch_sales['time'] = '0'
                        touch_sales['cash'] = '0'
                        touch_sales['card'] = '0'

                        if touch_row['cash']:
                            touch_sales['cash'] = int(touch_row['cash'])
                        if touch_row['master']:
                            touch_sales['card'] = int(touch_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(touch_sales)

                # Kiosk
                # 장비명
                curs.execute(device_name_qry, gls_config.KIOSK)
                kiosk_name_temp = curs.fetchone()

                # for row in kiosk_name_temp:
                #     kiosk_name = row['name']
                kiosk_name = kiosk_name_temp['name']

                # 장비 주소
                curs.execute(device_addr_qry, gls_config.KIOSK)
                kiosk_addr = curs.fetchall()

                # 장비 주소 별 매출
                for row in kiosk_addr:
                    curs.execute(get_use_device_qry, (gls_config.KIOSK, row['addr']))
                    kiosk_res = curs.fetchall()

                    for kiosk_row in kiosk_res:
                        # 값을 저장할 딕셔너리 초기화
                        kiosk_sales = OrderedDict()
                        kiosk_sales['device_addr'] = row['addr']
                        kiosk_sales['device_name'] = kiosk_name
                        kiosk_sales['device_type'] = gls_config.KIOSK
                        kiosk_sales['time'] = '0'
                        kiosk_sales['cash'] = '0'
                        kiosk_sales['card'] = '0'

                        if kiosk_row['cash']:
                            kiosk_sales['cash'] = int(kiosk_row['cash'])
                        if kiosk_row['master']:
                            kiosk_sales['card'] = int(kiosk_row['master'])

                        # 반환할 리스트에 저장
                        device_sales_list.append(kiosk_sales)
        # except Exception as e:
        #     print("From get_use_device except : ", e)
        finally:
            conn.close()

        return device_sales_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    12. 장비 세부 이력 조회
    포스로부터 장비 타입과 장비 주소를 인자로 넘겨받고, 해당 장비의 사용 이력을
    모두 검색하여 반환함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_use_device_detail(self, type, addr):

        print(type)
        print(addr)
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)
        use_device_detail = []
        try:
            with conn.cursor():
                # 세차장비
                if (type == str(gls_config.SELF) or type == str(gls_config.AIR) or type == str(gls_config.MATE)
                        or type == str(gls_config.READER) or type == str(gls_config.GARAGE)):
                    query = "SELECT UNIX_TIMESTAMP(`start_time`) AS 'start_time', " \
                            "UNIX_TIMESTAMP(`end_time`) AS 'end_time', " \
                            "`time`, `cash` * 100 AS 'cash', `card` * 100 AS 'card', `master_card` AS 'master', " \
                            "`remain_card` * 100 AS 'remain_card', `card_num`, `device_type`, `no` " \
                            "FROM gl_sales_list " \
                            "WHERE `device_type` = %s AND `device_addr` = %s " \
                            "ORDER BY `end_time` DESC"
                    curs.execute(query, (type, addr))
                    res = curs.fetchall()

                    for row in res:
                        temp_dict = OrderedDict()

                        if str(row['device_type']) == str(gls_config.SELF):
                            temp_dict['enable_type'] = self.get_self_detail(row['no'], 'self')
                        elif str(row['device_type']) == str(gls_config.AIR):
                            temp_dict['enable_type'] = '진공'
                        elif str(row['device_type']) == str(gls_config.MATE):
                            temp_dict['enable_type'] = '매트'
                        elif str(row['device_type']) == str(gls_config.READER):
                            temp_dict['enable_type'] = '매트'
                        elif str(row['device_type']) == str(gls_config.GARAGE):
                            temp_dict['enable_type'] = self.get_self_detail(row['no'], 'garage')

                            # 소수점 절삭
                        if row['cash']:
                            temp_dict['cash'] = int(row['cash'])
                        if row['card']:
                            temp_dict['card'] = int(row['card'])
                        if row['remain_card']:
                            temp_dict['remain_card'] = int(row['remain_card'])
                        if row['master']:
                            temp_dict['master'] = int(row['master'])

                        # 0원에 대한 처리
                        if row['cash'] == 0.0:
                            temp_dict['cash'] = 0
                        if row['card'] == 0.0:
                            temp_dict['card'] = 0
                        if row['remain_card'] == 0.0:
                            temp_dict['remain_card'] = 0
                        if row['master'] == 0.0:
                            temp_dict['master'] = 0

                        if row['start_time']:
                            temp_dict['start_time'] = row['start_time']
                        if row['end_time']:
                            temp_dict['end_time'] = row['end_time']
                        if row['time']:
                            temp_dict['time'] = row['time']
                        if row['card_num']:
                            temp_dict['card_num'] = row['card_num']

                        use_device_detail.append(temp_dict)

                # 충전장비
                elif type == str(gls_config.CHARGER) or type == str(gls_config.TOUCH) or type == str(gls_config.KIOSK):
                    query = "SELECT UNIX_TIMESTAMP(`input_date`) AS 'input_date', `kind`, " \
                            "`exhaust_money` * 100 AS 'card_price', " \
                            "`current_money` * 100 AS 'money', `current_bonus` * 100 AS 'bonus', " \
                            "`current_credit_money` * 100 AS 'credit_money', " \
                            "`current_charge` * 100 AS 'charge', `total_money` * 100 AS 'remain_card', " \
                            "`card_num` FROM gl_charger_state AS charger " \
                            "INNER JOIN gl_device_list AS d_list " \
                            "ON charger.device_no = d_list.`no`" \
                            "WHERE d_list.`type` = %s AND d_list.`addr` = %s"
                    curs.execute(query, (type, addr))
                    res = curs.fetchall()

                    for row in res:

                        temp_dict = OrderedDict()
                        temp_dict['enable_type'] = ' - '

                        if row['input_date']:
                            temp_dict['input_date'] = row['input_date']
                        if row['card_num']:
                            temp_dict['card_num'] = row['card_num']

                        # 소수점 절삭
                        if row['card_price']:
                            temp_dict['card_price'] = int(row['card_price'])
                        if row['money']:
                            temp_dict['money'] = int(row['money'])
                        if row['credit_money']:
                            temp_dict['credit_money'] = int(row['credit_money'])
                        if row['bonus']:
                            temp_dict['bonus'] = int(row['bonus'])
                        if row['charge']:
                            temp_dict['charge'] = int(row['charge'])
                        if row['remain_card']:
                            temp_dict['remain_card'] = int(row['remain_card'])

                        # 0원에 대한 처리
                        if row['card_price'] == 0.0:
                            temp_dict['card_price'] = 0
                        if row['money'] == 0.0:
                            temp_dict['money'] = 0
                        if row['credit_money'] == 0.0:
                            temp_dict['credit_money'] = 0
                        if row['bonus'] == 0.0:
                            temp_dict['bonus'] = 0
                        if row['charge'] == 0.0:
                            temp_dict['charge'] = 0
                        if row['remain_card'] == 0.0:
                            temp_dict['remain_card'] = 0

                        # 발급여부
                        if row['kind'] == '0':
                            temp_dict['kind'] = "발급"
                        elif row['kind'] == '1':
                            temp_dict['kind'] = "충전"

                        use_device_detail.append(temp_dict)

        except Exception as e:
            print("From get_use_device_detail except : ", e)
        finally:
            conn.close()

        return use_device_detail

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    13. 카드 등록
    포스로부터 카드번호를 인자로 넘겨받아 gl_card 테이블에 현재 시간으로 등록함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_card(self, card_num):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        res = '1'  # 성공 반환 값

        # 등록일자
        input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with conn.cursor():
                query = "INSERT INTO gl_card(`card_num`, `input_date`) VALUES (%s, %s)"
                curs.execute(query, (card_num, input_date))
                conn.commit()
        except Exception as e:
            print("From set_card except : ", e)
            res = '0'
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    14. 카드 정보 읽기
    포스로부터 카드번호를 인자로 넘겨받아
    해당 카드의 소지자, 마지막 사용일자, 카드 검증 값(사용/ 사용불가)를 반환
    * 참고 : 카드 검증은 gl_card 테이블에 등록되지 않은 카드이거나 정지카드에 
             등록된 경우 사용 불가 카드로 처리한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def read_card(self, card_num):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)

        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 저장 딕셔너리 초기화
        tempdict = OrderedDict()
        tempdict['name'] = ''  # 회원명
        tempdict['verification'] = ''  # 카드 검증 (사용/ 사용불가)
        tempdict['last_date'] = ''  # 최근 사용일자

        card_data = []  # 반환 값

        try:
            with conn.cursor():
                # 회원 이름 조회
                get_name_qry = "SELECT mb.`name` AS 'name' FROM gl_member_card AS mb_card " \
                               "INNER JOIN gl_member AS mb " \
                               "ON mb_card.`mb_no` = mb.`no` " \
                               "where mb_card.num = %s"
                curs.execute(get_name_qry, card_num)
                name_res = curs.fetchall()

                for name in name_res:
                    if name['name']:
                        tempdict['name'] = name['name']
                    else:
                        tempdict['name'] = ""

                # 사용 검증
                # 등록 카드 검사
                get_card = "SELECT `card_num` FROM gl_card WHERE `card_num` = %s"
                curs.execute(get_card, card_num)
                get_card_res = curs.fetchall()

                # 카드가 존재하지 않으면 사용불가 카드로 처리
                if get_card_res:
                    registration = '1'
                else:
                    registration = '0'
                    tempdict['verification'] = '0'

                # 정지 카드 여부 검사
                get_card_verification = "SELECT count(*) AS 'verification' FROM gl_card_blacklist " \
                                        "WHERE `card_num` = %s"
                curs.execute(get_card_verification, card_num)
                verification_res = curs.fetchall()

                for verification in verification_res:
                    # 등록된 카드이고 정지 카드 리스트에 없으면 사용 가능 카드로 처리
                    if verification['verification'] == 0 and registration == '1':
                        tempdict['verification'] = '1'
                    # 정지 카드에 있으면 사용불가처리
                    else:
                        tempdict['verification'] = '0'

                # 최근 사용일
                get_last_qry = "SELECT `end_time` AS 'last_date' FROM gl_sales_list WHERE `card_num` = %s " \
                               "ORDER BY `end_time` DESC LIMIT 1 "
                curs.execute(get_last_qry, card_num)
                last_res = curs.fetchall()

                for last in last_res:
                    if last['last_date']:
                        tempdict['last_date'] = str(last['last_date'])
                    else:
                        tempdict['last_date'] = ""

                # 반환 배열에 저장
                card_data.append(tempdict)
        except Exception as e:
            print("From read_card except : ", e)
        finally:
            conn.close()

        return card_data

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    15. 카드 이력 조회
    전체 카드의 카드번호, 발급일자, 누적충전금액, 현재 잔액, 최근사용일자, 회원코드를
    반환함. 필드에 값이 존재하지 않을 경우 '0'으로 처리
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_card_history(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 이력 조회 쿼리
                query = "SELECT card.`card_num`, UNIX_TIMESTAMP(card.`input_date`) AS 'input_date', " \
                        "IFNULL((select `mb_no` FROM gl_member_card WHERE `num` = card.card_num ORDER BY `input_date` DESC LIMIT 1), 0) AS 'mb_no'" \
                        "FROM gl_card as card WHERE NOT card.card_num in('00000000') ORDER BY input_date DESC"
                curs.execute(query)
                card_history = curs.fetchall()

        except Exception as e:
            print("From get_card_history except : ", e)
        finally:
            conn.close()

        return card_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    16. 카드 상세 조회
    포스로부터 카드번호를 넘겨 받아 해당 카드의 이력을 반환한다.
    사용일자 / 장비주소 / 장비명 / 충전금액 / 보너스 금액 / 사용금액 / 카드잔액
    세차장비의 경우 충전금액과 보너스는 '0'으로 처리되며
    충전장비의 경우 사용금액은 '0'으로 처리됨
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_card_history_detail(self, card_num):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        card_history = []  # 반환 값

        try:
            with conn.cursor():
                query = "SELECT `device_type`, `end_time`, `cash` * 100 AS 'charge', `card` * 100 AS 'bonus', " \
                        "`device_addr`, `device_name`, `remain_card` * 100 AS 'remain_card', " \
                        "(`cash` * 100) + (`card` * 100) AS 'use' , `no` " \
                        "FROM gl_sales_list WHERE 	card_num = %s"
                curs.execute(query, card_num)
                res = curs.fetchall()

                for row in res:
                    # 임시 저장 딕셔너리
                    temp_history = OrderedDict()
                    temp_history['time'] = str(row['end_time'])  # 사용일자
                    temp_history['device_addr'] = row['device_addr']  # 장비 주소
                    temp_history['device_name'] = row['device_name']  # 장비명
                    temp_history['charge'] = '0'  # 충전 금액
                    temp_history['bonus'] = '0'  # 보너스 금액
                    temp_history['use'] = '0'  # 사용금액
                    temp_history['remain_card'] = '0'  # 카드잔액

                    # 세부 사용 내역
                    if str(row['device_type']) == str(gls_config.SELF):
                        temp_history['enable_type'] = self.get_self_detail(row['no'], 'self')
                    elif str(row['device_type']) == str(gls_config.AIR):
                        temp_history['enable_type'] = '진공'
                    elif str(row['device_type']) == str(gls_config.MATE):
                        temp_history['enable_type'] = '매트'
                    elif str(row['device_type']) == str(gls_config.READER):
                        temp_history['enable_type'] = '매트'
                    elif str(row['device_type']) == str(gls_config.GARAGE):
                        temp_history['enable_type'] = self.get_self_detail(row['no'], 'garage')
                    else:
                        temp_history['enable_type'] = '-'

                    # 충전 장비의 경우
                    if row['device_type'] == '3' or row['device_type'] == '6' or row['device_type'] == '7' or row['device_type'] == '8':
                        if row['charge']:
                            temp_history['charge'] = int(row['charge'])
                        if row['bonus']:
                            temp_history['bonus'] = int(row['bonus'])
                        if row['remain_card']:
                            temp_history['remain_card'] = int(row['remain_card'])
                    # 세차 장비의 경우
                    else:
                        if row['use']:
                            temp_history['use'] = int(row['use'])
                        if row['remain_card']:
                            temp_history['remain_card'] = int(row['remain_card'])

                    # 반환 배열에 저장
                    card_history.append(temp_history)
        except Exception as e:
            print("From get_card_history_detail except : ", e)
        finally:
            conn.close()

        return card_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    17. 정지 카드 조회
    정지 카드의 리스트를 반환
    * 참고 : index 번호도 같이 반환함으로써 추후 수정 및 삭제의 키 값으로 사용
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_black_card(self):
        # 데이터베이스 접속 정보
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        black_card_list = []  # 반환 값

        try:
            with conn.cursor():
                query = "SELECT `no`, `card_num`, `content`, DATE_FORMAT(`input_date`, '%Y-%m-%d') AS 'input_date' " \
                        "FROM gl_card_blacklist"
                curs.execute(query)
                res = curs.fetchall()

                for row in res:
                    temp = OrderedDict()
                    temp['no'] = row['no']  # index
                    temp['card_num'] = row['card_num']  # 정지 카드 번호
                    temp['content'] = row['content']  # 정지 사유
                    temp['input_date'] = str(row['input_date'])  # 등록일자

                    black_card_list.append(temp)
        except Exception as e:
            print("From get_black_card except : ", e)
        finally:
            conn.close()

        return black_card_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    18. 정지 카드 등록
    포스로부터 정지카드번호와 정지사유를 인자로 넘겨받아 테이블에 저장
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_black_card(self, card_num, content):
        # 데이터베이스 접속 정보
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        res = '1'  # 반환 값

        # 등록일자
        input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with conn.cursor():
                query = "INSERT INTO gl_card_blacklist(`card_num`, `content`, `input_date`) VALUES (%s, %s, %s)"
                curs.execute(query, (card_num, content, input_date))
                conn.commit()
        except Exception as e:
            print("From set_black_card except: ", e)
            res = '0'
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    19. 정지 카드 해제
    정지카드의 테이블 index 번호를 넘겨 받아 테이블에서 삭제
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def delete_black_card(self, no):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        res = '1'  # 성공 반환 값

        try:
            with conn.cursor():
                query = "DELETE FROM gl_card_blacklist WHERE `no` = %s"
                curs.execute(query, no)
                conn.commit()
        except Exception as e:
            print("From delete_black_card except : ", e)
            res = 0
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    20. 회원 목록 조회
    gl_member 테이블에서 회원번호, 회원명, 휴대폰, 차량 정보를 검색 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_list(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                query = "SELECT `mb`.`no` AS 'mb_no' , `mb`.`name`, `mb`.`mobile`, `mb`.`car_num`, `card`.`num` AS 'card_num' " \
                        "FROM gl_member AS `mb` " \
                        "INNER JOIN gl_member_card AS `card` ON `mb`.`no` = `card`.`mb_no`"
                curs.execute(query)
                res = curs.fetchall()
        except Exception as e:
            print("From get_member_list except : ", e)
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    21. 회원 레벨 조회
    gl_member_level 테이블에서 등급, 등급명을 검색 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_level(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                query = "SELECT `level`, `level_name` FROM gl_member_level"
                curs.execute(query)
                res = curs.fetchall()
        except Exception as e:
            print("From get_member_level except : ", e)
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    22. 회원 정보 조회
    gl_member_card 를 검색하여 카드 단일 소지 / 다중 소지 / 미소지에 따라 
    작업을 실시하며 다중 카드 소지자의 경우 A카드^B카드^C카드 "^"를 구분 플래그로 
    사용하여 카드 값을 반환하고, 미소지자의 경우 공백을 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_detail(self, mb_no):
        # 데이터베이스 접속 정보
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        mb_data = OrderedDict()  # 저장 딕셔너리
        try:
            with conn.cursor():
                # 다중 카드 사용자 추출
                count_query = "SELECT COUNT(*) AS 'count' FROM gl_member AS mb " \
                              "INNER JOIN gl_member_card AS mb_card " \
                              "ON mb.`no` = mb_card.`mb_no` " \
                              "WHERE `mb_no` = %s"
                curs.execute(count_query, mb_no)
                res = curs.fetchall()

                for row in res:
                    count = row['count']
                # 다중 카드 사용자의 경우
                if count > 1:
                    mb_query = "SELECT `no` AS 'mb_no', mb.`level`, `name`, `birth`, `mobile`, `car_num`, `addr`, " \
                               "`group`, `input_date`, `vip_set`, mb_level.`level_name` " \
                               "FROM gl_member AS mb " \
                               "INNER JOIN gl_member_level AS mb_level ON mb.`level` = mb_level.`level` WHERE `no` = %s"
                    curs.execute(mb_query, mb_no)
                    mb = curs.fetchall()

                    # 기본 정보 저장
                    for row in mb:
                        mb_data['mb_no'] = row['mb_no']  # 회원 코드
                        mb_data['level'] = row['level']  # 회원 레벨
                        mb_data['name'] = row['name']  # 회원명
                        mb_data['birth'] = str(row['birth'])  # 생년월일 (yyyy-mm-dd)
                        mb_data['mobile'] = row['mobile']  # 연락처
                        mb_data['car_num'] = row['car_num']  # 차량 정보
                        mb_data['addr'] = row['addr']  # 주소
                        mb_data['group'] = row['group']  # 회원 그룹
                        mb_data['input_date'] = str(row['input_date'])  # 등록일자
                        mb_data['vip_set'] = row['vip_set']  # 우수회원 갱신 여부
                        mb_data['level_name'] = row['level_name']  # 회원 등급

                    # 다중 카드 정보 저장
                    card_query = "SELECT `num` AS 'card_num' FROM gl_member AS mb " \
                                 "INNER JOIN gl_member_card AS card " \
                                 "ON mb.`no` = card.`mb_no` " \
                                 "WHERE `mb_no` = %s"
                    curs.execute(card_query, mb_no)
                    card = curs.fetchall()
                    last_count = 0

                    # 카드 정보 저장 (카드 구분 플래그 -> ^ )
                    for row in card:
                        last_count = last_count + 1
                        if last_count == 1:
                            card_num = row['card_num'] + "^"
                        elif last_count == count:
                            card_num = card_num + row['card_num']
                        else:
                            card_num = card_num + row['card_num'] + "^"

                    mb_data['card_num'] = card_num
                # 카드 미소지자
                elif count == 0:
                    not_card = "SELECT `no` AS 'mb_no', mb.`level`, `name`, `birth`, `mobile`, `car_num`, `addr`, " \
                               "`group`, `input_date`, `vip_set`, mb_level.`level_name` " \
                               "FROM gl_member AS mb " \
                               "INNER JOIN gl_member_level AS mb_level ON mb.`level` = mb_level.`level` " \
                               "WHERE `no` = %s"
                    curs.execute(not_card, mb_no)
                    mb = curs.fetchall()

                    # 기본 정보 저장
                    for row in mb:
                        mb_data['mb_no'] = row['mb_no']  # 회원 코드
                        mb_data['level'] = row['level']  # 회원 레벨
                        mb_data['name'] = row['name']  # 회원명
                        mb_data['birth'] = str(row['birth'])  # 생년월일 (yyyy-mm-dd)
                        mb_data['mobile'] = row['mobile']  # 연락처
                        mb_data['car_num'] = row['car_num']  # 차량 정보
                        mb_data['addr'] = row['addr']  # 주소
                        mb_data['group'] = row['group']  # 회원 그룹
                        mb_data['input_date'] = str(row['input_date'])  # 등록일자
                        mb_data['vip_set'] = row['vip_set']  # 우수회원 갱신 여부
                        mb_data['level_name'] = row['level_name']  # 회원 등급
                    mb_data['card_num'] = ""
                # 단일 카드 사용자
                else:
                    mb_data_qry = "SELECT `no` AS 'mb_no', mb.`level`, `name`, `birth`, `mobile`, `car_num`, `addr`, " \
                                  "`group`, mb.`input_date` AS 'input_date', `num` AS 'card_num', `vip_set`, mb_level.`level_name` " \
                                  "FROM gl_member AS mb " \
                                  "INNER JOIN gl_member_card AS card " \
                                  "ON mb.`no` = card.`mb_no` " \
                                  "INNER JOIN gl_member_level AS mb_level " \
                                  "ON mb.`level` = mb_level.`level`" \
                                  "WHERE mb_no = %s"
                    curs.execute(mb_data_qry, mb_no)
                    temp = curs.fetchall()

                    for row in temp:
                        mb_data['mb_no'] = row['mb_no']  # 회원 코드
                        mb_data['level'] = row['level']  # 회원 레벨
                        mb_data['name'] = row['name']  # 회원명
                        mb_data['birth'] = str(row['birth'])  # 생년월일 (yyyy-mm-dd)
                        mb_data['mobile'] = row['mobile']  # 연락처
                        mb_data['car_num'] = row['car_num']  # 차량 정보
                        mb_data['addr'] = row['addr']  # 주소
                        mb_data['group'] = row['group']  # 회원 그룹
                        mb_data['input_date'] = str(row['input_date'])  # 등록일자
                        mb_data['card_num'] = row['card_num']  # 카드 번호
                        mb_data['vip_set'] = row['vip_set']  # 우수회원 갱신 여부
                        mb_data['level_name'] = row['level_name']  # 회원 등급
        # except Exception as e:
        #     print("From get_member_detail except : ", e)
        finally:
            conn.close()

        return mb_data

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    23. 회원 등록 및 수정
    회원 코드가 '0'이면 회원 등록, 회원 코드가 존재하면 회원 수정으로 간주한다.
    등록 및 수정 모두 단일 카드 소지 / 다중 카드 소지 / 카드 미소지를 구분하여
    작업하며 회원 수정에서 다중 카드를 소지한 경우 기존의 소지한 카드를 일괄 삭제 후
    재 등록함.
    ( 'A카드', 'B카드'에서 'B카드', 'C카드', 'D카드'와 같이 수정할 경우 'B카드'에 
      대한 원활한 처리를 위한 방법임.)
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_member(self, args):

        res = 1  # 반환값 (성공유무)

        # POST 데이터 파싱
        no = args['no']  # 회원 코드
        level = args['level']  # 회원 레벨
        name = args['name']  # 회원명
        birth = args['birth']  # 생년월일
        mobile = args['mobile']  # 연락처
        car_num = args['car_num']  # 차량 정보
        addr = args['addr']  # 주소
        group = args['group']  # 그룹 번호
        vip_set = args['vip_set']  # 우수회원 갱신 여부
        card_num = str(args['card_num'])  # 카드 번호
        multi_card = card_num.count('^')  # 다중 카드 수량
        multi_card_data = card_num.split('^')  # 다중 카드 정보

        # 등록 일자
        input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 회원 등록
                if no == '0':
                    insert_query = "INSERT INTO gl_member(`level`, `group`, `name`, `birth`, `mobile`, `addr`, " \
                                   "`car_num`, `input_date`, `vip_set`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    curs.execute(insert_query, (level, group, name, birth, mobile, addr, car_num, input_date, vip_set))
                    conn.commit()
                    # 카드 소지자의 경우
                    if card_num != '':
                        # 회원 등록 번호 검색
                        mb_no_qry = "SELECT `no` FROM gl_member WHERE `level` = %s AND `group` = %s AND `name` = %s " \
                                    "AND `birth` = %s AND `mobile` = %s AND `addr` = %s AND `car_num` = %s"
                        curs.execute(mb_no_qry, (level, group, name, birth, mobile, addr, car_num))
                        mb_no_res = curs.fetchall()

                        for row in mb_no_res:
                            mb_no = row['no']

                        # 카드 등록 쿼리
                        card_insert_qry = "INSERT INTO gl_member_card(`num`, `mb_no`, `input_date`) " \
                                          "VALUES (%s, %s, %s )"

                        if multi_card == 0:
                            # 단일 카드 등록
                            curs.execute(card_insert_qry, (card_num, mb_no, input_date))
                            conn.commit()
                        else:
                            # 다중 카드 등록
                            card = card_num.split('^')

                            for row in card:
                                curs.execute(card_insert_qry, (row, mb_no, input_date))
                                conn.commit()
                # 회원 업데이트
                elif no != '0':
                    # 회원 정보 업데이트
                    update_query = "UPDATE gl_member SET `level` = %s, `group` = %s, `name` = %s, `birth` = %s, " \
                                   "`mobile` = %s, `addr` = %s, `car_num` = %s, `input_date` = %s, `vip_set` = %s " \
                                   "WHERE `no` = %s"
                    curs.execute(update_query, (level, group, name, birth, mobile, addr, car_num, input_date, vip_set, no))
                    conn.commit()

                    # 등록된 카드를 지우는 경우
                    if card_num == '':
                        card_delete = "DELETE FROM gl_member_card WHERE `mb_no` = %s"
                        curs.execute(card_delete, no)
                        conn.commit()
                    # 카드 소지자의 경우
                    elif card_num != '':
                        # 회원 카드 정보 조회
                        count_card = "SELECT count(*) AS 'count' FROM gl_member_card WHERE `mb_no` = %s"
                        curs.execute(count_card, no)
                        count_row = curs.fetchall()

                        for row in count_row:
                            card_count = row['count']

                        if card_count != 0:
                            if multi_card == 0:
                                # 회원 단일 카드 정보 업데이트
                                update_card_qry = "UPDATE gl_member_card SET `num` = %s, `input_date` = %s " \
                                                  "WHERE `mb_no` = %s"
                                curs.execute(update_card_qry, (card_num, input_date, no))
                                conn.commit()
                            else:
                                # 회원 다중 카드 정보 업데이트
                                # 등록된 카드 삭제
                                before_card_qry = "SELECT `num` FROM gl_member_card WHERE `mb_no` = %s"
                                curs.execute(before_card_qry, no)
                                before_card = curs.fetchall()
                                card_delete = "DELETE FROM gl_member_card WHERE `num` = %s"

                                for before in before_card:
                                    curs.execute(card_delete, before['num'])
                                    conn.commit()

                                # 카드 재 등록
                                card_insert_qry = "INSERT INTO gl_member_card(`num`, `mb_no`, `input_date`) " \
                                                  "VALUES (%s, %s, %s )"

                                for after in multi_card_data:
                                    curs.execute(card_insert_qry, (after, no, input_date))
                                    conn.commit()
                        else:
                            # 회원 카드 신규 등록
                            card_insert_qry = "INSERT INTO gl_member_card(`num`, `mb_no`, `input_date`) " \
                                              "VALUES (%s, %s, %s )"
                            if multi_card == 0:
                                # 단일 카드 등록
                                curs.execute(card_insert_qry, (card_num, no, input_date))
                                conn.commit()
                            else:
                                # 다중 카드 등록
                                card = card_num.split('^')

                                for row in card:
                                    curs.execute(card_insert_qry, (row, no, input_date))
                                    conn.commit()
        except Exception as e:
            print("From set_member except : ", e)
            res = 0
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    24. 회원 삭제
    회원 코드(mb_no)를 받아 gl_member / gl_member_card에서 해당 레코드를 삭제 함
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def delete_member(self, no):
        res = 1  # 반환값 (성공유무)

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 회원 정보 삭제
                delete_mb_qry = "DELETE FROM gl_member WHERE `no` = %s"
                curs.execute(delete_mb_qry, no)
                conn.commit()

                # 회원 카드 정보 삭제
                delete_card_qry = "DELETE FROM gl_member_card WHERE `mb_no` = %s"
                curs.execute(delete_card_qry, no)
                conn.commit()
        except Exception as e:
            print("From delete_member except : ", e)
            res = 0
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    25. 회원 이력
    gl_member 테이블에서 기본 회원 정보를 저장한 이후
    gl_member_card 테이블에서 회원이 카드를 소지하였는지 검사하여 카드가 있을 경우
    gl_charger_state 에서 회원의 카드로 누적 충전금액을 추출하여 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_history(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 회원 검색 쿼리
                get_member_qry = "SELECT `no` AS 'mb_no', `name`, `mobile`, `car_num`, `input_date` FROM gl_member"

                # 회원 카드 검색 쿼리
                get_member_card_qry = "SELECT `num` AS 'card' FROM gl_member_card WHERE `mb_no`= %s"

                # 누적 충전 금액 검색 쿼리
                get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                                       "FROM gl_charger_state WHERE `card_num` = %s"

                # 반환 리스트
                member_history = []

                curs.execute(get_member_qry)
                get_member_list = curs.fetchall()

                for member in get_member_list:
                    # 저장 딕셔너리 선언 및 초기화
                    member_list = OrderedDict()

                    member_list['mb_no'] = member['mb_no']  # 회원 코드
                    member_list['name'] = member['name']  # 회원명
                    member_list['mobile'] = member['mobile']  # 연락처
                    member_list['car_num'] = member['car_num']  # 차량 정보
                    member_list['card_num'] = '0'  # 카드 정보
                    member_list['input_date'] = str(member['input_date'])  # 등록일자

                    # 누적 충전금액 초기화
                    member_list['total_charge'] = '0'

                    # 회원 카드 검색
                    curs.execute(get_member_card_qry, member['mb_no'])
                    mb_card_res = curs.fetchall()

                    for card in mb_card_res:
                        member_list['card_num'] = card['card']
                        # 누적 충전 금액 저장
                        curs.execute(get_total_charge_qry, card['card'])
                        total_charge_res = curs.fetchall()

                        for total_charge in total_charge_res:
                            # 소수점 절삭
                            if total_charge['total_charge']:
                                member_list['total_charge'] = int(total_charge['total_charge'])

                    member_history.append(member_list)
        except Exception as e:
            print("From get_member_history except : ", e)
        finally:
            conn.close()

        return member_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    26. 회원 상세 이력
    포스로부터 회원코드(mb_no)를 받아 회원 카드를 검색하고 해당 카드의 상세 이력을 
    조회하여 반환함.
    세차장비의 경우 충전금액과 보너스는 '0'으로 처리되며
    충전장비의 경우 사용금액은 '0'으로 처리됨
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_history_detail(self, mb_no):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        member_history = []  # 반환 값

        try:
            with conn.cursor():
                # 회원 카드 검색 쿼리
                get_member_card_qry = "SELECT `num` AS 'card' FROM gl_member_card WHERE `mb_no`= %s"

                # 상세 이력 조회
                query = "SELECT `device_type`, `end_time`, `cash` * 100 AS 'charge', `card` * 100 AS 'bonus', " \
                        "`device_addr`, `device_name`, `remain_card` * 100 AS 'remain_card', " \
                        "(`cash` * 100) + (`card` * 100) AS 'use' " \
                        "FROM gl_sales_list WHERE 	card_num = %s ORDER BY `end_time` DESC"
                curs.execute(get_member_card_qry, mb_no)
                card_res = curs.fetchall()

                for card in card_res:
                    curs.execute(query, card['card'])
                    res = curs.fetchall()

                    for row in res:
                        # 임시 저장 딕셔너리 초기화
                        temp_history = OrderedDict()
                        temp_history['card'] = card['card']  # 사용 카드 번호
                        temp_history['time'] = str(row['end_time'])  # 사용 시간
                        temp_history['device_addr'] = row['device_addr']  # 장비 주소
                        temp_history['device_name'] = row['device_name']  # 장비명
                        temp_history['charge'] = '0'  # 충전 금액
                        temp_history['bonus'] = '0'  # 보너스
                        temp_history['use'] = '0'  # 사용금액
                        temp_history['remain_card'] = '0'  # 카드 잔액

                        # 충전 장비의 경우
                        if (row['device_type'] == str(gls_config.CHARGER) or row['device_type'] == str(gls_config.TOUCH)
                                or row['device_type'] == str(gls_config.KIOSK) or row['device_type'] == str(gls_config.POS)):
                            if row['charge']:
                                temp_history['charge'] = int(row['charge'])
                            if row['bonus']:
                                temp_history['bonus'] = int(row['bonus'])
                            if row['remain_card']:
                                temp_history['remain_card'] = int(row['remain_card'])
                        # 세차 장비의 경우
                        else:
                            if row['use']:
                                temp_history['use'] = int(row['use'])
                            if row['remain_card']:
                                temp_history['remain_card'] = int(row['remain_card'])

                        # 반환 배열에 저장
                        member_history.append(temp_history)
        except Exception as e:
            print("From get_member_history_detail except : ", e)
        finally:
            conn.close()

        return member_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    27. 회원 검색
    포스로부터 회원명, 연락처, 카드번호 3개의 인자를 받아 검색 후 반환.
    포스에서 검색창은 한개로 구성되어 있기 때문에 3가지 인자값 중 한개의 인자만
    값이 들어오며 나머지 두개의 인자는 공백으로 받음.
    조건문에서 두개의 인자가 공백일 경우 나머지 인자가 값이 있다고 판단하여
    해당 인자로 검색을 실시함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def search_member(self, name, mobile, car, card):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        member_history = []  # 반환 리스트

        try:
            with conn.cursor():
                # name 검색
                if mobile == "" and car == "" and card == "":
                    # 회원 검색 쿼리
                    get_member_qry = "SELECT `mb`.`no` AS 'mb_no', `mb`.`name`, `mb`.`mobile`, `mb`.`car_num`, `mb`.`input_date`, `card`.`num` AS `card_num` " \
                                     "FROM gl_member  AS `mb` INNER JOIN gl_member_card AS `card` " \
                                     "ON `mb`.`no` = `card`.`mb_no` WHERE `mb`.`name` = %s"
                    curs.execute(get_member_qry, name)
                    get_member_res = curs.fetchall()

                    for member in get_member_res:
                        # 저장 딕셔너리 선언 및 초기화
                        member_list = OrderedDict()
                        member_list['mb_no'] = member['mb_no']  # 회원코드
                        member_list['name'] = member['name']  # 회원명
                        member_list['mobile'] = member['mobile']  # 연락처
                        member_list['car_num'] = member['car_num']  # 차량정보
                        member_list['card_num'] = member['card_num']  # 차량정보
                        member_list['input_date'] = str(member['input_date'])  # 등록일자

                        # 누적 충전금액 초기화
                        member_list['total_charge'] = 0

                        # 회원 카드 검색 쿼리
                        get_member_card_qry = "SELECT `num` AS 'card' FROM gl_member_card WHERE `mb_no`= %s"
                        curs.execute(get_member_card_qry, member['mb_no'])
                        get_card_res = curs.fetchall()

                        for card in get_card_res:
                            # 누적 충전 금액 검색 쿼리
                            get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                                                   "FROM gl_charger_state WHERE `card_num` = %s"
                            curs.execute(get_total_charge_qry, card['card'])
                            total_charge_res = curs.fetchall()

                            for total in total_charge_res:
                                if total['total_charge']:
                                    member_list['total_charge'] = member_list['total_charge'] + int(
                                        total['total_charge'])

                        member_history.append(member_list)
                # mobile 검색
                elif name == "" and car == "" and card == "":
                    # 회원 검색 쿼리
                    get_member_qry = "SELECT `mb`.`no` AS 'mb_no', `mb`.`name`, `mb`.`mobile`, `mb`.`car_num`, `mb`.`input_date`, `card`.`num` AS `card_num` " \
                                     "FROM gl_member  AS `mb` INNER JOIN gl_member_card AS `card` " \
                                     "ON `mb`.`no` = `card`.`mb_no` WHERE `mb`.`mobile` = %s"
                    curs.execute(get_member_qry, mobile)
                    get_member_res = curs.fetchall()

                    for member in get_member_res:
                        # 저장 딕셔너리 선언 및 초기화
                        member_list = OrderedDict()
                        member_list['mb_no'] = member['mb_no']  # 회원코드
                        member_list['name'] = member['name']  # 회원명
                        member_list['mobile'] = member['mobile']  # 연락처
                        member_list['car_num'] = member['car_num']  # 차량정보
                        member_list['card_num'] = member['card_num']  # 차량정보
                        member_list['input_date'] = str(member['input_date'])  # 등록일자

                        # 누적 충전금액 초기화
                        member_list['total_charge'] = 0

                        # 회원 카드 검색 쿼리
                        get_member_card_qry = "SELECT `num` AS 'card' FROM gl_member_card WHERE `mb_no`= %s"
                        curs.execute(get_member_card_qry, member['mb_no'])
                        get_card_res = curs.fetchall()

                        for card in get_card_res:
                            # 누적 충전 금액 검색 쿼리
                            get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                                                   "FROM gl_charger_state WHERE `card_num` = %s"
                            curs.execute(get_total_charge_qry, card['card'])
                            total_charge_res = curs.fetchall()

                            for total in total_charge_res:
                                if total['total_charge']:
                                    member_list['total_charge'] = member_list['total_charge'] + int(
                                        total['total_charge'])

                        member_history.append(member_list)
                # car 검색
                elif name == "" and mobile == "" and card == "":
                    # 회원 검색 쿼리
                    get_member_qry = "SELECT `no` AS 'mb_no', `name`, `mobile`, `car_num`, " \
                                     "mb.`input_date` AS 'input_date', card.`num` AS 'card_num' " \
                                     "FROM gl_member AS mb INNER JOIN gl_member_card AS card " \
                                     "ON mb.`no` = card.`mb_no` WHERE mb.`car_num` = %s"
                    curs.execute(get_member_qry, car)
                    get_member_res = curs.fetchall()

                    for member in get_member_res:
                        # 저장 딕셔너리 선언 및 초기화
                        member_list = OrderedDict()
                        member_list['mb_no'] = member['mb_no']  # 회원코드
                        member_list['name'] = member['name']  # 회원명
                        member_list['mobile'] = member['mobile']  # 연락처
                        member_list['car_num'] = member['car_num']  # 차량정보
                        member_list['card_num'] = member['card_num']  # 차량정보
                        member_list['input_date'] = str(member['input_date'])  # 등록일자

                        # 누적 충전금액 초기화
                        member_list['total_charge'] = 0

                        # 누적 충전 금액 검색 쿼리
                        get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                                               "FROM gl_charger_state WHERE `card_num` LIKE %s"
                        curs.execute(get_total_charge_qry, member['card_num'])
                        total_charge_res = curs.fetchall()

                        for total in total_charge_res:
                            if total['total_charge']:
                                member_list['total_charge'] = member_list['total_charge'] + int(total['total_charge'])

                        member_history.append(member_list)
                # card 검색
                elif name == "" and mobile == "" and car == "":
                    # 회원 검색 쿼리
                    get_member_qry = "SELECT `no` AS 'mb_no', `name`, `mobile`, `car_num`, " \
                                     "mb.`input_date` AS 'input_date', card.`num` AS 'card_num' " \
                                     "FROM gl_member AS mb INNER JOIN gl_member_card AS card " \
                                     "ON mb.`no` = card.`mb_no` WHERE card.`num` = %s"
                    curs.execute(get_member_qry, card)
                    get_member_res = curs.fetchall()

                    for member in get_member_res:
                        # 저장 딕셔너리 선언 및 초기화
                        member_list = OrderedDict()
                        member_list['mb_no'] = member['mb_no']  # 회원코드
                        member_list['name'] = member['name']  # 회원명
                        member_list['mobile'] = member['mobile']  # 연락처
                        member_list['car_num'] = member['car_num']  # 차량정보
                        member_list['card_num'] = member['card_num']  # 차량정보
                        member_list['input_date'] = str(member['input_date'])  # 등록일자

                        # 누적 충전금액 초기화
                        member_list['total_charge'] = 0

                        # 누적 충전 금액 검색 쿼리
                        get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                                               "FROM gl_charger_state WHERE `card_num` LIKE %s"
                        curs.execute(get_total_charge_qry, card)
                        total_charge_res = curs.fetchall()

                        for total in total_charge_res:
                            if total['total_charge']:
                                member_list['total_charge'] = member_list['total_charge'] + int(total['total_charge'])

                        member_history.append(member_list)

        except Exception as e:
            print("From search_member except : ", e)
        finally:
            conn.close()

        return member_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    28. 카드 층전
    카드번호 / 충전금액 / 보너스 / 차감금액 / 사용처 / 매출여부 / 수입여부
    포스로부터 위와 같은 배열을 넘겨 받아 충전을 진행한다.
    현재는 충전 부분만 진행되어 있음.
    추후 가장먼저 차감 부분이 추가 될 예정이며,
    이후 비매출 / 비수입 / 충전 타입(현금/카드) 및 사용처(물품구매) 기능 추가 예정
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_charge(self, args):
        res = '1'  # 반환값

        # 데이터 파싱
        card_num = args['card_num']  # 카드번호
        temp_current_money = args['charge']  # 충전 금액
        temp_current_bonus = args['bonus']  # 보너스
        temp_minus_money = args['minus']  # 차감 금액
        use = args['use']  # 사용처
        sales = args['sales']  # 매출여부
        income = args['income']  # 수입여부

        # 충전 금액
        current_charge = (int(temp_current_money) + int(temp_current_bonus) - int(temp_minus_money)) // 100
        if current_charge < 0:
            current_charge = "-" + str(abs(int(current_charge))).rjust(4, '0')
        else:
            current_charge = str(current_charge).rjust(4, '0')
        # 투입 금액
        current_money = (int(temp_current_money) - int(temp_minus_money)) // 100
        if current_money < 0:
            current_money = "-" + str(abs(int(current_money))).rjust(4, '0')
        else:
            current_money = str(current_money).rjust(4, '0')
        # 보너스
        current_bonus = str(int(temp_current_bonus) // 100).rjust(4, '0')
        # 카드 잔액
        total_money = str(int(args['remain']) // 100).rjust(4, '0')




        # 등록 일자 생성
        input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 포스 deivec_no 추출( 해당 쿼리는 포스가 하나라는 전제조건하에 성립하는 쿼리임.)
                get_device_no_qry = "SELECT `no` FROM gl_device_list WHERE `type` = %s"
                curs.execute(get_device_no_qry, gls_config.POS)
                get_device_no_res = curs.fetchall()

                for get_device_no in get_device_no_res:
                    device_no = get_device_no['no']
                if sales == '0' :
                    # 현금 충전 / 차감
                    charge_query = "INSERT INTO gl_charger_state(`device_no`, `current_money`, `current_bonus`, " \
                                   "`current_charge`, `total_money`, `card_num`, `input_date`) " \
                                   "VALUES(%s, %s, %s, %s, %s, %s, %s)"
                    curs.execute(charge_query, (device_no, current_money, current_bonus, current_charge, total_money,
                                                card_num, input_date))
                    conn.commit()
                    # 신용카드 충전 / 차감
                elif sales == '1' :
                    charge_query = "INSERT INTO gl_charger_state(`device_no`, `current_credit_money`, `current_bonus`, " \
                                   "`current_charge`, `total_money`, `card_num`, `input_date`) " \
                                   "VALUES(%s, %s, %s, %s, %s, %s, %s)"
                    curs.execute(charge_query, (device_no, current_money, current_bonus, current_charge, total_money,
                                                card_num, input_date))
                    conn.commit()

        except Exception as e:
            print("From set_charge except : ", e)
            res = '0'
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    29. 카드 검색
    포스로부터 카드번호, 회원코드, 최근사용일자 3개의 인자를 받아 검색 후 반환.
    포스에서 검색창은 한개로 구성되어 있기 때문에 3가지 인자값 중 한개의 인자만
    값이 들어오며 나머지 두개의 인자는 공백으로 받음.
    조건문에서 두개의 인자가 공백일 경우 나머지 인자가 값이 있다고 판단하여
    해당 인자로 검색을 실시함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def search_card(self, card_num, mb_no, end_time):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        card_data = []  # 반환 리스트

        # 회원 코드 검색 쿼리
        get_mb_no_qry = "SELECT `mb_no` FROM gl_member_card WHERE `num` = %s"

        # 발급일자 저장
        get_input_date_qry = "SELECT `input_date` FROM gl_card WHERE `card_num` = %s"

        # 누적 충전 금액 검색 쿼리
        get_total_charge_qry = "SELECT SUM(`current_charge`) * 100 AS 'total_charge' " \
                               "FROM gl_charger_state WHERE `card_num` = %s"

        # 카드 잔액 및 최근 사용 일자 검색 쿼리
        get_remain_card_qry = "SELECT `remain_card` * 100 AS 'remain_card', `end_time` FROM gl_sales_list " \
                              "WHERE `card_num` = %s " \
                              "ORDER BY `end_time` DESC LIMIT 1 "

        # card_num 검색
        if mb_no == "" and end_time == "":
            try:
                with conn.cursor():
                    # 임시저장 딕셔너리
                    temp_dict = OrderedDict()
                    temp_dict['card_num'] = card_num
                    temp_dict['input_date'] = '0'
                    temp_dict['mb_no'] = '0'
                    temp_dict['total_charge'] = '0'
                    temp_dict['remain_card'] = '0'
                    temp_dict['end_time'] = '0'

                    curs.execute(get_input_date_qry, card_num)
                    get_input_res = curs.fetchall()

                    for input_date in get_input_res:
                        if input_date['input_date']:
                            temp_dict['input_date'] = str(input_date['input_date'])

                    # 회원 코드 저장
                    curs.execute(get_mb_no_qry, card_num)
                    get_mb_no_res = curs.fetchall()

                    for mb_no in get_mb_no_res:
                        if mb_no['mb_no']:
                            temp_dict['mb_no'] = mb_no['mb_no']

                    # 누적 충전 금액 저장
                    curs.execute(get_total_charge_qry, card_num)
                    get_total_charge_res = curs.fetchall()

                    for total_charge in get_total_charge_res:
                        if total_charge['total_charge']:
                            temp_dict['total_charge'] = int(total_charge['total_charge'])

                    # 카드 잔액 및 최근 사용 일자 저장
                    curs.execute(get_remain_card_qry, card_num)
                    get_remain_card_res = curs.fetchall()

                    for remain_card in get_remain_card_res:
                        if remain_card['remain_card']:
                            temp_dict['remain_card'] = int(remain_card['remain_card'])
                        if remain_card['end_time']:
                            temp_dict['end_time'] = str(remain_card['end_time'])

                    card_data.append(temp_dict)
            except Exception as e:
                print("From search_card for `card_num` except : ", e)
            finally:
                conn.close()
        # mb_no 검색
        elif card_num == "" and end_time == "":

            try:
                with conn.cursor():
                    # 카드번호 및 발급 일자 가져오기
                    get_card_qry = "SELECT mb_card.`num` AS 'card_num', card.`input_date` AS 'input_date' " \
                                   "FROM gl_member_card AS mb_card " \
                                   "INNER JOIN gl_card AS card " \
                                   "ON mb_card.num = card.card_num " \
                                   "WHERE mb_card.mb_no = %s"
                    curs.execute(get_card_qry, mb_no)
                    get_card_res = curs.fetchall()

                    for card in get_card_res:
                        # 임시저장 딕셔너리
                        temp_dict = OrderedDict()
                        temp_dict['card_num'] = card['card_num']
                        temp_dict['input_date'] = str(card['input_date'])
                        temp_dict['mb_no'] = mb_no
                        # 초기화
                        temp_dict['total_charge'] = '0'
                        temp_dict['remain_card'] = '0'
                        temp_dict['end_time'] = '0'

                        # 누적 충전 금액 저장
                        curs.execute(get_total_charge_qry, card['card_num'])
                        get_total_charge_res = curs.fetchall()

                        for total_charge in get_total_charge_res:
                            if total_charge['total_charge']:
                                temp_dict['total_charge'] = int(total_charge['total_charge'])

                        # 카드 잔액 및 최근 사용 일자 저장
                        curs.execute(get_remain_card_qry, card['card_num'])
                        get_remain_card_res = curs.fetchall()

                        for remain_card in get_remain_card_res:
                            if remain_card['remain_card']:
                                temp_dict['remain_card'] = int(remain_card['remain_card'])
                            if remain_card['end_time']:
                                temp_dict['end_time'] = str(remain_card['end_time'])

                        # 반환 리스트 저장
                        card_data.append(temp_dict)
            except Exception as e:
                print("From search_card for `mb_no` except : ", e)
            finally:
                conn.close()
        # end_time 검색
        elif card_num == "" and mb_no == "":
            try:
                with conn.cursor():
                    # 최근 사용 카드 검색
                    get_end_card_qry = "SELECT `card_num` FROM gl_sales_list " \
                                       " WHERE `end_time` LIKE '%%" + end_time + "%%'" \
                                                                                 " GROUP BY `card_num`"
                    curs.execute(get_end_card_qry)
                    get_end_card_res = curs.fetchall()

                    for end_card in get_end_card_res:
                        # 임시저장 딕셔너리
                        temp_dict = OrderedDict()
                        temp_dict['card_num'] = end_card['card_num']
                        temp_dict['input_date'] = '0'
                        temp_dict['mb_no'] = '0'
                        temp_dict['total_charge'] = '0'
                        temp_dict['remain_card'] = '0'
                        temp_dict['end_time'] = '0'

                        # 발급일자 저장
                        curs.execute(get_input_date_qry, end_card['card_num'])
                        get_input_res = curs.fetchall()

                        for input_date in get_input_res:
                            if input_date['input_date']:
                                temp_dict['input_date'] = str(input_date['input_date'])

                        # 회원 코드 저장
                        curs.execute(get_mb_no_qry, end_card['card_num'])
                        get_mb_no_res = curs.fetchall()

                        for mb_no in get_mb_no_res:
                            if mb_no['mb_no']:
                                temp_dict['mb_no'] = mb_no['mb_no']

                        # 누적 충전 금액 저장
                        curs.execute(get_total_charge_qry, end_card['card_num'])
                        get_total_charge_res = curs.fetchall()

                        for total_charge in get_total_charge_res:
                            if total_charge['total_charge']:
                                temp_dict['total_charge'] = int(total_charge['total_charge'])

                        # 카드 잔액 및 최근 사용 일자 저장
                        curs.execute(get_remain_card_qry, end_card['card_num'])
                        get_remain_card_res = curs.fetchall()

                        for remain_card in get_remain_card_res:
                            if remain_card['remain_card']:
                                temp_dict['remain_card'] = int(remain_card['remain_card'])
                            if remain_card['end_time']:
                                temp_dict['end_time'] = str(remain_card['end_time'])

                        card_data.append(temp_dict)
            except Exception as e:
                print("From search_card for `end_time` except : ", e)
            finally:
                conn.close()

        return card_data

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    30. 카드 이력 초기화
    포스로부터 카드번호를 넘겨받아 해당 카드의 사용 내역을 삭제한다.
    전달받은 카드번호가 '0'일 경우 전체 카드 내역을 삭제한다.
    셀프 / 매트 / 진공 / 리더(매트) /  Garage / 충전 테이블에서 내역을 삭제
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def reset_card_history(self, card_num):
        res = '1'  # 반환값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 카드 번호가 있을 때
        if card_num != '0':

            try:
                with conn.cursor():
                    # self 내역 삭제
                    self_delete_qry = "DELETE FROM gl_self_state WHERE `card_num` = %s"
                    curs.execute(self_delete_qry, card_num)
                    conn.commit()

                    # air 내역 삭제
                    air_delete_qry = "DELETE FROM gl_air_state WHERE `card_num` = %s"
                    curs.execute(air_delete_qry, card_num)
                    conn.commit()

                    # mate 내역 삭제
                    mate_delete_qry = "DELETE FROM gl_mate_state WHERE `card_num` = %s"
                    curs.execute(mate_delete_qry, card_num)
                    conn.commit()

                    # reader 내역 삭제
                    reader_delete_qry = "DELETE FROM gl_reader_state WHERE `card_num` = %s"
                    curs.execute(reader_delete_qry, card_num)
                    conn.commit()

                    # garage 내역 삭제
                    garage_delete_qry = "DELETE FROM gl_garage_state WHERE `card_num` = %s"
                    curs.execute(garage_delete_qry, card_num)
                    conn.commit()

                    # charger 내역 삭제
                    charger_delete_qry = "DELETE FROM gl_charger_state WHERE `card_num` = %s"
                    curs.execute(charger_delete_qry, card_num)
                    conn.commit()
            except Exception as e:
                print("From reset_card_history for one_card except : ", e)
                res = '0'
            finally:
                conn.close()
        # 전체 카드 이력 초기화 - 현금 단독으로 사용한 세차장비 ->  card_num = '00000000'
        elif card_num == '0':

            try:
                with conn.cursor():
                    # self 내역 삭제
                    self_delete_qry = "DELETE FROM gl_self_state WHERE `card_num` NOT IN ('00000000')"
                    curs.execute(self_delete_qry)
                    conn.commit()

                    # air 내역 삭제
                    air_delete_qry = "DELETE FROM gl_air_state WHERE `card_num` NOT IN ('00000000')"
                    curs.execute(air_delete_qry)
                    conn.commit()

                    # mate 내역 삭제
                    mate_delete_qry = "DELETE FROM gl_mate_state WHERE `card_num` NOT IN ('00000000')"
                    curs.execute(mate_delete_qry)
                    conn.commit()

                    # reader 내역 삭제
                    reader_delete_qry = "DELETE FROM gl_reader_state WHERE `card_num` NOT IN ('00000000')"
                    curs.execute(reader_delete_qry)
                    conn.commit()

                    # garage 내역 삭제
                    garage_delete_qry = "DELETE FROM gl_garage_state WHERE `card_num` NOT IN ('00000000')"
                    curs.execute(garage_delete_qry)
                    conn.commit()

                    # charger 내역 삭제
                    charger_delete_qry = "DELETE FROM gl_charger_state"
                    curs.execute(charger_delete_qry)
                    conn.commit()

            except Exception as e:
                print("From reset_card_history for all_card except : ", e)
                res = '0'
            finally:
                conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    31. 장비 전체 이력 초기화
    셀프 / 매트 / 진공 / 리더(매트) / Garage / 충전 테이블을 초기화
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def reset_device_history(self):
        res = '1'  # 반환값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # self 내역 삭제
                self_delete_qry = "DELETE FROM gl_self_state "
                curs.execute(self_delete_qry)
                conn.commit()

                # air 내역 삭제
                air_delete_qry = "DELETE FROM gl_air_state"
                curs.execute(air_delete_qry)
                conn.commit()

                # mate 내역 삭제
                mate_delete_qry = "DELETE FROM gl_mate_state"
                curs.execute(mate_delete_qry)
                conn.commit()

                # reader 내역 삭제
                reader_delete_qry = "DELETE FROM gl_reader_state"
                curs.execute(reader_delete_qry)
                conn.commit()

                # garage 내역 삭제
                garage_delete_qry = "DELETE FROM gl_garage_state"
                curs.execute(garage_delete_qry)
                conn.commit()

                # charger 내역 삭제
                charger_delete_qry = "DELETE FROM gl_charger_state"
                curs.execute(charger_delete_qry)
                conn.commit()
        except Exception as e:
            res = '0'
            print("From reset_device_history except : ", e)
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    32. 관리 업체 정보 불러오기
    업체 번호 / 업체명 / 업체 키값 / 암호화 여부를 포스에 전달한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_manager_info(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_info_qry = "SELECT manager.`no` AS 'manager_no', manager.`name` AS 'manager_name', " \
                               "manager.`manager_id` AS 'manager_id', manager.`encrypt` AS 'manager_encrypt' " \
                               "FROM gl_pos_config AS pos " \
                               "INNER JOIN gl_manager AS manager " \
                               "ON pos.manager_no = manager.`no`"
                curs.execute(get_info_qry)
                get_info_res = curs.fetchall()

        except Exception as e:
            print("From get_manager_info except : ", e)
        finally:
            conn.close()
        return get_info_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    33. CRC 테이블 불러오기
    CRC 테이블의 모든 정보를 포스에 전달한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_crc(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_crc_qry = "SELECT * FROM gl_crc"
                curs.execute(get_crc_qry)
                get_crc_res = curs.fetchall()

                return get_crc_res

        except Exception as e:
            print("From get_crc except : ", e)
        finally:
            conn.close()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    34. 등록된 장비 목록 불러오기
    등록된 장비의 목록을 포스에 전달한다.( 기기주소변경시 선택용)
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_device_list(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_name_qry = "SELECT DISTINCT info.`device_name` AS 'device_name', list.`type` AS 'device_type' " \
                               "FROM gl_device_list AS list " \
                               "INNER JOIN gl_device_info AS info ON list.`type` = info.`type`"
                curs.execute(get_name_qry)
                get_name_res = curs.fetchall()

                return get_name_res

        except Exception as e:
            print("From get_device_list except : ", e)
        finally:
            conn.close()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    35. 실시간 모니터링(LAN)
    키오스크 및 터치충전기의 모니터링 상태를 전송하는 함수
    통신상태를 체크하는 PING에 TIMEOUT 1초가 걸려있기 때문에 485와 별도로 분리하였다.
    키오스크는 직접 데이터 베이스에 저장하고, 터치 충전기는 별도의 스레드가 있기 때문에
    장비에서 직접 동작값을 가져오는 별도의 행위는 없으며 DB에 저장된 값을 조회하여 
    전달한다. 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_lan_device_state(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 반환 배열
                lan_state_list = []

                # 기기 정보 추출
                get_device_qry = "SELECT `type`,  `addr`, `ip` " \
                                 "FROM gl_device_list " \
                                 "WHERE `type` = %s OR `type` = %s"
                curs.execute(get_device_qry, (gls_config.TOUCH, gls_config.KIOSK))
                device_list = curs.fetchall()

                for device in device_list:
                    query = "SELECT SUM(`current_charge`) * 100 AS 'charge', " \
                            "COUNT(CASE WHEN `kind` = '0' THEN 1 END) AS 'count'" \
                            " FROM gl_charger_state AS charger" \
                            " INNER JOIN gl_device_list AS d_list" \
                            " ON d_list.`no` = charger.`device_no`" \
                            " WHERE `charger`.`input_date` " \
                            " > date_format(curdate( ), '%%Y-%%m-%%d' ) " \
                            " AND d_list.`type` = %s AND d_list.addr = %s"
                    curs.execute(query, (device['type'], device['addr']))
                    res = curs.fetchall()

                    # 임시 저장 딕셔너리
                    temp_charger = OrderedDict()

                    # 기본 정보 저장
                    temp_charger['device_type'] = device['type']
                    temp_charger['device_addr'] = device['addr']
                    temp_charger['connect'] = '0'  # 통신상태
                    temp_charger['charge'] = '0'  # 금일 충전액
                    temp_charger['count'] = '0'  # 금일 카드 발급 수

                    # 통신 상태 테스트(ping) - 터치, 키오스크
                    con_res = os.system("timeout 1 ping -c 1 " + device['ip'])
                    if con_res == 0:
                        temp_charger['connect'] = '1'

                        # 전송 정보 저장
                        for row in res:
                            if row['charge']:
                                temp_charger['charge'] = int(row['charge'])
                            temp_charger['count'] = row['count']
                    else:
                        temp_charger['connect'] = '0'

                    lan_state_list.append(temp_charger)
        except Exception as e:
            print("From get_lan_device_state except : ", e)
        finally:
            conn.close()
        return lan_state_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    36. 우수회원 보너스 가져오기
    카드 번호를 받아 우수회원일 경우 우수회원 보너스를 반환한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_vip_bonus(self, card_num):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():

                vip_bonus_qry = "SELECT `level`.`level`, `level`.`level_name`, `bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, " \
                                "`bonus6`, `bonus7`, `bonus8`, `bonus9`,  `bonus10` FROM  gl_member_card AS mb_card " \
                                "INNER JOIN gl_member AS mb ON mb_card.mb_no = mb.`no` " \
                                "INNER JOIN gl_charger_bonus AS bonus ON mb.`level` = bonus.mb_level " \
                                "INNER JOIN gl_member_level AS `level` ON mb.`level` = `level`.`level` " \
                                "WHERE mb_card.num = %s"

                curs.execute(vip_bonus_qry, card_num)
                vip_bonus_res = curs.fetchall()
        except Exception as e:
            print(e)
        finally:
            conn.close()

        return vip_bonus_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    37. 우수회원 자동 갱신
    우수회원 조건을 만족한 사람을 업데이트한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def update_vip(self, second=10):
        print("update_vip_thread")
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():

                get_member_list_qry = "SELECT `no` FROM gl_member"
                curs.execute(get_member_list_qry)
                get_member_list_res = curs.fetchall()

                update_vip_qry = "UPDATE gl_member SET `level` = %s WHERE `no` = %s and vip_set = '0' "

                for get_member in get_member_list_res:
                    is_vip_qry = "SELECT `level_code` FROM gl_vip_list WHERE `mb_no` = %s"
                    curs.execute(is_vip_qry, get_member['no'])
                    is_vip_res = curs.fetchall()

                    if is_vip_res:
                        for vip in is_vip_res:
                            curs.execute(update_vip_qry, (vip['level_code'], get_member['no']))
                            conn.commit()
                    else:
                        curs.execute(update_vip_qry, ('1', get_member['no']))
                        conn.commit()

        except Exception as e:
            print(e)
            return
        finally:
            conn.close()
            threading.Timer(second, self.update_vip).start()  # 쓰레드 재귀 호출

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    38. 멤버 보너스 설정 불러오기
    회원 등급 별 보너스 설정을 불러온다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_member_bonus(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_member_bonus_q = "select `level`.`level`, `level`.`level_name`, v_con.`charge_money` AS 'money', v_con.`charge_period` / 30 AS 'period', " \
                                     "bonus.`bonus1` * 100 AS 'bonus1', bonus.`bonus2` * 100 AS 'bonus2', bonus.`bonus3` * 100 AS 'bonus3', bonus.`bonus4` * 100 AS 'bonus4', bonus.`bonus5` * 100 AS 'bonus5', " \
                                     "bonus.`bonus6` * 100 AS 'bonus6', bonus.`bonus7` * 100 AS 'bonus7', bonus.`bonus8` * 100 AS 'bonus8', bonus.`bonus9` * 100 AS 'bonus9', bonus.`bonus10` * 100 AS 'bonus10' " \
                                     "FROM gl_charger_bonus AS bonus " \
                                     "INNER JOIN gl_member_level AS `level` ON bonus.mb_level = `level`.`level` " \
                                     "INNER JOIN gl_vip_config AS v_con ON v_con.`level` = `level`.`level`"
                curs.execute(get_member_bonus_q)
                get_member_bonus_res = curs.fetchall()

                for get in get_member_bonus_res:
                    get['bonus1'] = int(get['bonus1'])
                    get['bonus2'] = int(get['bonus2'])
                    get['bonus3'] = int(get['bonus3'])
                    get['bonus4'] = int(get['bonus4'])
                    get['bonus5'] = int(get['bonus5'])
                    get['bonus6'] = int(get['bonus6'])
                    get['bonus7'] = int(get['bonus7'])
                    get['bonus8'] = int(get['bonus8'])
                    get['bonus9'] = int(get['bonus9'])
                    get['bonus10'] = int(get['bonus10'])
                    get['period'] = int(get['period'])

        except Exception as e:
            print(e)
        finally:
            conn.close()
        return get_member_bonus_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    39. 멤버 보너스 설정 
    회원 등급 별 보너스를 설정한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_member_bonus(self, args):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        res = '1'  # 반환값

        # 데이터 파싱
        period = int(args['period']) * 30
        lv1_name = args['lv1_name']
        lv2_name = args['lv2_name']
        lv3_name = args['lv3_name']
        lv1_money = args['lv1_money']
        lv2_money = args['lv2_money']
        lv3_money = args['lv3_money']
        lv1_bonus1 = int(args['lv1_bonus1']) // 100
        lv2_bonus1 = int(args['lv2_bonus1']) // 100
        lv3_bonus1 = int(args['lv3_bonus1']) // 100
        lv1_bonus2 = int(args['lv1_bonus2']) // 100
        lv2_bonus2 = int(args['lv2_bonus2']) // 100
        lv3_bonus2 = int(args['lv3_bonus2']) // 100
        lv1_bonus3 = int(args['lv1_bonus3']) // 100
        lv2_bonus3 = int(args['lv2_bonus3']) // 100
        lv3_bonus3 = int(args['lv3_bonus3']) // 100
        lv1_bonus4 = int(args['lv1_bonus4']) // 100
        lv2_bonus4 = int(args['lv2_bonus4']) // 100
        lv3_bonus4 = int(args['lv3_bonus4']) // 100
        lv1_bonus5 = int(args['lv1_bonus5']) // 100
        lv2_bonus5 = int(args['lv2_bonus5']) // 100
        lv3_bonus5 = int(args['lv3_bonus5']) // 100
        lv1_bonus6 = int(args['lv1_bonus6']) // 100
        lv2_bonus6 = int(args['lv2_bonus6']) // 100
        lv3_bonus6 = int(args['lv3_bonus6']) // 100
        lv1_bonus7 = int(args['lv1_bonus7']) // 100
        lv2_bonus7 = int(args['lv2_bonus7']) // 100
        lv3_bonus7 = int(args['lv3_bonus7']) // 100
        lv1_bonus8 = int(args['lv1_bonus8']) // 100
        lv2_bonus8 = int(args['lv2_bonus8']) // 100
        lv3_bonus8 = int(args['lv3_bonus8']) // 100
        lv1_bonus9 = int(args['lv1_bonus9']) // 100
        lv2_bonus9 = int(args['lv2_bonus9']) // 100
        lv3_bonus9 = int(args['lv3_bonus9']) // 100
        lv1_bonus10 = int(args['lv1_bonus10']) // 100
        lv2_bonus10 = int(args['lv2_bonus10']) // 100
        lv3_bonus10 = int(args['lv3_bonus10']) // 100

        try:
            with conn.cursor():
                # 우수회원 달성 조건 업데이트
                update_config_qry = "UPDATE gl_vip_config SET `charge_money` = %s, `charge_period` = %s WHERE `level` = %s"

                curs.execute(update_config_qry, (lv1_money, period, 1))
                conn.commit()
                curs.execute(update_config_qry, (lv2_money, period, 2))
                conn.commit()
                curs.execute(update_config_qry, (lv3_money, period, 3))
                conn.commit()

                # 우수회원 등급 업데이트
                update_level_name_q = "UPDATE gl_member_level SET `level_name` = %s WHERE `level` = %s"

                curs.execute(update_level_name_q, (lv1_name, 1))
                conn.commit()
                curs.execute(update_level_name_q, (lv2_name, 2))
                conn.commit()
                curs.execute(update_level_name_q, (lv3_name, 3))
                conn.commit()

                # 우수회원 보너스 업데이트
                update_bonus_qry = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, `bonus4` = %s, " \
                                   "`bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, `bonus9` = %s, `bonus10` = %s " \
                                   "WHERE `mb_level` = %s"
                curs.execute(update_bonus_qry, (lv1_bonus1, lv1_bonus2, lv1_bonus3, lv1_bonus4, lv1_bonus5, lv1_bonus6, lv1_bonus7, lv1_bonus8, lv1_bonus9, lv1_bonus10, 1))
                conn.commit()
                curs.execute(update_bonus_qry, (lv2_bonus1, lv2_bonus2, lv2_bonus3, lv2_bonus4, lv2_bonus5, lv2_bonus6, lv2_bonus7, lv2_bonus8, lv2_bonus9, lv2_bonus10, 2))
                conn.commit()
                curs.execute(update_bonus_qry, (lv3_bonus1, lv3_bonus2, lv3_bonus3, lv3_bonus4, lv3_bonus5, lv3_bonus6, lv3_bonus7, lv3_bonus8, lv3_bonus9, lv3_bonus10, 3))
                conn.commit()

                # 터치 충전기 보너스 테이블 업데이트
                get_touch_ip_q = "SELECT `ip` FROM gl_device_list WHERE `type` = %s"
                curs.execute(get_touch_ip_q, gls_config.TOUCH)
                get_touch_res = curs.fetchall()

                for get_touch in get_touch_res:
                    pi_conn = pymysql.connect(host=get_touch['ip'], user=gls_config.PI_MYSQL_USER, password=gls_config.PI_MYSQL_PWD,
                                              charset=gls_config.MYSQL_SET, db=gls_config.PI_MYSQL_DB)
                    pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)

                    try:
                        with pi_conn.cursor():

                            touch_bonus_qry = "UPDATE member_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, `bonus4` = %s, " \
                                              "`bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, `bonus9` = %s, `bonus10` = %s " \
                                              "WHERE `mb_level` = %s"
                            pi_curs.execute(touch_bonus_qry, (args['lv1_bonus1'], args['lv1_bonus2'], args['lv1_bonus3'], args['lv1_bonus4'], args['lv1_bonus5'], args['lv1_bonus6'], args['lv1_bonus7'], args['lv1_bonus8'], args['lv1_bonus9'], args['lv1_bonus10'], 1))
                            pi_conn.commit()
                            pi_curs.execute(touch_bonus_qry, (args['lv2_bonus1'], args['lv2_bonus2'], args['lv2_bonus3'], args['lv2_bonus4'], args['lv2_bonus5'], args['lv2_bonus6'], args['lv2_bonus7'], args['lv2_bonus8'], args['lv2_bonus9'], args['lv2_bonus10'], 2))
                            pi_conn.commit()
                            pi_curs.execute(touch_bonus_qry, (args['lv3_bonus1'], args['lv3_bonus2'], args['lv3_bonus3'], args['lv3_bonus4'], args['lv3_bonus5'], args['lv3_bonus6'], args['lv3_bonus7'], args['lv3_bonus8'], args['lv3_bonus9'], args['lv3_bonus10'], 3))
                            pi_conn.commit()
                    except Exception as e:
                        print(e)
                        res = 0
                    finally:
                        pi_conn.close()
        except Exception as e:
            print(e)
            res = 0
        finally:
            conn.close()
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    40. 마스터 카드 이력 조회 
    마스터카드의 사용 이력을 조회 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_master_card_history(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        master_card_history = []

        try:
            with conn.cursor():
                get_master_qry = "SELECT `device_name`, `device_addr`, `master_card` AS 'money', `end_time` AS 'input_date' " \
                                 "FROM gl_sales_list WHERE `master_card` != '0000'" \
                                 "AND (`device_type` = %s or `device_type` = %s or `device_type` = %s or `device_type` = %s " \
                                 "or `device_type` = %s) " \
                                 "ORDER BY `end_time` ASC"
                curs.execute(get_master_qry, (gls_config.SELF, gls_config.AIR, gls_config.MATE, gls_config.READER, gls_config.GARAGE))
                get_master_res = curs.fetchall()

                total = 0

                for get in get_master_res:
                    temp_master = OrderedDict()
                    temp_master['device_name'] = '0'
                    temp_master['device_addr'] = '0'
                    temp_master['money'] = '0'
                    temp_master['input_date'] = '0'
                    temp_master['total_money'] = '0'

                    total = total + int(int(get['money']) * 100)

                    temp_master['device_name'] = get['device_name']
                    temp_master['device_addr'] = get['device_addr']
                    temp_master['money'] = int(int(get['money']) * 100)
                    temp_master['input_date'] = str(get['input_date'])
                    temp_master['total_money'] = total

                    master_card_history.append(temp_master)

                    print(total)
        # except Exception as e:
        #     print(e)
        finally:
            conn.close()
        return master_card_history

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    41. 관리 업체 리스트 불러오기 
    관리 업체 리스트를 불러온다
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_manager_list(self):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                get_info_qry = "SELECT manager.`no` AS 'manager_no', manager.`name` AS 'manager_name', " \
                               "manager.`manager_id` AS 'manager_id', manager.`encrypt` AS 'manager_encrypt' " \
                               "FROM gl_manager AS manager "

                curs.execute(get_info_qry)
                get_info_res = curs.fetchall()

        except Exception as e:
            print("From get_manager_info except : ", e)
        finally:
            conn.close()
        return get_info_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    42. 마스터 설정 불러오기 
    마스터 페이지 설정 불러오기
    * 현재 auth_code만 구현 되어 있음
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_master_config(self, auth_code):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        master_config_list = []
        config = OrderedDict()

        try:
            with conn.cursor():
                get_auth_qry = "SELECT `auth_code` FROM gl_shop_info"
                curs.execute(get_auth_qry)
                get_auth_res = curs.fetchall()

                for get_auth in get_auth_res:
                    if get_auth['auth_code'] == auth_code:
                        config['auth'] = '1'
                        get_info_qry = "SELECT manager.`name` FROM gl_pos_config AS pos " \
                                       "INNER JOIN gl_manager AS manager ON pos.`manager_no` = manager.`no`"
                        curs.execute(get_info_qry)
                        get_info_res = curs.fetchone()
                        config['manager_name'] = get_info_res['name']

                        get_enable_card_q = "SELECT `enable_card` FROM gl_pos_config"
                        curs.execute(get_enable_card_q)
                        get_enable_card = curs.fetchone()
                        config['enable_card'] = get_enable_card['enable_card']

                        get_binary_card_q = "SELECT `auth_code` FROM gl_pos_config"
                        curs.execute(get_binary_card_q)
                        get_binary_card = curs.fetchone()
                        config['card_binary'] = get_binary_card['auth_code']
                    else:
                        config['auth'] = '0'
                    master_config_list.append(config)

        except Exception as e:
            print("From get_master_config except : ", e)
        finally:
            conn.close()
        return master_config_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    43. 마스터 설정  
    마스터 페이지 설정 
    * 현재 auth_code만 구현 되어 있음
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_master_config(self, auth_code, manager_no, enable_card, card_binary):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        res = 1

        if str(enable_card) == '1':
            gls_config.ENABLE_CARD = False
        elif str(enable_card) == '0':
            gls_config.ENABLE_CARD = True

        try:
            with conn.cursor():
                set_master_config_q = "UPDATE gl_shop_info SET `auth_code` = %s"
                curs.execute(set_master_config_q, auth_code)
                conn.commit()

                set_manager_no_q = "UPDATE gl_pos_config SET `manager_no` = %s, `enable_card` = %s, `auth_code` = %s "
                curs.execute(set_manager_no_q, (manager_no, enable_card, card_binary))
                conn.commit()

                if manager_no =='1' or manager_no == '4':
                    gls_config.MANAGER_CODE = '01'
                elif manager_no == '2':
                    gls_config.MANAGER_CODE = '02'
                elif manager_no == '3' or manager_no == '5':
                    gls_config.MANAGER_CODE = '03'

        except Exception as e:
            print("From get_master_config except : ", e)
            res = 0
        finally:
            conn.close()
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    44. 히든 설정 불러오기  
    마스터 페이지에서 사용 하는 기능의 일부
    DB에서 셀프 세차기의 히든 설정값을 불러온다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_hidden_config(self, device_addr):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                query = "SELECT `speedier_enable` AS `enable_type`, `use_type` AS `pay_type`, " \
                        "`set_coating_output` AS `coating_type`, `wipping_enable` AS `wipping_enable`, " \
                        "`wipping_temperature` AS `wipping_temp` " \
                        "FROM gl_self_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                curs.execute(query, device_addr)
                res = curs.fetchall()

        except Exception as e:
            print("From get_hidden_config except : ", e)
            res = 0
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    45. 히든 설정   
    마스터 페이지에서 사용 하는 기능의 일부
    히든 설정값은 포스로부터 전달 받고
    나머지 설정값은 DB에서 직접 조회
    최종적으로 args를 만들어 set_self_config를 호출한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def set_hidden_config(self, args):
        # 데이터 파싱
        device_addr = args['device_addr']
        speedier_enable = args['enable_type']
        use_type = args['pay_type']
        set_coating_output = args['coating_type']
        wipping_enable = args['wipping_enable']
        wipping_temperature = args['wipping_temp']

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                query = "SELECT * FROM gl_self_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                curs.execute(query, device_addr)
                get_config = curs.fetchall()

                config = OrderedDict()
                config['device_addr'] = str(device_addr)

                # 히든 설정값
                config['use_type'] = use_type
                config['speedier_enable'] = speedier_enable
                config['set_coating_output'] = set_coating_output
                config['wipping_enable'] = wipping_enable
                config['wipping_temperature'] = wipping_temperature

                # 기본 설정 값
                for row in get_config:
                    if row['self_init_money']:
                        config['self_init_money'] = int(row['self_init_money']) * 100
                    if row['self_init_time']:
                        config['self_init_time'] = row['self_init_time']
                    if row['self_con_enable']:
                        config['self_con_enable'] = row['self_con_enable']
                    if row['self_con_money']:
                        config['self_con_money'] = int(row['self_con_money']) * 100
                    if row['self_con_time']:
                        config['self_con_time'] = row['self_con_time']
                    if row['self_pause_time']:
                        config['self_pause_time'] = row['self_pause_time']
                    if row['foam_enable']:
                        config['foam_enable'] = row['foam_enable']
                    if row['foam_con_enable']:
                        config['foam_con_enable'] = row['foam_con_enable']
                    if row['foam_speedier']:
                        config['foam_speedier'] = row['foam_speedier']
                    if row['foam_init_money']:
                        config['foam_init_money'] = int(row['foam_init_money']) * 100
                    if row['foam_init_time']:
                        config['foam_init_time'] = row['foam_init_time']
                    if row['foam_con_money']:
                        config['foam_con_money'] = int(row['foam_con_money']) * 100
                    if row['foam_con_time']:
                        config['foam_con_time'] = row['foam_con_time']
                    if row['foam_pause_time']:
                        config['foam_pause_time'] = row['foam_pause_time']
                    if row['foam_end_delay']:
                        config['foam_end_delay'] = row['foam_end_delay']
                    if row['under_enable']:
                        config['under_enable'] = row['under_enable']
                    if row['under_con_enable']:
                        config['under_con_enable'] = row['under_con_enable']
                    if row['under_speedier']:
                        config['under_speedier'] = row['under_speedier']
                    if row['under_init_money']:
                        config['under_init_money'] = int(row['under_init_money']) * 100
                    if row['under_init_time']:
                        config['under_init_time'] = row['under_init_time']
                    if row['under_con_money']:
                        config['under_con_money'] = int(row['under_con_money']) * 100
                    if row['under_con_time']:
                        config['under_con_time'] = row['under_con_time']
                    if row['under_pause_time']:
                        config['under_pause_time'] = row['under_pause_time']
                    if row['coating_enable']:
                        config['coating_enable'] = row['coating_enable']
                    if row['coating_con_enable']:
                        config['coating_con_enable'] = row['coating_con_enable']
                    if row['coating_speedier']:
                        config['coating_speedier'] = row['coating_speedier']
                    if row['coating_init_money']:
                        config['coating_init_money'] = int(row['coating_init_money']) * 100
                    if row['coating_init_time']:
                        config['coating_init_time'] = row['coating_init_time']
                    if row['coating_con_money']:
                        config['coating_con_money'] = int(row['coating_con_money']) * 100
                    if row['coating_con_time']:
                        config['coating_con_time'] = row['coating_con_time']
                    if row['coating_pause_time']:
                        config['coating_pause_time'] = row['coating_pause_time']
                    if row['cycle_money']:
                        config['cycle_money'] = int(row['cycle_money']) * 100
                    if row['buzzer_time']:
                        config['buzzer_time'] = row['buzzer_time']
                    if row['pause_count']:
                        config['pause_count'] = row['pause_count']
                    if row['pay_free']:
                        config['pay_free'] = row['pay_free']
                    if row['secret_enable']:
                        config['secret_enable'] = row['secret_enable']
                    if row['secret_date']:
                        config['secret_date'] = row['secret_date']

                dv = device.Device()

                res = dv.set_self_config(config)


        # except Exception as e:
        #     print("From set_hidden_config except : ", e)
        #     res = 0
        finally:
            conn.close()

        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    46. 셀프 주소 추출   
    마스터 페이지에서 사용 하는 기능의 일부인 히든 설정의 셀렉트 박스를 위한 값
    셀프 세차기의 주소를 반환한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_self_list(self):

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s "
                curs.execute(query, gls_config.SELF)
                get_self = curs.fetchall()

        # except Exception as e:
        #     print("From set_hidden_config except : ", e)
        #     res = 0
        finally:
            conn.close()

        return get_self

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    47. 셀프 사용 내역   
    셀프 사용 내역 추출 (셀프 / 폼 / 하부 / 코팅)
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_self_detail(self, no, type):

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                if str(type) == 'self':
                    query = "SELECT `self_time`, `under_time`, `foam_time`, `coating_time` FROM gl_self_state AS self WHERE self.`no` = %s"
                    curs.execute(query, no)
                    get_res = curs.fetchall()

                    use_detail = ''

                    for row in get_res:
                        if row['self_time'] != '0000':
                            use_detail += '셀프/'
                        if row['under_time'] != '0000':
                            use_detail += '하부/'
                        if row['foam_time'] != '0000':
                            use_detail += '폼/'
                        if row['coating_time'] != '0000':
                            use_detail += '코팅/'

                    if use_detail:
                        use_detail = use_detail[:-1]
                elif str(type) == 'garage':
                    query = "SELECT `self_time`, `under_time`, `foam_time`, `coating_time`, `air_time`, `airgun_time` FROM gl_garage_state AS garage WHERE garage.`no` = %s"
                    curs.execute(query, no)
                    get_res = curs.fetchall()

                    use_detail = ''

                    for row in get_res:
                        if row['self_time'] != '00000':
                            use_detail += '셀프/'
                        if row['under_time'] != '00000':
                            use_detail += '하부/'
                        if row['foam_time'] != '00000':
                            use_detail += '폼/'
                        if row['coating_time'] != '00000':
                            use_detail += '코팅/'
                        if row['air_time'] != '00000':
                            use_detail += '진공/'
                        if row['airgun_time'] != '00000':
                            use_detail += '에어/'

                    if use_detail:
                        use_detail = use_detail[:-1]


        # except Exception as e:
        #     print("From set_hidden_config except : ", e)
        #     res = 0
        finally:
            conn.close()

        return use_detail

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    48. 신용 카드 월간 매출   
    year, month 를 조건절로 두고 gl_credit_card_log를 검색 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_credit_sales(self, year, month):
        sales_list = []  # 월간 매출 저장 레코드
        total_amount = "0"      # 공급가 누계 초기화
        total_vat = "0"         # 부가세 누계 초기화
        total_pay_amount = "0"  # 승인금액 누계 초기화

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 월간 매출 리스트 추출(레코드 : 일간 매출)
                for i in range(1, 32):
                    days = str(i)

                    # 일간 매출 저장 레코드 초기화
                    temp_list = OrderedDict()            # 일간 매출 저장 레코드
                    temp_list['days'] = '0'              # 일자 초기화
                    temp_list['amount'] = '0'            # 공급가
                    temp_list['vat'] = '0'               # 부가세
                    temp_list['pay_amount'] = '0'        # 승인금액
                    temp_list['total_amount'] = '0'      # 공급가 누계
                    temp_list['total_vat'] = '0'         # 부가세 누계
                    temp_list['total_pay_amount'] = '0'  # 승인금액 누계

                    # 충전 데이터 추출
                    temp_charger = OrderedDict()
                    temp_charger['amount'] = '0'
                    temp_charger['vat'] = '0'
                    temp_charger['pay_amount'] = '0'
                    charger_total_qry = "SELECT SUM(`amount`) AS 'amount', " \
                                        " SUM(`vat`) AS 'vat', " \
                                        " SUM(`pay_amount`)  AS 'pay_amount'" \
                                        " FROM	gl_credit_card_log WHERE `input_date`" \
                                        " LIKE '%%" + year + "-" + month.rjust(2, '0') + "-" + days.rjust(2, '0') + "%%'"
                    curs.execute(charger_total_qry)
                    charger_res = curs.fetchall()

                    # 소수점 절삭
                    for row in charger_res:
                        if row['amount']:
                            temp_charger['amount'] = int(row['amount'])
                        if row['vat']:
                            temp_charger['vat'] = int(row['vat'])
                        if row['pay_amount']:
                            temp_charger['pay_amount'] = int(row['pay_amount'])

                    # 누계 저장
                    total_amount = (int(total_amount) + int(temp_charger['amount']))
                    total_vat = (int(total_vat) + int(temp_charger['vat']))
                    total_pay_amount = (int(total_pay_amount) + int(temp_charger['pay_amount']))

                    # 일간 매출 저장
                    temp_list['days'] = days
                    temp_list['amount'] = int(temp_charger['amount'])
                    temp_list['vat'] = int(temp_charger['vat'])
                    temp_list['pay_amount'] = int(temp_charger['pay_amount'])
                    temp_list['total_amount'] = total_amount
                    temp_list['total_vat'] = total_vat
                    temp_list['total_pay_amount'] = total_pay_amount

                    # 월간 매출 리스트 저장
                    sales_list.insert(i - 1, temp_list)
        # except Exception as e:
            # print("From get_credit_sales except : ", e)
        finally:
            conn.close()

        return sales_list


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    49. 신용 카드 일간 매출   
    year, month, day 를 조건절로 두고 gl_credit_card_log를 검색 후 반환
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def get_credit_days_sales(self, year, month, days):
        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        test_list = []

        try:
            with conn.cursor():
                get_days_total_q = "SELECT `amount`, `vat`, `pay_amount`, `buyer`, `card_commpany_name` AS 'company', " \
                                   "`credit_card_num`, `input_date`, `approval_num` AS 'app_num' " \
                                   "FROM gl_credit_card_log WHERE `input_date` " \
                                   " LIKE '%" + str(year) + "-" + str(month).rjust(2, '0') + "-" \
                                   + str(days).rjust(2, '0') + "%'" \
                                   + " ORDER BY `input_date` ASC"
                curs.execute(get_days_total_q)
                res = curs.fetchall()

                for row in res:
                    temp_dict = OrderedDict()

                    # 소수점 절삭
                    if row['amount']:
                        temp_dict['amount'] = int(row['amount'])
                    if row['vat']:
                        temp_dict['vat'] = int(row['vat'])
                    if row['pay_amount']:
                        temp_dict['pay_amount'] = int(row['pay_amount'])

                    # 0원에 대한 처리
                    if row['amount'] == 0.0:
                        temp_dict['amount'] = 0
                    if row['vat'] == 0.0:
                        temp_dict['vat'] = 0
                    if row['pay_amount'] == 0.0:
                        temp_dict['pay_amount'] = 0

                    if row['buyer']:
                        temp_dict['buyer'] = row['buyer']
                    if row['company']:
                        temp_dict['company'] = row['company']
                    if row['credit_card_num']:
                        temp_dict['credit_card_num'] = row['credit_card_num']
                    if row['input_date']:
                        temp_dict['input_date'] = str(row['input_date'])
                    if row['app_num']:
                        temp_dict['app_num'] = row['app_num']

                    test_list.append(temp_dict)

        except Exception as e:
            print("From credit_days_sales except : ", e)
        finally:
            conn.close()

        print(str(test_list))

        return test_list