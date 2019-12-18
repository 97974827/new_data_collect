import pymysql.cursors
import serial
import threading
import time
import datetime
import gls_config
import touch_charger
import pos
from datetime import datetime, timedelta
from collections import OrderedDict


# Device 기능 목록
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
1. 메인 스레드                 # main_thread
2. 시간 설정                   # set_time
3. 실시간 모니터링             # get_device_state
4. 셀프 설정 불러오기          # get_self_config
5. 셀프 설정                   # set_self_config
6. 진공 설정 불러오기          # get_air_config
7. 진공 설정                   # set_air_config
8. 매트 설정 불러오기          # get_mate_config
9. 매트 설정                   # set_mate_config
10. 충전기 설정 불러오기       # get_charger_config
11. 충전기 설정                # set_charger_config
12. 기기 주소 변경             # change_device_addr
13. 누적 금액 초기화           # reset_total_money
14. 세차장 ID 변경             # update_shop_no
15. 체크섬                     # get_checksum
16. 스레드 감시                # thread_monitor
17. 게러지 설정 불러오기       # get_garage_config
18. 게러지 설정                # set_garage_config
19. 장비 설정 복사             # copy_device_config
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Device:

    # 485 스레드 제어 변수
    USE = False
    USE_EACH = True

    TIME_USE = False
    TIME_USE_EACH = True

    FLAG_MAIN = ''
    FLAG_STATE = ''


    # 스레드 상수화
    device_state_thread = ''
    state_monitor = ''


    # 485 접속 설정
    # PORT = "/dev/ttyUSB0"  # USB
    PORT = "/dev/ttyS0"  # COM 1
    BAUD = "9600"

    # # 485 Thread 버퍼
    # global temp_state
    # temp_state = OrderedDict()
    # temp_state['state'] = '0'  # 동작 상태
    # temp_state['start_time'] = '0'  # 시작 시간
    # temp_state['current_cash'] = '0'  # 투입금액 - 현금
    # temp_state['current_card'] = '0'  # 투입금액 - 카드
    # temp_state['current_master'] = '0'  # 투입금액 - 마스터
    # temp_state['use_cash'] = '0'  # 사용금액 - 현금
    # temp_state['use_card'] = '0'  # 사용금액 - 카드
    # temp_state['use_master'] = '0'  # 사용금액 - 마스터
    # temp_state['remain_time'] = '0'  # 남은 시간
    # temp_state['card_num'] = '0'  # 카드번호
    # temp_state['sales'] = '0'  # 당일 매출
    # temp_state['connect'] = '0'  # 통신 상태
    #
    # global state_list
    # state_list = []



    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    1. 메인 스레드
    get_device_state 함수를 실행 시키는 스레드로서 485통신의 메인 부분.
    POS에서 메인화면으로 진입할 때 마다 호출 된다.
    시작 시 1초의 슬립을 주어 485 충돌시 재 정비할 수 있도록 한다.
    get_device_state 함수를 호출 할 때는 flag를 주어 
    시간 설정 명령과 충돌이 나지 않도록 방지한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def main_thread(self, second=1):
        try:
            time.sleep(0.1)
            self.USE = False
            self.USE_EACH = True
            self.TIME_USE = False
            self.TIME_USE_EACH = True
            self.device_state_thread = threading.Timer(second, self.main_thread)
            self.device_state_thread.daemon = True
            self.FLAG_MAIN = "thread"
            self.get_device_state_thread(self.FLAG_MAIN)
            self.device_state_thread.start()
        except Exception as e:
            print("From Main_thread except : ", e)
            pass

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    2. 시간 설정
    장비의 시간을 설정하는 함수.
    데이터 수집장치에 전원이 들어올 때 최초로 1회 실행되며 
    이후 POS에서 메인화면으로 진입할 때 마다 1회씩 실행된다.
    TIME_USE를 제어하여 외부에서 실행을 종료 시킬 수 있다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_time(self):
        print("set_time")
        # Raise 명령을 통해 강제로 에러를 발생시켜서 함수를 종료시킨다.
        if self.TIME_USE:
            try:
                print("set_time stop")
                raise NotImplementedError
            except Exception as e:
                print("From set_time excpet: ", e)
                pass
            finally:
                return

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        try:
            with conn.cursor():
                # 기기 정보 추출
                get_device_qry = "SELECT `type`,  `addr` " \
                                 "FROM gl_device_list " \
                                 "WHERE `type` = %s OR `type` = %s OR `type` = %s OR `type` = %s OR `type` = %s OR `type` = %s "
                curs.execute(get_device_qry,
                             (gls_config.SELF, gls_config.AIR, gls_config.MATE, gls_config.CHARGER, gls_config.READER, gls_config.GARAGE))

                device_list = curs.fetchall()

                # 시리얼 통신 연결
                ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

                for device in device_list:
                    if self.TIME_USE_EACH:
                        # 현재 시간 정보 추출
                        t_year = datetime.today().strftime('%y')
                        t_month = datetime.today().strftime('%m')
                        t_day = datetime.today().strftime('%d')
                        t_hour = datetime.today().strftime('%H')
                        t_minute = datetime.today().strftime('%M')
                        t_second = datetime.today().strftime('%S')

                        # 시간 설정 값 보내기
                        time_trans = "GL029TS"
                        time_trans += str(gls_config.MANAGER_CODE)
                        time_trans += str(device['type']).rjust(2, "0")
                        time_trans += str(device['addr'])
                        time_trans += str(t_year)
                        time_trans += str(t_month)
                        time_trans += str(t_day)
                        time_trans += str(t_hour)
                        time_trans += str(t_minute)
                        time_trans += str(t_second)
                        time_trans += self.get_checksum(time_trans)
                        time_trans += "CH"  # ETX
                        time_trans = time_trans.encode("utf-8")
                        res = ser.readline(ser.write(bytes(time_trans)) + 100)
                        print("Time Trans : ", time_trans)
                        print("Time Set : ", res)
        except Exception as e:
            print("set_time_thread except : ", e)
        finally:
            conn.close()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    3. 실시간 모니터링(485)
    485 통신의 메인이 되는 함수.
    각 장비에게 동작 상태를 호출하여
    저장값 있는 대기 동작, 저장값 없는 대기 동작, 동작 중인 상태에 대하여 처리한다.
    실행은 메인 스레드에서 호출을 하거나, POS의 실시간 모니터링에서 직접 호출하는
    두 가지 방식이 있으며 flag에 의해 구분된다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_device_state_thread(self, flag):
        if self.USE:
            try:
                print("get_device_state stop")
                raise NotImplementedError
            except Exception as e:
                print("From get_device_state stop except : ", e)
                pass
            finally:
                return

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 실시간 모니터링에서 호출 했을 때
        if flag == "monitor":
            self.TIME_USE = True

        try:
            with conn.cursor():
                # 플래그 설정
                self.FLAG_STATE = 'start'

                # 반환 배열
                global state_list
                state_list = []
                # state_list.clear()


                # RS-485 연결
                ser = serial.Serial(self.PORT, self.BAUD, timeout= 0.1)

                # 기기 정보 추출
                get_device_qry = "SELECT `type`,  `addr`, `ip` " \
                                 "FROM gl_device_list " \
                                 "WHERE `type` = %s OR `type` = %s OR `type` = %s OR `type` = %s OR `type` = %s " \
                                 "OR `type` = %s OR `type` = %s OR `type` = %s"
                curs.execute(get_device_qry, (gls_config.SELF, gls_config.AIR, gls_config.MATE, gls_config.CHARGER,
                                              gls_config.COIN, gls_config.BILL, gls_config.READER, gls_config.GARAGE))
                device_list = curs.fetchall()

                # 등록카드 검사 쿼리
                check_card_qry = "SELECT count(*) AS 'check' FROM gl_card WHERE `card_num` = %s"

                # 정지카드 검사 쿼리
                check_black_card_qry = "SELECT count(*) AS 'check' FROM gl_card_blacklist WHERE `card_num` = %s"

                for device in device_list:
                    if self.USE_EACH:
                        # 세차 장비 동작 상태 전송
                        if (device['type'] == gls_config.SELF or device['type'] == gls_config.AIR
                                or device['type'] == gls_config.MATE or device['type'] == gls_config.READER or device['type'] == gls_config.GARAGE):

                            # 동작상태 호출 프로토콜 생성
                            trans = "GL017RD"
                            trans += str(gls_config.MANAGER_CODE)       # 관리업체 번호
                            trans += str(device['type']).rjust(2, "0")  # 장비 타입
                            trans += str(device['addr'])                # 장비 주소
                            trans += self.get_checksum(trans)           # 체크섬
                            trans += "CH"                               # ETX
                            trans = trans.encode("utf-8")               # 인코딩

                            print("trans : ", trans)
                            try:
                                # 임시 저장 딕셔너리
                                temp_state = OrderedDict()

                                # 딕셔너리 초기화
                                temp_state['state'] = '0'           # 동작 상태
                                temp_state['start_time'] = '0'      # 시작 시간
                                temp_state['current_cash'] = '0'    # 투입금액 - 현금
                                temp_state['current_card'] = '0'    # 투입금액 - 카드
                                temp_state['current_master'] = '0'  # 투입금액 - 마스터
                                temp_state['use_cash'] = '0'        # 사용금액 - 현금
                                temp_state['use_card'] = '0'        # 사용금액 - 카드
                                temp_state['use_master'] = '0'      # 사용금액 - 마스터
                                temp_state['remain_time'] = '0'     # 남은 시간
                                temp_state['card_num'] = '0'        # 카드번호
                                temp_state['sales'] = '0'           # 당일 매출

                                # 기본 정보 저장
                                temp_state['device_type'] = device['type']
                                temp_state['device_addr'] = device['addr']
                                temp_state['connect'] = '0'        # 통신 상태

                                line = []
                                ser.write(bytes(trans))

                                while 1:
                                    temp = ser.read()
                                    if temp:
                                        line.append(temp.decode('utf-8'))
                                    else:
                                        orgin = ''.join(line)
                                        state = orgin.replace(" ", "0")
                                        break
                                stx = state[0:2]

                                state_len = len(state)

                                if stx == 'GL':
                                    print("state : ", state)

                                    # 통신 상태 저장
                                    temp_state['connect'] = '1'

                                    # 셀프 금일 매출 저장
                                    if state[5] == 'S':
                                        get_self_sales_q = "SELECT (SUM(`use_cash`) + SUM(`use_card`)) * 100 AS 'sales' FROM gl_self_state " \
                                                           "WHERE `end_time` > date_format(curdate( ), '%%Y-%%m-%%d' ) AND `device_addr` = %s"
                                        curs.execute(get_self_sales_q, device['addr'])
                                        self_res = curs.fetchone()

                                        if self_res['sales']:
                                            temp_state['sales'] = int(self_res['sales'])

                                    # Garage 금일 매출 저장
                                    if state[5] == 'G':
                                        get_garage_sales_q = "SELECT (SUM(`use_cash`) + SUM(`use_card`)) * 100 AS 'sales' FROM gl_garage_state " \
                                                             "WHERE `end_time` > date_format(curdate( ), '%%Y-%%m-%%d' ) AND `device_addr` = %s"
                                        curs.execute(get_garage_sales_q, device['addr'])
                                        garage_res = curs.fetchone()

                                        if garage_res['sales']:
                                            temp_state['sales'] = int(garage_res['sales'])

                                    # 진공 금일 매출 저장
                                    if state[5] == 'V':
                                        get_air_sales_q = "SELECT (SUM(`air_cash`) + SUM(`air_card`)) * 100 AS 'sales' FROM gl_air_state " \
                                                          "WHERE `end_time` > date_format(curdate( ), '%%Y-%%m-%%d' ) AND `device_addr` = %s"
                                        curs.execute(get_air_sales_q, device['addr'])
                                        air_res = curs.fetchone()

                                        if air_res['sales']:
                                            temp_state['sales'] = int(air_res['sales'])

                                    # 매트 금일 매출 저장
                                    if state[5] == 'M':
                                        get_mate_sales_q = "SELECT (SUM(`mate_cash`) + SUM(`mate_card`)) * 100 AS 'sales' FROM gl_mate_state " \
                                                           "WHERE `end_time` > date_format(curdate( ), '%%Y-%%m-%%d' ) AND `device_addr` = %s"
                                        curs.execute(get_mate_sales_q, device['addr'])
                                        mate_res = curs.fetchone()

                                        if mate_res['sales']:
                                            temp_state['sales'] = int(mate_res['sales'])

                                    # 리더기 금일 매출 저장
                                    if state[5] == 'R':
                                        get_reader_sales_q = "SELECT (SUM(`reader_cash`) + SUM(`reader_card`)) * 100 AS 'sales' FROM gl_reader_state " \
                                                             "WHERE `end_time` > date_format(curdate( ), '%%Y-%%m-%%d' ) AND `device_addr` = %s"
                                        curs.execute(get_reader_sales_q, device['addr'])
                                        reader_res = curs.fetchone()

                                        if reader_res['sales']:
                                            temp_state['sales'] = int(reader_res['sales'])

                                    # 셀프 / Garage 동작 상태 저장
                                    if (state[5:7] == 'SR' or state[5:7] == 'GR') and state[62:64] == 'CH' and state_len == 64:
                                        check_sum = str(self.get_checksum(orgin[:60])).replace(" ", "0")
                                        res_check_sum = state[60:62]
                                        if check_sum == res_check_sum:
                                            temp_state['state'] = state[11]
                                            temp_state['start_time'] = str(state[12:14]) + ":" + str(state[14:16]) + ":" + str(state[16:18])
                                            temp_state['current_cash'] = int(state[18:23]) * 100
                                            temp_state['current_card'] = int(state[23:28]) * 100
                                            temp_state['current_master'] = int(state[28:33]) * 100
                                            temp_state['use_cash'] = int(state[33:38]) * 100
                                            temp_state['use_card'] = int(state[38:43]) * 100
                                            temp_state['use_master'] = int(state[43:48]) * 100
                                            temp_state['remain_time'] = state[48:52]
                                            temp_state['card_num'] = state[52:60]

                                            # 등록 카드 사용 기능
                                            card_check = ''
                                            black_check = ''
                                            if gls_config.ENABLE_CARD:
                                                # 정지 카드 검사
                                                curs.execute(check_black_card_qry, temp_state['card_num'])
                                                black_card_res = curs.fetchall()
                                                for black_card in black_card_res:
                                                    black_check = black_card['check']
                                            else:
                                                # 등록 카드 검사
                                                curs.execute(check_card_qry, temp_state['card_num'])
                                                check_card_res = curs.fetchall()
                                                for check_card in check_card_res:
                                                    card_check = check_card['check']

                                                # 정지 카드 검사
                                                curs.execute(check_black_card_qry, temp_state['card_num'])
                                                black_card_res = curs.fetchall()
                                                for black_card in black_card_res:
                                                    black_check = black_card['check']

                                            # 현재 카드 사용 중지 명령
                                            if (card_check == 0 or black_check == 1) and temp_state['use_master'] == 0:
                                                trans = "GL017ER"
                                                trans += str(gls_config.MANAGER_CODE)
                                                trans += str(device['type']).rjust(2, "0")
                                                trans += str(device['addr'])
                                                trans += self.get_checksum(trans)
                                                trans += "CH"  # ETX
                                                trans = trans.encode("utf-8")
                                                state = ser.readline(ser.write(bytes(trans)))

                                    # 진공 / 매트 / 리더(매트) 동작 상태 저장
                                    if (state[5:7] == 'VR' or state[5:7] == 'MR' or state[5:7] == 'RR') and state[61:63] == 'CH' and state_len == 63:
                                        check_sum = str(self.get_checksum(orgin[:59])).replace(" ", "0")
                                        res_check_sum = state[59:61]
                                        if check_sum == res_check_sum:
                                            temp_state['state'] = '1'
                                            temp_state['start_time'] = str(state[11:13]) + ":" + str(state[13:15]) + ":" + str(state[15:17])
                                            temp_state['current_cash'] = int(state[17:22]) * 100
                                            temp_state['current_card'] = int(state[22:27]) * 100
                                            temp_state['current_master'] = int(state[27:32]) * 100
                                            temp_state['use_cash'] = int(state[32:37]) * 100
                                            temp_state['use_card'] = int(state[37:42]) * 100
                                            temp_state['use_master'] = int(state[42:47]) * 100
                                            temp_state['remain_time'] = state[47:51]
                                            temp_state['card_num'] = state[51:59]

                                            # 등록 카드 사용 기능
                                            card_check = ''
                                            black_check = ''
                                            if gls_config.ENABLE_CARD:
                                                # 정지 카드 검사
                                                curs.execute(check_black_card_qry, temp_state['card_num'])
                                                black_card_res = curs.fetchall()
                                                for black_card in black_card_res:
                                                    black_check = black_card['check']
                                            else:
                                                # 등록 카드 검사
                                                curs.execute(check_card_qry, temp_state['card_num'])
                                                check_card_res = curs.fetchall()
                                                for check_card in check_card_res:
                                                    card_check = check_card['check']

                                                # 정지 카드 검사
                                                curs.execute(check_black_card_qry, temp_state['card_num'])
                                                black_card_res = curs.fetchall()
                                                for black_card in black_card_res:
                                                    black_check = black_card['check']

                                            # 현재 카드 사용 중지 명령
                                            if (card_check == 0 or black_check == 1) and temp_state['use_master'] == 0:
                                                trans = "GL017ER"
                                                trans += str(gls_config.MANAGER_CODE)
                                                trans += str(device['type']).rjust(2, "0")
                                                trans += str(device['addr'])
                                                trans += self.get_checksum(trans)
                                                trans += "CH"  # ETX
                                                trans = trans.encode("utf-8")
                                                state = ser.readline(ser.write(bytes(trans)))

                                    # 셀프 저장값 있는 데이터
                                    if state[5:7] == 'SW' and state[75:77] == 'CH' and state_len == 77:
                                        check_sum = str(self.get_checksum(orgin[:73])).replace(" ", "0")
                                        res_check_sum = state[73:75]
                                        if check_sum == res_check_sum:
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            s_h = state[20:22]
                                            s_m = state[22:24]
                                            s_s = state[24:26]
                                            e_h = state[26:28]
                                            e_m = state[28:30]
                                            e_s = state[30:32]
                                            card_num = state[32:40]
                                            remain_card = state[40:45]
                                            card_use = state[45:49]
                                            cash_use = state[49:53]
                                            master_use = state[53:57]
                                            self_time = state[57:61]
                                            foam_time = state[61:65]
                                            under_time = state[65:69]
                                            coating_time = state[69:73]
                                            start_time = "20" + year + "-" + month + "-" + day + " " \
                                                         + s_h + ":" + s_m + ":" + s_s
                                            end_time = "20" + year + "-" + month + "-" + day + " " \
                                                       + e_h + ":" + e_m + ":" + e_s

                                            # 시간 값 검사
                                            # 현재 시간 정보 추출
                                            t_year = datetime.today().strftime('%y')
                                            t_month = datetime.today().strftime('%m')
                                            t_day = datetime.today().strftime('%d')
                                            t_hour = datetime.today().strftime('%H')
                                            t_minute = datetime.today().strftime('%M')
                                            t_second = datetime.today().strftime('%S')
                                            if t_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31 or e_m != t_minute:
                                                end_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                                use_second = int(self_time) + int(foam_time) + int(under_time) + int(coating_time)
                                                start_time = datetime.today() - timedelta(seconds=use_second)

                                                # 시간 설정 값 보내기
                                                time_trans = "GL029TS"
                                                time_trans += str(gls_config.MANAGER_CODE)
                                                time_trans += str(device['type']).rjust(2, "0")
                                                time_trans += str(device['addr'])
                                                time_trans += str(t_year)
                                                time_trans += str(t_month)
                                                time_trans += str(t_day)
                                                time_trans += str(t_hour)
                                                time_trans += str(t_minute)
                                                time_trans += str(t_second)
                                                time_trans += self.get_checksum(time_trans)
                                                time_trans += "CH"  # ETX
                                                time_trans = time_trans.encode("utf-8")
                                                res = ser.readline(ser.write(bytes(time_trans)) + 100)
                                                print("Time Trans : ", time_trans)
                                                print("Time Set : ", res)

                                            # 데이터 저장
                                            self_insert = "INSERT INTO gl_self_state(`device_addr`, `card_num`, " \
                                                          "`self_time`, `under_time`, `foam_time`, `coating_time`, " \
                                                          "`use_cash`, `use_card`, `remain_card`, `master_card`, " \
                                                          "`start_time`, `end_time`) VALUES " \
                                                          "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                            curs.execute(self_insert, (device['addr'], card_num, self_time, under_time,
                                                                       foam_time, coating_time, cash_use, card_use,
                                                                       remain_card, master_use, start_time, end_time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, "0")
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans)) + 20)

                                    # 진공 저장값 있는 데이터
                                    if state[5:7] == 'VW' and state[59:61] == 'CH' and state_len == 61:
                                        check_sum = str(self.get_checksum(orgin[:57])).replace(" ", "0")
                                        res_check_sum = state[57:59]
                                        if check_sum == res_check_sum:
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            s_h = state[20:22]
                                            s_m = state[22:24]
                                            s_s = state[24:26]
                                            e_h = state[26:28]
                                            e_m = state[28:30]
                                            e_s = state[30:32]
                                            card_num = state[32:40]
                                            remain_card = state[40:45]
                                            card_use = state[45:49]
                                            cash_use = state[49:53]
                                            master_use = state[53:57]
                                            start_time = "20" + year + "-" + month + "-" + day + " " \
                                                         + s_h + ":" + s_m + ":" + s_s
                                            end_time = "20" + year + "-" + month + "-" + day + " " \
                                                       + e_h + ":" + e_m + ":" + e_s

                                            # 시간 값 검사
                                            # 현재 시간 정보 추출
                                            t_year = datetime.today().strftime('%y')
                                            t_month = datetime.today().strftime('%m')
                                            t_day = datetime.today().strftime('%d')
                                            t_hour = datetime.today().strftime('%H')
                                            t_minute = datetime.today().strftime('%M')
                                            t_second = datetime.today().strftime('%S')
                                            if t_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31 or e_m != t_minute:
                                                start_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                                end_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

                                                # 시간 설정 값 보내기
                                                time_trans = "GL029TS"
                                                time_trans += str(gls_config.MANAGER_CODE)
                                                time_trans += str(device['type']).rjust(2, "0")
                                                time_trans += str(device['addr'])
                                                time_trans += str(t_year)
                                                time_trans += str(t_month)
                                                time_trans += str(t_day)
                                                time_trans += str(t_hour)
                                                time_trans += str(t_minute)
                                                time_trans += str(t_second)
                                                time_trans += self.get_checksum(time_trans)
                                                time_trans += "CH"  # ETX
                                                time_trans = time_trans.encode("utf-8")
                                                res = ser.readline(ser.write(bytes(time_trans)) + 100)
                                                print("Time Trans : ", time_trans)
                                                print("Time Set : ", res)

                                            # 데이터 저장
                                            air_insert = "INSERT INTO gl_air_state(`device_addr`, `card_num`, " \
                                                         "`air_cash`, `air_card`, `remain_card`, " \
                                                         "`master_card`, `start_time`, `end_time`) " \
                                                         "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                            curs.execute(air_insert,
                                                         (device['addr'], card_num, cash_use, card_use, remain_card,
                                                          master_use, start_time, end_time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, '0')
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans))+ 20)

                                    # 매트 저장값 있는 데이터
                                    if state[5:7] == 'MW' and state[59:61] == 'CH' and state_len == 61:
                                        check_sum = str(self.get_checksum(orgin[:57])).replace(" ", "0")
                                        res_check_sum = state[57:59]
                                        if check_sum == res_check_sum:
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            s_h = state[20:22]
                                            s_m = state[22:24]
                                            s_s = state[24:26]
                                            e_h = state[26:28]
                                            e_m = state[28:30]
                                            e_s = state[30:32]
                                            card_num = state[32:40]
                                            remain_card = state[40:45]
                                            card_use = state[45:49]
                                            cash_use = state[49:53]
                                            master_use = state[53:57]
                                            start_time = "20" + year + "-" + month + "-" + day + " " \
                                                         + s_h + ":" + s_m + ":" + s_s
                                            end_time = "20" + year + "-" + month + "-" + day + " " \
                                                       + e_h + ":" + e_m + ":" + e_s

                                            # 시간 값 검사
                                            # 현재 시간 정보 추출
                                            t_year = datetime.today().strftime('%y')
                                            t_month = datetime.today().strftime('%m')
                                            t_day = datetime.today().strftime('%d')
                                            t_hour = datetime.today().strftime('%H')
                                            t_minute = datetime.today().strftime('%M')
                                            t_second = datetime.today().strftime('%S')
                                            if t_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31 or e_m != t_minute:
                                                start_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                                end_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

                                                # 시간 설정 값 보내기
                                                time_trans = "GL029TS"
                                                time_trans += str(gls_config.MANAGER_CODE)
                                                time_trans += str(device['type']).rjust(2, "0")
                                                time_trans += str(device['addr'])
                                                time_trans += str(t_year)
                                                time_trans += str(t_month)
                                                time_trans += str(t_day)
                                                time_trans += str(t_hour)
                                                time_trans += str(t_minute)
                                                time_trans += str(t_second)
                                                time_trans += self.get_checksum(time_trans)
                                                time_trans += "CH"  # ETX
                                                time_trans = time_trans.encode("utf-8")
                                                res = ser.readline(ser.write(bytes(time_trans)) + 100)
                                                print("Time Trans : ", time_trans)
                                                print("Time Set : ", res)

                                            mate_insert = "INSERT INTO gl_mate_state(`device_addr`, `card_num`, " \
                                                          "`mate_cash`, `mate_card`, `remain_card`, " \
                                                          "`master_card`, `start_time`, `end_time`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                            curs.execute(mate_insert,
                                                         (device['addr'], card_num, cash_use, card_use,
                                                          remain_card, master_use, start_time, end_time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, '0')
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans))+ 20)

                                    # 리더기 저장값 있는 데이터
                                    if state[5:7] == 'RW' and state[59:61] == 'CH' and state_len == 61:
                                        check_sum = str(self.get_checksum(orgin[:57])).replace(" ", "0")
                                        res_check_sum = state[57:59]
                                        if check_sum == res_check_sum:
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            s_h = state[20:22]
                                            s_m = state[22:24]
                                            s_s = state[24:26]
                                            e_h = state[26:28]
                                            e_m = state[28:30]
                                            e_s = state[30:32]
                                            card_num = state[32:40]
                                            remain_card = state[40:45]
                                            card_use = state[45:49]
                                            cash_use = state[49:53]
                                            master_use = state[53:57]
                                            start_time = "20" + year + "-" + month + "-" + day + " " \
                                                         + s_h + ":" + s_m + ":" + s_s
                                            end_time = "20" + year + "-" + month + "-" + day + " " \
                                                       + e_h + ":" + e_m + ":" + e_s

                                            # 시간 값 검사
                                            # 현재 시간 정보 추출
                                            t_year = datetime.today().strftime('%y')
                                            t_month = datetime.today().strftime('%m')
                                            t_day = datetime.today().strftime('%d')
                                            t_hour = datetime.today().strftime('%H')
                                            t_minute = datetime.today().strftime('%M')
                                            t_second = datetime.today().strftime('%S')
                                            if t_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31 or e_m != t_minute:
                                                start_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                                end_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

                                                # 시간 설정 값 보내기
                                                time_trans = "GL029TS"
                                                time_trans += str(gls_config.MANAGER_CODE)
                                                time_trans += str(device['type']).rjust(2, "0")
                                                time_trans += str(device['addr'])
                                                time_trans += str(t_year)
                                                time_trans += str(t_month)
                                                time_trans += str(t_day)
                                                time_trans += str(t_hour)
                                                time_trans += str(t_minute)
                                                time_trans += str(t_second)
                                                time_trans += self.get_checksum(time_trans)
                                                time_trans += "CH"  # ETX
                                                time_trans = time_trans.encode("utf-8")
                                                res = ser.readline(ser.write(bytes(time_trans)) + 100)
                                                print("Time Trans : ", time_trans)
                                                print("Time Set : ", res)

                                            mate_insert = "INSERT INTO gl_reader_state(`device_addr`, `card_num`, " \
                                                          "`reader_cash`, `reader_card`, `remain_card`, " \
                                                          "`master_card`, `start_time`, `end_time`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                            curs.execute(mate_insert,
                                                         (device['addr'], card_num, cash_use, card_use,
                                                          remain_card, master_use, start_time, end_time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, '0')
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans)) + 20)

                                    # Garage 저장값 있는 데이터
                                    if state[5:7] == 'GW' and state[89:91] == 'CH' and state_len == 91:
                                        check_sum = str(self.get_checksum(orgin[:87])).replace(" ", "0")
                                        res_check_sum = state[87:89]
                                        if check_sum == res_check_sum:
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            s_h = state[20:22]
                                            s_m = state[22:24]
                                            s_s = state[24:26]
                                            e_h = state[26:28]
                                            e_m = state[28:30]
                                            e_s = state[30:32]
                                            card_num = state[32:40]
                                            remain_card = state[40:45]
                                            card_use = state[45:49]
                                            cash_use = state[49:53]
                                            master_use = state[53:57]
                                            self_time = state[57:62]
                                            foam_time = state[62:67]
                                            under_time = state[67:72]
                                            coating_time = state[72:77]
                                            air_time = state[77:82]
                                            airgun_time = state[82:87]
                                            start_time = "20" + year + "-" + month + "-" + day + " " \
                                                         + s_h + ":" + s_m + ":" + s_s
                                            end_time = "20" + year + "-" + month + "-" + day + " " \
                                                       + e_h + ":" + e_m + ":" + e_s

                                            # 시간 값 검사
                                            # 현재 시간 정보 추출
                                            t_year = datetime.today().strftime('%y')
                                            t_month = datetime.today().strftime('%m')
                                            t_day = datetime.today().strftime('%d')
                                            t_hour = datetime.today().strftime('%H')
                                            t_minute = datetime.today().strftime('%M')
                                            t_second = datetime.today().strftime('%S')
                                            if t_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31 or e_m != t_minute:
                                                start_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                                end_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

                                                # 시간 설정 값 보내기
                                                time_trans = "GL029TS"
                                                time_trans += str(gls_config.MANAGER_CODE)
                                                time_trans += str(device['type']).rjust(2, "0")
                                                time_trans += str(device['addr'])
                                                time_trans += str(t_year)
                                                time_trans += str(t_month)
                                                time_trans += str(t_day)
                                                time_trans += str(t_hour)
                                                time_trans += str(t_minute)
                                                time_trans += str(t_second)
                                                time_trans += self.get_checksum(time_trans)
                                                time_trans += "CH"  # ETX
                                                time_trans = time_trans.encode("utf-8")
                                                res = ser.readline(ser.write(bytes(time_trans)) + 100)
                                                print("Time Trans : ", time_trans)
                                                print("Time Set : ", res)

                                            garage_insert = "INSERT INTO gl_garage_state(`device_addr`, `card_num`, `remain_card`, `use_card`, " \
                                                            "`use_cash`, `use_master`, `self_time`, `foam_time`, `under_time`, `coating_time`, " \
                                                            "`air_time`, `airgun_time`, `start_time`, `end_time`) " \
                                                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                                            curs.execute(garage_insert, (device['addr'], card_num, remain_card, card_use, cash_use, master_use,
                                                                         self_time, foam_time, under_time, coating_time, air_time, airgun_time,
                                                                         start_time, end_time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, '0')
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans)) + 20)

                                    # 셀프 / Garage 저장값 없는 대기 동작
                                    if (state[5:7] == 'SN' or state[5:7] == 'GN') and state[39:41] == 'CH' and state_len == 41:
                                        check_sum = str(self.get_checksum(orgin[:37])).replace(" ", "0")
                                        res_check_sum = state[37:39]
                                        if check_sum == res_check_sum:
                                            cash = int(state[12:19]) * 100
                                            card = int(state[19:26]) * 100
                                            master = int(state[26:33]) * 100
                                            version = int(state[33:37])

                                            # 데이터 업데이트
                                            t_update_qry = "UPDATE gl_wash_total SET `cash` = %s, `card` = %s, `master` = %s, `version` = %s " \
                                                           "WHERE `type` = %s AND `addr` = %s"
                                            curs.execute(t_update_qry, (cash, card, master, version, device['type'], device['addr']))
                                            conn.commit()

                                    # 진공 / 매트 / 리더(매트) 저장값 없는 대기 동작
                                    if (state[5:7] == 'VN' or state[5:7] == 'MN' or state[5:7] == 'RN') and state[38:40] == 'CH' and state_len == 40:
                                        check_sum = str(self.get_checksum(orgin[:36])).replace(" ", "0")
                                        res_check_sum = state[36:38]
                                        if check_sum == res_check_sum:
                                            cash = int(state[11:18]) * 100
                                            card = int(state[18:25]) * 100
                                            master = int(state[25:32]) * 100
                                            version = int(state[32:36])

                                            # 데이터 업데이트
                                            t_update_qry = "UPDATE gl_wash_total SET `cash` = %s, `card` = %s, `master` = %s, `version` = %s " \
                                                           "WHERE `type` = %s AND `addr` = %s"
                                            curs.execute(t_update_qry, (cash, card, master, version, device['type'], device['addr']))
                                            conn.commit()

                                state_list.append(temp_state)
                            except Exception as e:
                                print("From get_device_state for 485 : ", e)
                                return
                            finally:
                                pass
                        elif device['type'] == gls_config.CHARGER:

                            # 임시 저장 딕셔너리
                            temp_charger = OrderedDict()

                            # 기본 정보 저장
                            temp_charger['device_type'] = device['type']
                            temp_charger['device_addr'] = device['addr']
                            temp_charger['connect'] = '0'  # 통신상태
                            temp_charger['charge'] = '0'   # 금일 충전액
                            temp_charger['count'] = '0'    # 금일 카드 발급 장수

                            # 동작 상태 호출
                            trans = "GL017RD"
                            trans += str(gls_config.MANAGER_CODE)
                            trans += str(device['type']).rjust(2, '0')
                            trans += str(device['addr'])
                            trans += self.get_checksum(trans)
                            trans += "CH"  # ETX
                            trans = trans.encode("utf-8")
                            print("trans : ", trans)
                            try:
                                ser.write(bytes(trans))

                                line = []

                                while 1:
                                    temp = ser.read()
                                    if temp:
                                        line.append(temp.decode('utf-8'))
                                    else:
                                        orgin = ''.join(line)
                                        state = orgin.replace(" ", "0")
                                        break

                                # 체크섬 정보
                                state_len = len(state)
                                stx = state[0:2]
                                etx = state[59:61]

                                if stx == 'GL' and (state_len == 61 or state_len == 57):
                                    print("state : ", state)
                                    temp_charger['connect'] = '1'
                                    check_sum = str(self.get_checksum(orgin[:57])).replace(" ", "0")
                                    res_check_sum = state[57:59]
                                    if check_sum == res_check_sum:
                                        year = ''
                                        month = ''
                                        day = ''
                                        h = ''
                                        m = ''
                                        s = ''
                                        device_no = ''
                                        kind = ''
                                        card_price = ''
                                        current_money = ''
                                        current_bonus = ''
                                        current_charge = ''
                                        remain_card = ''
                                        card_num = ''
                                        # 충전 정보 저장
                                        if state[5:7] == 'CW' and etx == 'CH':
                                            year = state[14:16]
                                            month = state[16:18]
                                            day = state[18:20]
                                            h = state[20:22]
                                            m = state[22:24]
                                            s = state[24:26]
                                            current_charge = state[30:34]
                                            remain_card = state[34:39]
                                            current_bonus = state[39:44]
                                            card_price = state[44:49]
                                            card_num = state[49:57]
                                            if state[49:57] == '00000000':
                                                kind = '0'
                                                if int(state[44:49]) > int(state[39:44]):
                                                    current_money = int(state[44:49]) - int(state[39:44])
                                                else:
                                                    current_money = '0000'
                                                    current_bonus = state[44:49]
                                            else:
                                                current_money = state[26:30]
                                                kind = '1'


                                            # 시간 값 검사
                                            today_year = datetime.today().strftime('%y')
                                            if today_year != year or int(month) == 0 or int(month) > 12 or int(day) == 0 or int(day) > 31:
                                                time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                            else:
                                                time = "20" + year + "-" + month + "-" + day + " " + h + ":" + m + ":" + s

                                            # device_no 추출
                                            get_device_no_qry = "SELECT `no` FROM gl_device_list " \
                                                                "WHERE `type` = %s AND `addr` = %s"
                                            curs.execute(get_device_no_qry, (gls_config.CHARGER, device['addr']))
                                            get_device_no_res = curs.fetchall()

                                            for get_device_no in get_device_no_res:
                                                device_no = get_device_no['no']

                                            # 충전값 데이터베이스 저장
                                            charger_insert = "INSERT INTO gl_charger_state(`device_no`, `kind`, " \
                                                             "`exhaust_money`, `current_money`, `current_bonus`, " \
                                                             "`current_charge`, `total_money`, `card_num`, `input_date`) " \
                                                             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                            curs.execute(charger_insert, (device_no, kind, card_price, current_money,
                                                                          current_bonus, current_charge, remain_card,
                                                                          card_num, time))
                                            conn.commit()

                                            # OK SIGN
                                            trans = "GL017OK"
                                            trans += str(gls_config.MANAGER_CODE)
                                            trans += str(device['type']).rjust(2, '0')
                                            trans += str(device['addr'])
                                            trans += self.get_checksum(trans)
                                            trans += "CH"  # ETX
                                            trans = trans.encode("utf-8")
                                            state = ser.readline(ser.write(bytes(trans))+ 20)

                            except Exception as e:
                                print("From get_device_state for charger_state except : ", e)
                                temp_charger['connect'] = '0'
                            finally:
                                # 충전기 실시간 모니터링 데이터 전송 값
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

                            # 전송 정보 저장
                            for row in res:
                                if row['charge']:
                                    temp_charger['charge'] = int(row['charge'])
                                temp_charger['count'] = row['count']

                            state_list.append(temp_charger)
        finally:
            conn.close()
            self.FLAG_STATE = 'stop'
            if flag == 'thread':
                pass
                # self.set_time()
            print("1 loop 종료")
        # return state_list

    # noinspection PyMethodMayBeStatic
    def get_device_state(self):
        # if (self.FLAG_MAIN == 'monitor' or self.FLAG_MAIN == 'cancel') and self.FLAG_STATE == 'stop':
        #     self.main_thread(1)
        return state_list

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    4. 셀프 설정 불러오기
    PCB로부터 직접 장비 설정 값을 호출하여 포스에게 전달하는 함수
    각 장비로부터 설정값을 불러와 데이터베이스에 저장된 값과 비교를 하여
    다른 부분이 있으면 새로운 설정을 데이터베이스에 입력한 후 포스에 전달한다.
    * 참고 : config는 update가 아닌 insert로 log 형식으로 누적한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_self_config(self):

        # 반환 값
        self_config_list = []

        time.sleep(3)
        
        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT * FROM gl_self_config WHERE `device_addr` = %s ORDER BY `input_date` DESC " \
                               "LIMIT 1"

                    # 장비 주소 추출
                    curs.execute(query, gls_config.SELF)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        self_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_self_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)  # 회사 분류
                        trans += str(gls_config.SELF).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)  # 체크섬
                        trans += "CH"  # ETX + 개행문자
                        # trans += "CH\r\n"  # ETX + 개행문자
                        trans = trans.encode("utf-8")
                        try:
                            # 485 명령 전송
                            ser.write(bytes(trans))

                            line = []

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            res_len = len(res)

                            # 체크섬 정보
                            stx = res[0:2]
                            etx = res[107:109]
                            check_sum = str(self.get_checksum(orgin[:105])).replace(" ", "0")
                            res_check_sum = res[105:107]

                            if stx == 'GL' and etx == 'CH' and res_len == 109 and res_check_sum == check_sum:
                                print("get_self_config : ", res)

                            # 응답 프르토콜 분할
                                # 디바이스 정보
                                self_config['device_addr'] = res[9:11]  # 장비 주소
                                self_config['state'] = '1'              # 통신 상태

                                # 셀프 설정
                                self_config['self_init_money'] = int(res[11:14]) * 100  # 셀프 초기 동작 금액
                                self_config['self_init_time'] = res[14:17]              # 셀프 초기 동작 시간
                                self_config['self_con_enable'] = res[17]                # 셀프 연속 동작 유무
                                self_config['self_con_money'] = int(res[18:21]) * 100   # 셀프 연속 동작 금액
                                self_config['self_con_time'] = res[21:24]               # 셀프 연속 동작 시간
                                self_config['self_pause_time'] = res[24:27]             # 셀프 일시 정지 시간

                                # 폼 설정
                                self_config['foam_enable'] = res[27]                    # 폼 사용 유무
                                self_config['foam_con_enable'] = res[28]                # 폼 연속 동작 유무
                                self_config['foam_speedier'] = res[29:31]               # 폼 배속제 단게
                                self_config['foam_init_money'] = int(res[31:34]) * 100  # 폼 초기 동작 금액
                                self_config['foam_init_time'] = res[34:37]              # 폼 초기 동작 시간
                                self_config['foam_con_money'] = int(res[37:40]) * 100   # 폼 연속 동작 금액
                                self_config['foam_con_time'] = res[40:43]               # 폼 연속 동작 시간
                                self_config['foam_pause_time'] = res[43:46]             # 폼 일시 정지 시간
                                self_config['foam_end_delay'] = res[46:49]              # 폼 정지 딜레이 시간

                                # 하부 설정
                                self_config['under_enable'] = res[49]                    # 하부 사용 유무
                                self_config['under_con_enable'] = res[50]                # 하부 연속 동작 유무
                                self_config['under_speedier'] = res[51:53]               # 하부 배속제 단계
                                self_config['under_init_money'] = int(res[53:56]) * 100  # 하부 초기 동작 금액
                                self_config['under_init_time'] = res[56:59]              # 하부 초기 동작 시간
                                self_config['under_con_money'] = int(res[59:62]) * 100   # 하부 연속 동작 금액
                                self_config['under_con_time'] = res[62:65]               # 하부 연속 동작 시간
                                self_config['under_pause_time'] = res[65:68]             # 하부 일시 정지 시간

                                # 코팅 설정
                                self_config['coating_enable'] = res[68]                    # 코팅 사용 유무
                                self_config['coating_con_enable'] = res[69]                # 코팅 연속 동작 유무
                                self_config['coating_speedier'] = res[70:72]               # 코팅 배속제 단계
                                self_config['coating_init_money'] = int(res[72:75]) * 100  # 코팅 초기 동작 금액
                                self_config['coating_init_time'] = res[75:78]              # 코팅 초기 동작 시간
                                self_config['coating_con_money'] = int(res[78:81]) * 100   # 코팅 연속 동작 금액
                                self_config['coating_con_time'] = res[81:84]               # 코팅 연속 동작 시간
                                self_config['coating_pause_time'] = res[84:87]             # 코팅 일시 정지 시간

                                # 기타 설정
                                self_config['cycle_money'] = int(res[87:90]) * 100  # 한 사이클 이용 금액
                                self_config['pay_free'] = res[90]  # 유 / 무료 선택
                                self_config['buzzer_time'] = res[91:93]  # 부저 동작 시간
                                self_config['pause_count'] = res[93:95]  # 일시 정지 횟수
                                self_config['secret_enable'] = res[95]  # 비밀 모드 사용 유무
                                self_config['secret_date'] = res[96:99]  # 비밀 모드 사용 일자
                                self_config['speedier_enable'] = res[99]            # 배속 / 정액제 선택
                                self_config['use_type'] = res[100]            # 터치식 / 거치식 선택
                                self_config['set_coating_output'] = res[101]            # 코팅 출력 선택
                                self_config['wipping_enable'] = res[102]  # 위핑 사용 유무
                                self_config['wipping_temperature'] = res[103:105]  # 위핑 설정 온도

                            else:
                                self_config['device_addr'] = str(row['addr'])  # 장비 주소
                                self_config['state'] = '0'                     # 통신 상태
                        # except Exception as e:
                        #     print("From get_self_config except : ", e)
                        finally:
                            pass

                        # 반환할 리스트에 저장
                        self_config_list.append(self_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, row['addr'])
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            db_self_config['device_addr'] = db_row['device_addr']

                            # 셀프 설정
                            db_self_config['self_init_money'] = int(db_row['self_init_money']) * 100
                            db_self_config['self_init_time'] = db_row['self_init_time']
                            db_self_config['self_con_enable'] = db_row['self_con_enable']
                            db_self_config['self_con_money'] = int(db_row['self_con_money']) * 100
                            db_self_config['self_con_time'] = db_row['self_con_time']
                            db_self_config['self_pause_time'] = db_row['self_pause_time']

                            # 폼 설정
                            db_self_config['foam_enable'] = db_row['foam_enable']
                            db_self_config['foam_con_enable'] = db_row['foam_con_enable']
                            db_self_config['foam_speedier'] = db_row['foam_speedier']
                            db_self_config['foam_init_money'] = int(db_row['foam_init_money']) * 100
                            db_self_config['foam_init_time'] = db_row['foam_init_time']
                            db_self_config['foam_con_money'] = int(db_row['foam_con_money']) * 100
                            db_self_config['foam_con_time'] = db_row['foam_con_time']
                            db_self_config['foam_pause_time'] = db_row['foam_pause_time']
                            db_self_config['foam_end_delay'] = db_row['foam_end_delay']

                            # 하부 설정
                            db_self_config['under_enable'] = db_row['under_enable']
                            db_self_config['under_con_enable'] = db_row['under_con_enable']
                            db_self_config['under_speedier'] = db_row['under_speedier']
                            db_self_config['under_init_money'] = int(db_row['under_init_money']) * 100
                            db_self_config['under_init_time'] = db_row['under_init_time']
                            db_self_config['under_con_money'] = int(db_row['under_con_money']) * 100
                            db_self_config['under_con_time'] = db_row['under_con_time']
                            db_self_config['under_pause_time'] = db_row['under_pause_time']

                            # 코팅 설정
                            db_self_config['coating_enable'] = db_row['coating_enable']
                            db_self_config['coating_con_enable'] = db_row['coating_con_enable']
                            db_self_config['coating_speedier'] = db_row['coating_speedier']
                            db_self_config['coating_init_money'] = int(db_row['coating_init_money']) * 100
                            db_self_config['coating_init_time'] = db_row['coating_init_time']
                            db_self_config['coating_con_money'] = int(db_row['coating_con_money']) * 100
                            db_self_config['coating_con_time'] = db_row['coating_con_time']
                            db_self_config['coating_pause_time'] = db_row['coating_pause_time']

                            # 기타 설정
                            db_self_config['cycle_money'] = int(db_row['cycle_money']) * 100
                            db_self_config['speedier_enable'] = db_row['speedier_enable']
                            db_self_config['pay_free'] = db_row['pay_free']
                            db_self_config['use_type'] = db_row['use_type']
                            db_self_config['set_coating_output'] = db_row['set_coating_output']
                            db_self_config['buzzer_time'] = db_row['buzzer_time']
                            db_self_config['pause_count'] = db_row['pause_count']
                            db_self_config['secret_enable'] = db_row['secret_enable']
                            db_self_config['secret_date'] = db_row['secret_date']
                            db_self_config['wipping_enable'] = db_row['wipping_enable']
                            db_self_config['wipping_temperature'] = db_row['wipping_temperature']

                            if self_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                diff = '0'  # 설정 이상 비교 플래그
                                diff_set = OrderedDict()  # 설정 이상 정보 저장 딕셔너리
                                # 기본 설정
                                if db_self_config['device_addr'] != self_config['device_addr']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_addr'] = db_self_config['device_addr']
                                    diff_set['self_addr'] = self_config['device_addr']
                                # 셀프 설정
                                if db_self_config['self_init_money'] != self_config['self_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_init_money'] = db_self_config['self_init_money']
                                    diff_set['self_self_init_money'] = self_config['self_init_money']
                                if db_self_config['self_init_time'] != self_config['self_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_init_time'] = db_self_config['self_init_time']
                                    diff_set['self_self_init_time'] = self_config['self_init_time']
                                if db_self_config['self_con_enable'] != self_config['self_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_con_enable'] = db_self_config['self_con_enable']
                                    diff_set['self_self_con_enable'] = self_config['self_con_enable']
                                if db_self_config['self_con_money'] != self_config['self_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_con_money'] = db_self_config['self_con_money']
                                    diff_set['self_self_con_money'] = self_config['self_con_money']
                                if db_self_config['self_con_time'] != self_config['self_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_con_time'] = db_self_config['self_con_time']
                                    diff_set['self_self_con_time'] = self_config['self_con_time']
                                if db_self_config['self_pause_time'] != self_config['self_pause_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_pause_time'] = db_self_config['self_pause_time']
                                    diff_set['self_self_pause_time'] = self_config['self_pause_time']

                                # 폼 설정
                                if db_self_config['foam_enable'] != self_config['foam_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_enable'] = db_self_config['foam_enable']
                                    diff_set['self_foam_enable'] = self_config['foam_enable']
                                if db_self_config['foam_con_enable'] != self_config['foam_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_con_enable'] = db_self_config['foam_con_enable']
                                    diff_set['self_foam_con_enable'] = self_config['foam_con_enable']
                                if db_self_config['foam_speedier'] != self_config['foam_speedier']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_speedier'] = db_self_config['foam_speedier']
                                    diff_set['self_foam_speedier'] = self_config['foam_speedier']
                                if db_self_config['foam_init_money'] != self_config['foam_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_init_money'] = db_self_config['foam_init_money']
                                    diff_set['self_foam_init_money'] = self_config['foam_init_money']
                                if db_self_config['foam_init_time'] != self_config['foam_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_init_time'] = db_self_config['foam_init_time']
                                    diff_set['self_foam_init_time'] = self_config['foam_init_time']
                                if db_self_config['foam_con_money'] != self_config['foam_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_con_money'] = db_self_config['foam_con_money']
                                    diff_set['self_foam_con_money'] = self_config['foam_con_money']
                                if db_self_config['foam_con_time'] != self_config['foam_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_con_time'] = db_self_config['foam_con_time']
                                    diff_set['self_foam_con_time'] = self_config['foam_con_time']
                                if db_self_config['foam_pause_time'] != self_config['foam_pause_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_pause_time'] = db_self_config['foam_pause_time']
                                    diff_set['self_foam_pause_time'] = self_config['foam_pause_time']
                                if db_self_config['foam_end_delay'] != self_config['foam_end_delay']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_end_delay'] = db_self_config['foam_end_delay']
                                    diff_set['self_foam_end_delay'] = self_config['foam_end_delay']

                                # 하부 설정
                                if db_self_config['under_enable'] != self_config['under_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_enable'] = db_self_config['under_enable']
                                    diff_set['self_under_enable'] = self_config['under_enable']
                                if db_self_config['under_con_enable'] != self_config['under_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_con_enable'] = db_self_config['under_con_enable']
                                    diff_set['self_under_con_enable'] = self_config['under_con_enable']
                                if db_self_config['under_speedier'] != self_config['under_speedier']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_speedier'] = db_self_config['under_speedier']
                                    diff_set['self_under_speedier'] = self_config['under_speedier']
                                if db_self_config['under_init_money'] != self_config['under_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_init_money'] = db_self_config['under_init_money']
                                    diff_set['self_under_init_money'] = self_config['under_init_money']
                                if db_self_config['under_init_time'] != self_config['under_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_init_time'] = db_self_config['under_init_time']
                                    diff_set['self_under_init_time'] = self_config['under_init_time']
                                if db_self_config['under_con_money'] != self_config['under_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_con_money'] = db_self_config['under_con_money']
                                    diff_set['self_under_con_money'] = self_config['under_con_money']
                                if db_self_config['under_con_time'] != self_config['under_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_con_time'] = db_self_config['under_con_time']
                                    diff_set['self_under_con_time'] = self_config['under_con_time']
                                if db_self_config['under_pause_time'] != self_config['under_pause_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_pause_time'] = db_self_config['under_pause_time']
                                    diff_set['self_under_pause_time'] = self_config['under_pause_time']

                                # 코팅 설정
                                if db_self_config['coating_enable'] != self_config['coating_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_enable'] = db_self_config['coating_enable']
                                    diff_set['self_coating_enable'] = self_config['coating_enable']
                                if db_self_config['coating_con_enable'] != self_config['coating_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_con_enable'] = db_self_config['coating_con_enable']
                                    diff_set['self_coating_con_enable'] = self_config['coating_con_enable']
                                if db_self_config['coating_speedier'] != self_config['coating_speedier']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_speedier'] = db_self_config['coating_speedier']
                                    diff_set['self_coating_speedier'] = self_config['coating_speedier']
                                if db_self_config['coating_init_money'] != self_config['coating_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_init_money'] = db_self_config['coating_init_money']
                                    diff_set['self_coating_init_money'] = self_config['coating_init_money']
                                if db_self_config['coating_init_time'] != self_config['coating_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_init_time'] = db_self_config['coating_init_time']
                                    diff_set['self_coating_init_time'] = self_config['coating_init_time']
                                if db_self_config['coating_con_money'] != self_config['coating_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_con_money'] = db_self_config['coating_con_money']
                                    diff_set['self_coating_con_money'] = self_config['coating_con_money']
                                if db_self_config['coating_con_time'] != self_config['coating_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_con_time'] = db_self_config['coating_con_time']
                                    diff_set['self_coating_con_time'] = self_config['coating_con_time']
                                if db_self_config['coating_pause_time'] != self_config['coating_pause_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_pause_time'] = db_self_config['coating_pause_time']
                                    diff_set['self_coating_pause_time'] = self_config['coating_pause_time']

                                # 기타 설정
                                if db_self_config['cycle_money'] != self_config['cycle_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_cycle_money'] = db_self_config['cycle_money']
                                    diff_set['self_cycle_money'] = self_config['cycle_money']
                                if db_self_config['speedier_enable'] != self_config['speedier_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_speedier_enable'] = db_self_config['speedier_enable']
                                    diff_set['self_speedier_enable'] = self_config['speedier_enable']
                                if db_self_config['pay_free'] != self_config['pay_free']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_pay_free'] = db_self_config['pay_free']
                                    diff_set['self_pay_free'] = self_config['pay_free']
                                if db_self_config['buzzer_time'] != self_config['buzzer_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_buzzer_time'] = db_self_config['buzzer_time']
                                    diff_set['self_buzzer_time'] = self_config['buzzer_time']
                                if db_self_config['pause_count'] != self_config['pause_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_pause_count'] = db_self_config['pause_count']
                                    diff_set['self_pause_count'] = self_config['pause_count']
                                if db_self_config['secret_enable'] != self_config['secret_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_secret_enable'] = db_self_config['secret_enable']
                                    diff_set['self_secret_enable'] = self_config['secret_enable']
                                if db_self_config['secret_date'] != self_config['secret_date']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_secret_date'] = db_self_config['secret_date']
                                    diff_set['self_secret_date'] = self_config['secret_date']
                                if db_self_config['wipping_enable'] != self_config['wipping_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_wipping_enable'] = db_self_config['wipping_enable']
                                    diff_set['self_wipping_enable'] = self_config['wipping_enable']
                                if db_self_config['wipping_temperature'] != self_config['wipping_temperature']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_wipping_temperature'] = db_self_config['wipping_temperature']
                                    diff_set['self_wipping_temperature'] = self_config['wipping_temperature']
                                if db_self_config['use_type'] != self_config['use_type']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_use_type'] = db_self_config['use_type']
                                    diff_set['self_use_type'] = self_config['use_type']
                                if db_self_config['set_coating_output'] != self_config['set_coating_output']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_set_coating_output'] = db_self_config['set_coating_output']
                                    diff_set['self_set_coating_output'] = self_config['set_coating_output']

                                # 장비 설정값이 데이터베이스와 다를 때
                                if diff == '1':
                                    insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    new_self_config_qry = "INSERT INTO gl_self_config(`device_addr`, " \
                                                          "`self_init_money`, `self_init_time`, `self_con_enable`, " \
                                                          "`self_con_money`, `self_con_time`, `self_pause_time`, " \
                                                          "`foam_enable`, `foam_con_enable`, `foam_speedier`, " \
                                                          "`foam_init_money`, `foam_init_time`, `foam_con_money`, " \
                                                          "`foam_con_time`, `foam_pause_time`, `foam_end_delay`, " \
                                                          "`under_enable`, `under_con_enable`, `under_speedier`, " \
                                                          "`under_init_money`, `under_init_time`, `under_con_money`, " \
                                                          "`under_con_time`, `under_pause_time`, `coating_enable`, " \
                                                          "`coating_con_enable`, `coating_speedier`, " \
                                                          "`coating_init_money`, `coating_init_time`, " \
                                                          "`coating_con_money`, `coating_con_time`, " \
                                                          "`coating_pause_time`, `cycle_money`, `speedier_enable`, " \
                                                          "`pay_free`, `buzzer_time`, `pause_count`, " \
                                                          "`secret_enable`, `secret_date`, " \
                                                          "`wipping_enable`, `wipping_temperature`, `input_date`, `use_type`, " \
                                                          "`set_coating_output`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                                          "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                                          "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                                          "%s, %s, %s, %s)"
                                    curs.execute(new_self_config_qry, (self_config['device_addr'],
                                                                       str(self_config['self_init_money'] // 100).rjust(3,'0'),
                                                                       self_config['self_init_time'],
                                                                       self_config['self_con_enable'],
                                                                       str(self_config['self_con_money'] // 100).rjust(3, '0'),
                                                                       self_config['self_con_time'],
                                                                       self_config['self_pause_time'],
                                                                       self_config['foam_enable'],
                                                                       self_config['foam_con_enable'],
                                                                       self_config['foam_speedier'],
                                                                       str(self_config['foam_init_money'] // 100).rjust(3, '0'),
                                                                       self_config['foam_init_time'],
                                                                       str(self_config['foam_con_money'] // 100).rjust(3, '0'),
                                                                       self_config['foam_con_time'],
                                                                       self_config['foam_pause_time'],
                                                                       self_config['foam_end_delay'],
                                                                       self_config['under_enable'],
                                                                       self_config['under_con_enable'],
                                                                       self_config['under_speedier'],
                                                                       str(self_config['under_init_money'] // 100).rjust(3, '0'),
                                                                       self_config['under_init_time'],
                                                                       str(self_config['under_con_money'] // 100).rjust(3, '0'),
                                                                       self_config['under_con_time'],
                                                                       self_config['under_pause_time'],
                                                                       self_config['coating_enable'],
                                                                       self_config['coating_con_enable'],
                                                                       self_config['coating_speedier'],
                                                                       str(self_config['coating_init_money'] // 100).rjust(3, '0'),
                                                                       self_config['coating_init_time'],
                                                                       str(self_config['coating_con_money'] // 100).rjust(3, '0'),
                                                                       self_config['coating_con_time'],
                                                                       self_config['coating_pause_time'],
                                                                       str(self_config['cycle_money'] // 100).rjust(3, '0'),
                                                                       self_config['speedier_enable'],
                                                                       self_config['pay_free'],
                                                                       self_config['buzzer_time'],
                                                                       self_config['pause_count'],
                                                                       # self_config['shop_pw'],
                                                                       self_config['secret_enable'],
                                                                       self_config['secret_date'],
                                                                       self_config['wipping_enable'],
                                                                       self_config['wipping_temperature'],
                                                                       insert_input_date,
                                                                       self_config['use_type'],
                                                                       self_config['set_coating_output']))
                                    conn.commit()
            finally:
                conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
        finally:
            # self.main_thread(1)
            pass
        return {'result': self_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    5. 셀프 설정
    포스로부터 설정값을 전달받아 형식에 맞게 파싱한 후 
    DB에 저장하고, 485 장치에 저장한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_self_config(self, args):
        # 반환 값
        returun_res = '1'
        time.sleep(1)
        print(args)

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')                            # 장비 번호
        self_init_money = str(int(args['self_init_money']) // 100).rjust(3, '0')        # 셀프 초기 동작 금액
        self_init_time = str(args['self_init_time']).rjust(3, '0')                      # 셀프 초기 동작 시간
        self_con_enable = args['self_con_enable']                                       # 셀프 연속 동작 유무
        self_con_money = str(int(args['self_con_money']) // 100).rjust(3, '0')          # 셀프 연속 동작 금액
        self_con_time = str(args['self_con_time']).rjust(3, '0')                        # 셀프 연속 동작 시간
        self_pause_time = str(args['self_pause_time']).rjust(3, '0')                    # 셀프 일시 정지 시간
        foam_enable = args['foam_enable']                                               # 폼 사용 유무
        foam_con_enable = args['foam_con_enable']                                       # 폼 연속 동작 유무
        foam_speedier = str(args['foam_speedier']).rjust(2, '0')                        # 폼 배속제 단계
        foam_init_money = str(int(args['foam_init_money']) // 100).rjust(3, '0')        # 폼 초기 동작 금액
        foam_init_time = str(args['foam_init_time']).rjust(3, '0')                      # 폼 초기 동작 시간
        foam_con_money = str(int(args['foam_con_money']) // 100).rjust(3, '0')          # 폼 연속 동작 금액
        foam_con_time = str(args['foam_con_time']).rjust(3, '0')                        # 폼 연속 동작 시간
        foam_pause_time = str(args['foam_pause_time']).rjust(3, '0')                    # 폼 일시 정지 시간
        foam_end_delay = str(args['foam_end_delay']).rjust(3, '0')                      # 폼 종료 딜레이 시간
        under_enable = args['under_enable']                                             # 하부 사용 유무
        under_con_enable = args['under_con_enable']                                     # 하부 연속 동작 유무
        under_speedier = str(args['under_speedier']).rjust(2, '0')                      # 하부 배속제 단계
        under_init_money = str(int(args['under_init_money']) // 100).rjust(3, '0')      # 하부 초기 동작 금액
        under_init_time = str(args['under_init_time']).rjust(3, '0')                    # 하부 초기 동작 시간
        under_con_money = str(int(args['under_con_money']) // 100).rjust(3, '0')        # 하부 연속 동작 금액
        under_con_time = str(args['under_con_time']).rjust(3, '0')                      # 하부 연속 동작 시간
        under_pause_time = str(args['under_pause_time']).rjust(3, '0')                  # 하부 일시 정지 시간
        coating_enable = args['coating_enable']                                         # 코팅 사용 유무
        coating_con_enable = args['coating_con_enable']                                 # 코딩 연속 동작 유무
        coating_speedier = str(args['coating_speedier']).rjust(2, '0')                  # 코팅 배속제 단계
        coating_init_money = str(int(args['coating_init_money']) // 100).rjust(3, '0')  # 코팅 초기 동작 금액
        coating_init_time = str(args['coating_init_time']).rjust(3, '0')                # 코팅 초기 동작 시간
        coating_con_money = str(int(args['coating_con_money']) // 100).rjust(3, '0')    # 코팅 연속 동작 금액
        coating_con_time = str(args['coating_con_time']).rjust(3, '0')                  # 코팅 연속 동작 시간
        coating_pause_time = str(args['coating_pause_time']).rjust(3, '0')              # 코팅 일시 정지 시간
        cycle_money = str(int(args['cycle_money']) // 100).rjust(3, '0')                # 한 사이클 금액
        speedier_enable = args['speedier_enable']                                       # 배속 / 정액제 사용
        use_type = args['use_type']                                                     # 터치식 / 거치식 선택
        pay_free = args['pay_free']                                                     # 유/ 무료
        buzzer_time = str(args['buzzer_time']).rjust(2, '0')                            # 부저 동작 시간
        pause_count = str(args['pause_count']).rjust(2, '0')                            # 일시 정지 횟수
        set_coating_output = str(args['set_coating_output'])                            # 코팅 출력 선택
        secret_enable = args['secret_enable']                                           # 비밀 모드 사용 유무
        secret_date = str(args['secret_date']).rjust(3, '0')                            # 비밀 모드 사용 일자
        wipping_enable = args['wipping_enable']                                         # 위핑 사용 유무
        wipping_temperature = str(args['wipping_temperature']).rjust(2, '0')            # 위핑 설정 온도

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                # 입력 날짜 생성
                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # DB 저장
                insert_self_config_q = "INSERT INTO gl_self_config(`device_addr`, `self_init_money`, " \
                                      "`self_init_time`, `self_con_enable`, `self_con_money`, `self_con_time`, " \
                                      "`self_pause_time`, `foam_enable`, `foam_con_enable`, `foam_speedier`, " \
                                      "`foam_init_money`, `foam_init_time`, `foam_con_money`, `foam_con_time`, " \
                                      "`foam_pause_time`, `foam_end_delay`, `under_enable`, `under_con_enable`, " \
                                      "`under_speedier`, `under_init_money`, `under_init_time`, `under_con_money`, " \
                                      "`under_con_time`, `under_pause_time`, `coating_enable`, `coating_con_enable`, " \
                                      "`coating_speedier`, `coating_init_money`, `coating_init_time`, " \
                                      "`coating_con_money`, `coating_con_time`, `coating_pause_time`, `cycle_money`, " \
                                      "`speedier_enable`, `pay_free`, `buzzer_time`, `pause_count`, `set_coating_output`, " \
                                      "`secret_enable`, `secret_date`, `wipping_enable`, `wipping_temperature`, " \
                                      "`input_date`, `use_type`) " \
                                      "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                       "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                       "%s, %s, %s, %s, %s, %s, %s, %s)"
                curs.execute(insert_self_config_q, (device_addr, self_init_money, self_init_time, self_con_enable,
                                                    self_con_money, self_con_time, self_pause_time, foam_enable,
                                                    foam_con_enable, foam_speedier, foam_init_money, foam_init_time,
                                                    foam_con_money, foam_con_time, foam_pause_time, foam_end_delay,
                                                    under_enable, under_con_enable, under_speedier, under_init_money,
                                                    under_init_time, under_con_money, under_con_time, under_pause_time,
                                                    coating_enable, coating_con_enable, coating_speedier,
                                                    coating_init_money, coating_init_time, coating_con_money,
                                                    coating_con_time, coating_pause_time, cycle_money, speedier_enable,
                                                    pay_free, buzzer_time, pause_count, set_coating_output, secret_enable,
                                                    secret_date, wipping_enable, wipping_temperature,
                                                    insert_input_date, use_type))
                conn.commit()

                # 485 장비 저장
                trans = "GL111SS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.SELF).rjust(2, "0")
                trans += device_addr
                trans += self_init_money
                trans += self_init_time
                trans += self_con_enable
                trans += self_con_money
                trans += self_con_time
                trans += self_pause_time
                trans += foam_enable
                trans += foam_con_enable
                trans += foam_speedier
                trans += foam_init_money
                trans += foam_init_time
                trans += foam_con_money
                trans += foam_con_time
                trans += foam_pause_time
                trans += foam_end_delay
                trans += under_enable
                trans += under_con_enable
                trans += under_speedier
                trans += under_init_money
                trans += under_init_time
                trans += under_con_money
                trans += under_con_time
                trans += under_pause_time
                trans += coating_enable
                trans += coating_con_enable
                trans += coating_speedier
                trans += coating_init_money
                trans += coating_init_time
                trans += coating_con_money
                trans += coating_con_time
                trans += coating_pause_time
                trans += cycle_money
                trans += pay_free
                trans += buzzer_time
                trans += pause_count
                trans += secret_enable
                trans += secret_date
                trans += speedier_enable
                trans += use_type
                trans += set_coating_output
                trans += wipping_enable
                trans += wipping_temperature
                trans += self.get_checksum(trans)
                trans += "CH\r\n"  # ETX + 개행문자
                trans = trans.encode("utf-8")
                print("set_self_config : ", trans)

                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    print(res)

                except Exception as e:
                    print("transErr : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        # except UnboundLocalError as ex:
        #     print('엑세스 거부', ex)
        #     returun_res = '0'
        # except FileNotFoundError as ex:
        #     print('지정된 포트를 찾을 수 없습니다.', ex)
        #     returun_res = '0'
        # except UnicodeDecodeError as ex1:
        #     print('디코딩 오류', ex1)
        #     returun_res = '0'
        # except Exception as ex1:
        #     print('오류를 알 수 없습니다.', ex1)
        #     returun_res = '0'
        finally:
            pass
        return returun_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    6. 진공 설정 불러오기
    PCB로부터 직접 장비 설정 값을 호출하여 포스에게 전달하는 함수
    각 장비로부터 설정값을 불러와 데이터베이스에 저장된 값과 비교를 하여
    다른 부분이 있으면 새로운 설정을 데이터베이스에 입력한 후 포스에 전달한다.
    * 참고 : config는 update가 아닌 insert로 log 형식으로 누적한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_air_config(self):
        # 반환 값
        air_config_list = []
        time.sleep(1)

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT * FROM gl_air_config WHERE `device_addr` = %s ORDER BY `input_date` DESC " \
                               "LIMIT 1"

                    curs.execute(query, gls_config.AIR)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        air_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_air_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)
                        trans += str(gls_config.AIR).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)
                        trans += "CH"
                        trans = trans.encode("utf-8")

                        try:
                            line = []
                            ser.write(bytes(trans))

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            # 체크섬 정보
                            res_len = len(res)
                            stx = res[0:2]
                            etx = res[33:35]
                            res_check_sum = res[31:33]
                            check_sum = str(self.get_checksum(orgin[:31])).replace(" ", "0")

                            if stx == 'GL' and etx == 'CH' and res_len ==35 and res_check_sum == check_sum:
                                print("get_air_config : ", res)

                                # 응답 프르토콜 분할
                                # 디바이스 정보
                                air_config['device_addr'] = res[9:11]  # 장비 주소
                                air_config['state'] = '1'              # 통신 상태

                                # 설정 값
                                air_config['air_init_money'] = int(res[11:14]) * 100  # 진공 초기 동작 금액
                                air_config['air_init_time'] = res[14:17]              # 진공 초기 동작 시간
                                air_config['air_con_money'] = int(res[17:20]) * 100   # 진공 연속 동작 금액
                                air_config['air_con_time'] = res[20:23]               # 진공 연속 동작 시간
                                air_config['cycle_money'] = int(res[23:26]) * 100     # 한 사이클 이용 금액
                                air_config['buzzer_time'] = res[26:28]                # 부저 동작 시간
                                air_config['air_con_enable'] = res[28]                # 진공 연속 동작 유무
                                air_config['pay_free'] = res[29]                      # 유 /무료 설정
                                air_config['key_enable'] = res[30]                    # 키 사용 유무

                                # CheckSum
                                air_config['check_sum'] = res[31:33]
                            else:
                                air_config['device_addr'] = str(row['addr'])  # 장비 주소
                                air_config['state'] = '0'                     # 통신 상태
                        except Exception as e:
                            print("From get_air_config except : ", e)

                        # 반환할 리스트에 저장
                        air_config_list.append(air_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, row['addr'])
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            db_air_config['device_addr'] = db_row['device_addr']

                            # 설정 값
                            db_air_config['air_init_money'] = int(db_row['air_init_money']) * 100
                            db_air_config['air_init_time'] = db_row['air_init_time']
                            db_air_config['air_con_money'] = int(db_row['air_con_money']) * 100
                            db_air_config['air_con_time'] = db_row['air_con_time']
                            db_air_config['cycle_money'] = int(db_row['air_cycle_money']) * 100
                            db_air_config['buzzer_time'] = db_row['air_buzzer_time']
                            db_air_config['air_con_enable'] = db_row['air_con_enable']
                            db_air_config['pay_free'] = db_row['air_pay_free']
                            db_air_config['key_enable'] = db_row['air_key_enable']

                            if air_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                diff = '0'  # 설정 이상 비교 플래그
                                diff_set = OrderedDict()  # 설정 이상 정보 저장 딕셔너리
                                # 기본 설정
                                if db_air_config['device_addr'] != air_config['device_addr']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_addr'] = db_air_config['device_addr']
                                    diff_set['air_addr'] = air_config['device_addr']
                                # 셀프 설정
                                if db_air_config['air_init_money'] != air_config['air_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_init_money'] = db_air_config['air_init_money']
                                    diff_set['air_init_money'] = air_config['air_init_money']

                                if db_air_config['air_init_time'] != air_config['air_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_init_time'] = db_air_config['air_init_time']
                                    diff_set['air_init_time'] = air_config['air_init_time']

                                if db_air_config['air_con_money'] != air_config['air_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_con_money'] = db_air_config['air_con_money']
                                    diff_set['air_con_money'] = air_config['air_con_money']

                                if db_air_config['air_con_time'] != air_config['air_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_con_time'] = db_air_config['air_con_time']
                                    diff_set['air_con_time'] = air_config['air_con_time']

                                if db_air_config['cycle_money'] != air_config['cycle_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_cycle_money'] = db_air_config['cycle_money']
                                    diff_set['air_cycle_money'] = air_config['cycle_money']

                                if db_air_config['buzzer_time'] != air_config['buzzer_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_buzzer_time'] = db_air_config['buzzer_time']
                                    diff_set['air_buzzer_time'] = air_config['buzzer_time']

                                if db_air_config['air_con_enable'] != air_config['air_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_con_enable'] = db_air_config['air_con_enable']
                                    diff_set['air_con_enable'] = air_config['air_con_enable']

                                if db_air_config['pay_free'] != air_config['pay_free']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_pay_free'] = db_air_config['pay_free']
                                    diff_set['air_pay_free'] = air_config['pay_free']

                                if db_air_config['key_enable'] != air_config['key_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_key_enable'] = db_air_config['key_enable']
                                    diff_set['air_key_enable'] = air_config['key_enable']

                                if diff == '1':
                                    insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    new_air_config_qry = "INSERT INTO gl_air_config(`device_addr`, " \
                                                         "`air_init_money`, `air_init_time`, " \
                                                         "`air_con_money`, `air_con_time`, " \
                                                         "`air_cycle_money`, `air_buzzer_time`, `air_con_enable`," \
                                                         "`air_pay_free`, " \
                                                         "`air_key_enable`, `input_date`) " \
                                                         "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    curs.execute(new_air_config_qry, (air_config['device_addr'],
                                                                      str(air_config['air_init_money'] // 100).rjust(3, '0'),
                                                                      air_config['air_init_time'],
                                                                      str(air_config['air_con_money'] // 100).rjust(3, '0'),
                                                                      air_config['air_con_time'],
                                                                      str(air_config['cycle_money'] // 100).rjust(3, '0'),
                                                                      air_config['buzzer_time'],
                                                                      air_config['air_con_enable'],
                                                                      air_config['pay_free'],
                                                                      air_config['key_enable'],
                                                                      insert_input_date))
                                    conn.commit()
            finally:
                conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
        finally:
            pass

        return {'result': air_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    7. 진공 설정
    포스로부터 설정값을 전달받아 형식에 맞게 파싱한 후
    DB에 저정하고, 485 장비에 저장한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_air_config(self, args):
        # 반환 값
        returun_res = '1'
        time.sleep(1)

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')                    # 장비 주소
        air_init_money = str(int(args['air_init_money']) // 100).rjust(3, '0')  # 진공 초기 동작 금액
        air_init_time = str(args['air_init_time']).rjust(3, '0')                # 진공 초기 동작 시간
        air_con_money = str(int(args['air_con_money']) // 100).rjust(3, '0')    # 진공 연속 동작 금액
        air_con_time = str(args['air_con_time']).rjust(3, '0')                  # 진공 연속 동작 시간
        cycle_money = str(int(args['cycle_money']) // 100).rjust(3, '0')        # 한 사이클 이용 금액
        buzzer_time = str(args['buzzer_time']).rjust(2, '0')                    # 부저 동작 시간
        air_con_enable = args['air_con_enable']                                 # 진공 연속 동작 유무
        pay_free = args['pay_free']                                             # 유/무료 설정
        key_enable = args['key_enable']                                         # 키 사용 유무

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                # 입력 날짜 생성
                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # DB 저장
                insert_air_config_q = "INSERT INTO gl_air_config(`device_addr`, `air_init_money`, " \
                                      "`air_init_time`, `air_con_money`, `air_con_time`, `air_cycle_money`, " \
                                      "`air_buzzer_time`, `air_con_enable`, `air_pay_free`, `air_key_enable`, " \
                                      "`input_date`) " \
                                      "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                curs.execute(insert_air_config_q, (device_addr, air_init_money, air_init_time, air_con_money,
                                                   air_con_time, cycle_money, buzzer_time, air_con_enable, pay_free,
                                                   key_enable, insert_input_date))
                conn.commit()

                trans = "GL037VS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.AIR).rjust(2, '0')
                trans += device_addr
                trans += air_init_money
                trans += air_init_time
                trans += air_con_money
                trans += air_con_time
                trans += cycle_money
                trans += buzzer_time
                trans += air_con_enable
                trans += pay_free
                trans += key_enable
                trans += self.get_checksum(trans)
                trans += "CH"  # ETX
                trans = trans.encode("utf-8")

                try:
                    ser.readline(ser.write(bytes(trans)))

                except Exception as e:
                    print("transErr : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
            returun_res = '0'
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
            returun_res = '0'
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
            returun_res = '0'
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            returun_res = '0'
        finally:
            pass
        return returun_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    8. 매트 설정 불러오기
    PCB로부터 직접 장비 설정 값을 호출하여 포스에게 전달하는 함수
    각 장비로부터 설정값을 불러와 데이터베이스에 저장된 값과 비교를 하여
    다른 부분이 있으면 새로운 설정을 데이터베이스에 입력한 후 포스에 전달한다.
    * 참고 : config는 update가 아닌 insert로 log 형식으로 누적한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_mate_config(self):
        # 반환 값
        mate_config_list = []
        time.sleep(1)

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD, 
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT * FROM gl_mate_config WHERE `device_addr` = %s ORDER BY `input_date` DESC " \
                               "LIMIT 1"

                    # 장비 주소 추출
                    curs.execute(query, gls_config.MATE)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        mate_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_mate_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)
                        trans += str(gls_config.MATE).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)
                        trans += "CH"
                        trans = trans.encode("utf-8")
                        try:
                            ser.write(bytes(trans))

                            line = []

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            # 체크섬 정보
                            res_len = len(res)
                            stx = res[0:2]
                            etx = res[37:39]
                            res_check_sum = res[35:37]
                            check_sum = str(self.get_checksum(orgin[:35])).replace(" ", "0")


                            if stx == 'GL' and etx == 'CH' and res_len == 39 and res_check_sum == check_sum:
                                print("get_mate_config : ", res)

                            # 응답 프르토콜 분할
                                # 디바이스 정보
                                mate_config['device_addr'] = res[9:11]  # 장비 주소
                                mate_config['state'] = '1'              # 통신 상태

                                # 설정 값
                                mate_config['mate_init_money'] = int(res[11:14]) * 100  # 매트 초기 동작 금액
                                mate_config['mate_init_time'] = res[14:17]              # 매트 초기 동작 시간
                                mate_config['mate_con_money'] = int(res[17:20]) * 100   # 매트 연속 동작 금액
                                mate_config['mate_con_time'] = res[20:23]               # 매트 연속 동작 시간
                                mate_config['cycle_money'] = int(res[23:26]) * 100      # 한 사이클 이용 금액
                                mate_config['buzzer_time'] = res[26:28]                 # 부저 동작 시간
                                mate_config['mate_con_enable'] = res[28]                # 매트 연속 동작 유무
                                mate_config['pay_free'] = res[29]                       # 유/무료 설정
                                mate_config['key_enable'] = res[30]                     # 키 사용 유무
                                mate_config['relay_delay'] = res[31:35]                 # 릴레이 딜레이 시간

                                # CheckSum
                                mate_config['check_sum'] = res[35:37]
                            else:
                                mate_config['device_addr'] = str(row['addr'])  # 장비 주소
                                mate_config['state'] = '0'                     # 통신 상태
                        except Exception as e:
                            print("From get_air_config except : ", e)

                        # 반환할 리스트에 저장
                        mate_config_list.append(mate_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, row['addr'])
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            db_mate_config['device_addr'] = db_row['device_addr']

                            # 설정 값
                            db_mate_config['mate_init_money'] = int(db_row['mate_init_money']) * 100
                            db_mate_config['mate_init_time'] = db_row['mate_init_time']
                            db_mate_config['mate_con_money'] = int(db_row['mate_con_money']) * 100
                            db_mate_config['mate_con_time'] = db_row['mate_con_time']
                            db_mate_config['cycle_money'] = int(db_row['mate_cycle_money']) * 100
                            db_mate_config['buzzer_time'] = db_row['mate_buzzer_time']
                            db_mate_config['mate_con_enable'] = db_row['mate_con_enable']
                            db_mate_config['pay_free'] = db_row['mate_pay_free']
                            db_mate_config['key_enable'] = db_row['mate_key_enable']
                            db_mate_config['relay_delay'] = db_row['mate_relay_delay']

                            if mate_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                diff = '0'  # 설정 이상 비교 플래그
                                diff_set = OrderedDict()  # 설정 이상 정보 저장 딕셔너리
                                # 설정 값
                                if db_mate_config['device_addr'] != mate_config['device_addr']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_addr'] = db_mate_config['device_addr']
                                    diff_set['mate_addr'] = mate_config['device_addr']
                                if db_mate_config['mate_init_money'] != mate_config['mate_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_mate_init_money'] = db_mate_config['mate_init_money']
                                    diff_set['mate_init_money'] = mate_config['mate_init_money']

                                if db_mate_config['mate_init_time'] != mate_config['mate_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_mate_init_time'] = db_mate_config['mate_init_time']
                                    diff_set['mate_init_time'] = mate_config['mate_init_time']

                                if db_mate_config['mate_con_money'] != mate_config['mate_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_mate_con_money'] = db_mate_config['mate_con_money']
                                    diff_set['mate_con_money'] = mate_config['mate_con_money']

                                if db_mate_config['mate_con_time'] != mate_config['mate_con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_mate_con_time'] = db_mate_config['mate_con_time']
                                    diff_set['mate_con_time'] = mate_config['mate_con_time']

                                if db_mate_config['cycle_money'] != mate_config['cycle_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_cycle_money'] = db_mate_config['cycle_money']
                                    diff_set['mate_cycle_money'] = mate_config['cycle_money']

                                if db_mate_config['buzzer_time'] != mate_config['buzzer_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_buzzer_time'] = db_mate_config['buzzer_time']
                                    diff_set['mate_buzzer_time'] = mate_config['buzzer_time']

                                if db_mate_config['mate_con_enable'] != mate_config['mate_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_mate_con_enable'] = db_mate_config['mate_con_enable']
                                    diff_set['mate_con_enable'] = mate_config['mate_con_enable']

                                if db_mate_config['pay_free'] != mate_config['pay_free']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_pay_free'] = db_mate_config['pay_free']
                                    diff_set['mate_pay_free'] = mate_config['pay_free']

                                if db_mate_config['key_enable'] != mate_config['key_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_key_enable'] = db_mate_config['key_enable']
                                    diff_set['mate_key_enable'] = mate_config['key_enable']
                                if db_mate_config['relay_delay'] != mate_config['relay_delay']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_relay_delay'] = db_mate_config['relay_delay']
                                    diff_set['mate_relay_delay'] = mate_config['relay_delay']

                                if diff == '1':
                                    insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    new_mate_config_qry = "INSERT INTO gl_mate_config(`device_addr`, " \
                                                          "`mate_init_money`, `mate_init_time`, " \
                                                          "`mate_con_money`, `mate_con_time`, " \
                                                          "`mate_cycle_money`, `mate_buzzer_time`, `mate_con_enable`," \
                                                          "`mate_pay_free`, " \
                                                          "`mate_key_enable`, `mate_relay_delay`, `input_date`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    curs.execute(new_mate_config_qry, (mate_config['device_addr'],
                                                                      str(mate_config['mate_init_money'] // 100).rjust(3, '0'),
                                                                      mate_config['mate_init_time'],
                                                                      str(mate_config['mate_con_money'] // 100).rjust(3, '0'),
                                                                      mate_config['mate_con_time'],
                                                                      str(mate_config['cycle_money'] // 100).rjust(3, '0'),
                                                                      mate_config['buzzer_time'],
                                                                      mate_config['mate_con_enable'],
                                                                      mate_config['pay_free'],
                                                                      mate_config['key_enable'],
                                                                      mate_config['relay_delay'],
                                                                      insert_input_date))
                                    conn.commit()
            finally:
                conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
        finally:
            pass
        return {'result': mate_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    9. 매트 설정
    포스로부터 설정값을 전달받아 형식에 맞게 파싱한 후
    DB에 저정하고, 485 장비에 저장한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_mate_config(self, args):
        # 반환 값
        returun_res = '1'
        time.sleep(1)

        print(args)

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')                      # 장비 주소
        mate_init_money = str(int(args['mate_init_money']) // 100).rjust(3, '0')  # 매트 초기 동작 금액
        mate_init_time = str(args['mate_init_time']).rjust(3, '0')                # 매트 초기 동작 시간
        mate_con_money = str(int(args['mate_con_money']) // 100).rjust(3, '0')    # 매트 연속 동작 금액
        mate_con_time = str(args['mate_con_time']).rjust(3, '0')                  # 매트 연속 동작 시간
        cycle_money = str(int(args['cycle_money']) // 100).rjust(3, '0')          # 한 사이클 이용 금액
        buzzer_time = str(args['buzzer_time']).rjust(2, '0')                      # 부저 동작 시간
        mate_con_enable = args['mate_con_enable']                                 # 매트 연속 동장 유무
        pay_free = args['pay_free']                                               # 유/무료 설정
        key_enable = args['key_enable']                                           # 키 사용 유무
        relay_delay = str(args['relay_delay']).rjust(4, '0')                      # 릴레이 딜레이 시간


        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD, 
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():
                
                # 입력 날짜 생성
                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # DB 저장
                insert_mate_config_q = "INSERT INTO gl_mate_config(`device_addr`, `mate_init_money`, " \
                                       "`mate_init_time`, `mate_con_money`, `mate_con_time`, `mate_cycle_money`, " \
                                       "`mate_buzzer_time`, `mate_con_enable`, `mate_pay_free`, `mate_key_enable`, " \
                                       "`mate_relay_delay`, `input_date`) " \
                                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                curs.execute(insert_mate_config_q, (device_addr, mate_init_money, mate_init_time, mate_con_money,
                                                   mate_con_time, cycle_money, buzzer_time, mate_con_enable, pay_free,
                                                   key_enable, relay_delay, insert_input_date))
                conn.commit()

                trans = "GL041MS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.MATE).rjust(2, '0')
                trans += device_addr
                trans += mate_init_money
                trans += mate_init_time
                trans += mate_con_money
                trans += mate_con_time
                trans += cycle_money
                trans += buzzer_time
                trans += mate_con_enable
                trans += pay_free
                trans += key_enable
                trans += relay_delay
                trans += self.get_checksum(trans)
                trans += "CH"  # ETX
                trans = trans.encode("utf-8")

                print("mate_set : ", trans)

                try:
                    ser.readline(ser.write(bytes(trans)))

                except Exception as e:
                    print("transErr : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
            returun_res = '0'
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
            returun_res = '0'
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
            returun_res = '0'
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            returun_res = '0'
        finally:
            pass
        return returun_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    10. 충전기 설정 불러오기
    PCB로부터 직접 장비 설정 값을 호출하여 포스에게 전달하는 함수
    각 장비로부터 설정값을 불러와 데이터베이스에 저장된 값과 비교를 하여
    다른 부분이 있으면 새로운 설정을 데이터베이스에 입력한 후 포스에 전달한다.
    * 참고 : 1. config는 update가 아닌 insert로 log 형식으로 누적한다.
             2. bonus가 변경될 경우 default_bonus를 변경하며 전체 장비에 영향을 끼친다. 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_charger_config(self):
        # 반환 값
        charger_config_list = []
        time.sleep(1)

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET,
                                   db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT `device_no`, `shop_pw`, `card_price`, `card_min_price`, " \
                               "`auto_charge_enable`, `auto_charge_price`, `exhaust_charge_enable`, " \
                               "`bonus1`, `bonus2`, `bonus3`, `bonus4`, `bonus5`, `bonus6`, `bonus7`, `bonus8`, " \
                               "`bonus9`, `bonus10`, `addr` AS 'device_addr' " \
                               "FROM gl_charger_config AS config " \
                               "INNER JOIN gl_device_list AS list ON config.`device_no` = list.`no` " \
                               "INNER JOIN gl_charger_bonus AS bonus ON config.`default_bonus_no` = bonus.`no` " \
                               "WHERE list.type = %s AND list.`addr` = %s ORDER BY config.`input_date` DESC LIMIT 1"

                    curs.execute(query, gls_config.CHARGER)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        charger_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_charger_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)
                        trans += str(gls_config.CHARGER).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)
                        trans += "CH"
                        trans = trans.encode("utf-8")
                        print(trans)
                        try:
                            ser.write(bytes(trans))

                            line = []

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            # 체크섬 정보
                            res_len = len(res)
                            stx = res[0:2]
                            etx = res[53:55]
                            res_check_sum = res[51:53]
                            check_sum = str(self.get_checksum(orgin[:51])).replace(" ", "0")

                            if stx == 'GL' and etx == 'CH' and res_len == 55 and check_sum == res_check_sum:
                                print("get_charger_config : ", res)
                                # 응답 프르토콜 분할
                                # 디바이스 정보
                                charger_config['device_addr'] = res[9:11]  # 장비 주소
                                charger_config['state'] = '1'  # 통신 상태

                                # 설정 값
                                charger_config['card_min_price'] = int(res[11:14]) * 100  # 카드 발급 진행 최소 금액
                                charger_config['card_price'] = int(res[14:17]) * 100  # 카드 가격
                                charger_config['auto_charge_enable'] = res[17]  # 자동 충전 기능 사용 여부
                                charger_config['auto_charge_price'] = int(res[18:21]) * 100  # 자동 충전 금액
                                charger_config['bonus1'] = int(res[21:24]) * 100
                                charger_config['bonus2'] = int(res[24:27]) * 100
                                charger_config['bonus3'] = int(res[27:30]) * 100
                                charger_config['bonus4'] = int(res[30:33]) * 100
                                charger_config['bonus5'] = int(res[33:36]) * 100
                                charger_config['bonus6'] = int(res[36:39]) * 100
                                charger_config['bonus7'] = int(res[39:42]) * 100
                                charger_config['bonus8'] = int(res[42:45]) * 100
                                charger_config['bonus9'] = int(res[45:48]) * 100
                                charger_config['bonus10'] = int(res[48:51]) * 100

                            else:
                                charger_config['device_addr'] = str(row['addr'])  # 장비 주소
                                charger_config['state'] = '0'  # 통신 상태
                        except Exception as e:
                            print("From get_air_config except : ", e)

                        # 반환할 리스트에 저장
                        charger_config_list.append(charger_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, (gls_config.CHARGER, row['addr']))
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            device_no = db_row['device_no']
                            db_charger_config['device_addr'] = db_row['device_addr']

                            # 설정 값
                            db_charger_config['card_price'] = int(db_row['card_price']) * 100
                            db_charger_config['card_min_price'] = int(db_row['card_min_price']) * 100
                            db_charger_config['auto_charge_enable'] = db_row['auto_charge_enable']
                            db_charger_config['auto_charge_price'] = int(db_row['auto_charge_price']) * 100
                            db_charger_config['bonus1'] = int(db_row['bonus1']) * 100
                            db_charger_config['bonus2'] = int(db_row['bonus2']) * 100
                            db_charger_config['bonus3'] = int(db_row['bonus3']) * 100
                            db_charger_config['bonus4'] = int(db_row['bonus4']) * 100
                            db_charger_config['bonus5'] = int(db_row['bonus5']) * 100
                            db_charger_config['bonus6'] = int(db_row['bonus6']) * 100
                            db_charger_config['bonus7'] = int(db_row['bonus7']) * 100
                            db_charger_config['bonus8'] = int(db_row['bonus8']) * 100
                            db_charger_config['bonus9'] = int(db_row['bonus9']) * 100
                            db_charger_config['bonus10'] = int(db_row['bonus10']) * 100

                            diff = '0'  # 설정 이상 비교 플래그
                            if charger_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                # 설정 값
                                if charger_config['device_addr'] != db_charger_config['device_addr']:
                                    diff = '1'
                                if charger_config['card_price'] != db_charger_config['card_price']:
                                    diff = '1'
                                if charger_config['card_min_price'] != db_charger_config['card_min_price']:
                                    diff = '1'
                                if charger_config['auto_charge_enable'] != db_charger_config['auto_charge_enable']:
                                    diff = '1'
                                if charger_config['auto_charge_price'] != db_charger_config['auto_charge_price']:
                                    diff = '1'
                                if charger_config['bonus1'] != db_charger_config['bonus1']:
                                    diff = '2'
                                if charger_config['bonus2'] != db_charger_config['bonus2']:
                                    diff = '2'
                                if charger_config['bonus3'] != db_charger_config['bonus3']:
                                    diff = '2'
                                if charger_config['bonus4'] != db_charger_config['bonus4']:
                                    diff = '2'
                                if charger_config['bonus5'] != db_charger_config['bonus5']:
                                    diff = '2'
                                if charger_config['bonus6'] != db_charger_config['bonus6']:
                                    diff = '2'
                                if charger_config['bonus7'] != db_charger_config['bonus7']:
                                    diff = '2'
                                if charger_config['bonus8'] != db_charger_config['bonus8']:
                                    diff = '2'
                                if charger_config['bonus9'] != db_charger_config['bonus9']:
                                    diff = '2'
                                if charger_config['bonus10'] != db_charger_config['bonus10']:
                                    diff = '2'
                            # input_date
                            input_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

                            print(charger_config)
                            print(db_charger_config)

                            # 충전기의 설정 내용이 다를 경우
                            if diff == '1':
                                print("설정이상")
                                update_config_qry = "INSERT INTO gl_charger_config(`device_no`, `card_price`, " \
                                                    "`card_min_price`, `auto_charge_price`, `auto_charge_enable`, " \
                                                    "`input_date`) VALUES (%s, %s, %s, %s, %s, %s)"
                                curs.execute(update_config_qry, (device_no,
                                                                 str(int(charger_config['card_price']) // 100).rjust(3, '0') ,
                                                                 str(int(charger_config['card_min_price']) // 100).rjust(3, '0'),
                                                                 str(int(charger_config['auto_charge_price']) // 100).rjust(3, '0'),
                                                                 charger_config['auto_charge_enable'],
                                                                 input_date))
                                conn.commit()

                            # 보너스의 설정이 다를 경우
                            if diff == '2':
                                update_bonus_qry = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, " \
                                                   "`bonus3` = %s, `bonus4` = %s, `bonus5` = %s, `bonus6` = %s, " \
                                                   "`bonus7` = %s, `bonus8` = %s, `bonus9` = %s, `bonus10` = %s " \
                                                   "WHERE `no` = %s"
                                curs.execute(update_bonus_qry, (str(int(charger_config['bonus1']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus2']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus3']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus4']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus5']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus6']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus7']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus8']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus9']) // 100).rjust(3, '0'),
                                                                str(int(charger_config['bonus10']) // 100).rjust(3, '0'),
                                                                gls_config.DEFAULT_BONUS))
                                conn.commit()

            finally:
                conn.close()
        # except UnboundLocalError as ex:
        #     print('엑세스 거부', ex)
        # except FileNotFoundError as ex:
        #     print('지정된 포트를 찾을 수 없습니다.', ex)
        # except UnicodeDecodeError as ex1:
        #     print('디코딩 오류', ex1)
        # except Exception as ex1:
        #     print('오류를 알 수 없습니다.', ex1)
        finally:
            pass
        return {'result': charger_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    11. 충전기 설정
    포스로부터 설정값을 전달받아 형식에 맞게 파싱한 후
    DB에 저정하고, 485 장비에 저장한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_charger_config(self, args):
        # 반환 값
        time.sleep(1)
        returun_res = '1'

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')  # 장비 주소
        card_price = str(int(int(args['card_price'])) // 100).rjust(3, '0')  # 카드 금액
        card_min_price = str(int(int(args['card_min_price'])) // 100).rjust(3, '0')  # 카드 발급 진행 최소 금액
        auto_charge_enable = args['auto_charge_enable']  # 자동 충전 기능 사용 유무
        auto_charge_price = str(int(args['auto_charge_price']) // 100).rjust(3, '0')  # 자동 충전 금액
        bonus1 = str(int(args['bonus1']) // 100).rjust(3, '0')
        bonus2 = str(int(args['bonus2']) // 100).rjust(3, '0')
        bonus3 = str(int(args['bonus3']) // 100).rjust(3, '0')
        bonus4 = str(int(args['bonus4']) // 100).rjust(3, '0')
        bonus5 = str(int(args['bonus5']) // 100).rjust(3, '0')
        bonus6 = str(int(args['bonus6']) // 100).rjust(3, '0')
        bonus7 = str(int(args['bonus7']) // 100).rjust(3, '0')
        bonus8 = str(int(args['bonus8']) // 100).rjust(3, '0')
        bonus9 = str(int(args['bonus9']) // 100).rjust(3, '0')
        bonus10 = str(int(args['bonus10']) // 100).rjust(3, '0')

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER,
                                   password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET,
                                   db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # device_no 추출
                get_device_no_qry = "SELECT `no` FROM gl_device_list WHERE `type` = %s AND `addr` = %s"
                curs.execute(get_device_no_qry, (gls_config.CHARGER, device_addr))
                get_device_no_res = curs.fetchall()
                for get_device_no in get_device_no_res:
                    device_no = get_device_no['no']

                # shop_no 추출
                get_shop_no_qry = "SELECT `no` FROM gl_shop_info"
                curs.execute(get_shop_no_qry)
                get_shop_no_res = curs.fetchall()
                for shop in get_shop_no_res:
                    shop_no = shop['no']

                # DB 저장
                insert_config_q = "INSERT INTO gl_charger_config(`device_no`, `card_price`, " \
                                  "`card_min_price`, `auto_charge_enable`, `auto_charge_price`, `shop_no`, `input_date`) " \
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                curs.execute(insert_config_q, (device_no, card_price, card_min_price, auto_charge_enable,
                                               auto_charge_price, shop_no, insert_input_date))
                conn.commit()

                # 보너스 설정 값 업데이트
                bonus_query = "UPDATE gl_charger_bonus SET `bonus1` = %s, `bonus2` = %s, `bonus3` = %s, " \
                              "`bonus4` = %s, `bonus5` = %s, `bonus6` = %s, `bonus7` = %s, `bonus8` = %s, " \
                              "`bonus9` = %s, `bonus10` = %s WHERE `no` = %s"
                curs.execute(bonus_query, (bonus1, bonus2, bonus3, bonus4, bonus5, bonus6,
                                           bonus7, bonus8, bonus9, bonus10, gls_config.DEFAULT_BONUS))
                conn.commit()

                # 485 장비 저장
                trans = "GL057CS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.CHARGER).rjust(2, '0')
                trans += device_addr
                trans += card_min_price
                trans += card_price
                trans += auto_charge_enable
                trans += auto_charge_price
                trans += bonus1
                trans += bonus2
                trans += bonus3
                trans += bonus4
                trans += bonus5
                trans += bonus6
                trans += bonus7
                trans += bonus8
                trans += bonus9
                trans += bonus10
                # trans += "00"
                trans += self.get_checksum(trans)
                trans += "CH"  # ETX
                trans = trans.encode("utf-8")

                print("trans : ", trans)

                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!res : ", res)
                    if res:
                        pass
                    else:
                        returun_res = '0'

                except Exception as e:
                    print("transErr : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
            returun_res = '0'
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
            returun_res = '0'
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
            returun_res = '0'
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            returun_res = '0'
        finally:
            pass
        return returun_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    12. 기기 주소 변경
    device_type, before_addr, after_addr 3개의 인자를 받아 장비의 주소를 변경한다.
    after_addr을 1씩 늘려가며 현재 설정되어 있는 가장 큰 주소값을 찾고,
    그 주소에 1을 더해 임시 저장 주소로 사용한다.
    임시 저장 주소가 변경하고자하는 주소와 같을 경우는 바로 변경 작업을 하고,
    다를 경우 아래와 같은 순서로 변경을 실시한다. 
    1. after -> temp
    2. before -> after
    3. temp -> before
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def change_device_addr(self, device_type, before_addr, after_addr):
        # 반환 값
        return_res = '1'

        # 데이터 수집 장치 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        temp = int(after_addr) - 1  # 반복문 진입을 위한 - 1 카운트

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            while True:
                temp = int(temp) + 1

                # 기기 주소 확인 프로토콜 생성
                trans = "GL020AD"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(temp).rjust(2, '0')
                trans += str(before_addr).rjust(2, '0')
                trans += '1'  # 시도횟수
                trans += self.get_checksum(trans)
                trans += "CH"
                trans = trans.encode("utf-8")

                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    res = res.decode("utf-8")  # 받은 값에 대한 디코드
                    res = res.replace(" ", "0")

                    # 무응답 일 경우
                    if res == "":
                        temp_addr = str(temp).rjust(2, '0')
                        break

                except Exception as e:
                    print("From change_device_addr for while loop except : ", e)
                    return_res = '0'

            if str(temp_addr) == str(after_addr):
                # 기기 주소 변경 프로토콜 생성
                trans = "GL020AD"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(before_addr).rjust(2, '0')
                trans += str(after_addr).rjust(2, '0')
                trans += '3'  # 시도횟수
                trans += self.get_checksum(trans)
                trans += "CH"
                trans = trans.encode("utf-8")
                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    res = res.decode("utf-8")  # 받은 값에 대한 디코드
                    res = res.replace(" ", "0")
                except Exception as e:
                    print("From change_device_addr for changer except : ", e)
                    return_res = '0'
                # 데이터베이스 변경
                change_addr_qry = "UPDATE gl_device_list SET `addr` = %s WHERE `type` = %s AND `addr` = %s"
                curs.execute(change_addr_qry, (after_addr, device_type, before_addr))
                conn.commit()
            else:
                # after -> temp
                # 기기 주소 변경 프로토콜 생성
                trans = "GL020AD"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(after_addr).rjust(2, '0')
                trans += str(temp_addr).rjust(2, '0')
                trans += '3'  # 시도횟수
                trans += self.get_checksum(trans)
                trans += "CH"
                trans = trans.encode("utf-8")
                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    res = res.decode("utf-8")  # 받은 값에 대한 디코드
                    res = res.replace(" ", "0")
                except Exception as e:
                    print("From change_device_addr for changer except : ", e)
                    return_res = '0'

                # 데이터베이스 변경
                change_addr_qry = "UPDATE gl_device_list SET `addr` = %s WHERE `type` = %s AND `addr` = %s"
                curs.execute(change_addr_qry, (temp_addr, device_type, after_addr))
                conn.commit()

                # before -> after
                # 기기 주소 변경 프로토콜 생성
                trans = "GL020AD"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(before_addr).rjust(2, '0')
                trans += str(after_addr).rjust(2, '0')
                trans += '3'  # 시도횟수
                trans += self.get_checksum(trans)
                trans += "CH"
                trans = trans.encode("utf-8")
                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    res = res.decode("utf-8")  # 받은 값에 대한 디코드
                    res = res.replace(" ", "0")
                except Exception as e:
                    print("From change_device_addr for changer except : ", e)
                    return_res = '0'

                # 데이터베이스 변경
                change_addr_qry = "UPDATE gl_device_list SET `addr` = %s WHERE `type` = %s AND `addr` = %s"
                curs.execute(change_addr_qry, (after_addr, device_type, before_addr))
                conn.commit()

                # temp -> before
                # 기기 주소 변경 프로토콜 생성
                trans = "GL020AD"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(temp_addr).rjust(2, '0')
                trans += str(before_addr).rjust(2, '0')
                trans += '3'  # 시도횟수
                trans += self.get_checksum(trans)
                trans += "CH"
                trans = trans.encode("utf-8")
                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    res = res.decode("utf-8")  # 받은 값에 대한 디코드
                    res = res.replace(" ", "0")
                except Exception as e:
                    print("From change_device_addr for changer except : ", e)
                    return_res = '0'

                # 데이터베이스 변경
                change_addr_qry = "UPDATE gl_device_list SET `addr` = %s WHERE `type` = %s AND `addr` = %s"
                curs.execute(change_addr_qry, (before_addr, device_type, temp_addr))
                conn.commit()

        except Exception as e:
            print("From change_device_addr for connect_rs except : ", e)
            return_res = '0'
        finally:
            pass

        return return_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    13. 누적금액 초기화
    포스에서 원활한 UI 제어를 위해 한번에 전체 장비를 초기화하지 않고
    포스로부터 디바이스 타입과 주소를 넘겨 받아 해당 장비의 누적금액을 초기화한 후
    '성공', '실패'를 리턴한다.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def reset_total_money(self, device_type, device_addr):
        res = "실패"  # 반환값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 485 장비
        if (device_type == str(gls_config.SELF) or device_type == str(gls_config.AIR)
                or device_type == str(gls_config.MATE) or device_type == str(gls_config.READER)
                or device_type == str(gls_config.CHARGER)):
            try:
                # RS-485 연결
                ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

                # 누적 금액 초기화 프로토콜 생성
                trans = "GL017IN"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(device_addr)
                trans += self.get_checksum(trans)  # checksum
                trans += "CH"
                trans = trans.encode("utf-8")
                # 누적 금액 초기화 명령 전송
                state = ser.readline(ser.write(bytes(trans)))

                if state:
                    res = "성공"

            except Exception as e:
                print("From reset_total_money for RS-485 except : ", e)
                res = "실패"
        # LAN 장비
        elif device_type == str(gls_config.TOUCH) or device_type == str(gls_config.KIOSK):
            try:
                with conn.cursor():
                    # device_no 추출
                    get_device_no_qry = "SELECT `no` FROM gl_device_list WHERE `type` = %s and `addr` = %s"
                    curs.execute(get_device_no_qry, (device_type, device_addr))
                    get_device_no_res = curs.fetchall()

                    for device in get_device_no_res:
                        reset_total_qry = "UPDATE gl_charger_total SET `charge` = '0', `cash` = '0', `bonus` = '0', " \
                                          "`card_amount` = '0', card_count = '0' WHERE `device_no` = %s"
                        curs.execute(reset_total_qry, device['no'])
                        conn.commit()
                        res = "성공"
            except Exception as e:
                print('From reset_total_money for charger except : ', e)
                res = "실패"
            finally:
                conn.close()
        pass
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    14. 세차장 ID 변경
    각 장비의 상점 ID를 변경한다.
    누적금액 초기화와 같은 이유로 한번에 전체 장비를 초기화하지 않고
    포스로부터 디바이스 타입과 주소를 넘겨 받아 해당 장비의 상점 ID를 변경한 후
    '성공', '실패'를 리턴한다.
    * 참고 : 본 함수는 포스 설정에서 이미 변경되어 있는 상점 ID를 장비에 입력하는 기능
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def update_shop_no(self, device_type, device_addr):
        res = "실패"  # 반환값

        # 데이터베이스 접속 설정
        conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                               charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
        curs = conn.cursor(pymysql.cursors.DictCursor)

        # 포스 설정에서 변경한 ID 값 추출
        get_shop_no_qry = "SELECT `no` FROM gl_shop_info"
        curs.execute(get_shop_no_qry)
        get_shop_no_res = curs.fetchall()

        for shop in get_shop_no_res:
            shop_no = str(shop['no']).rjust(4, '0')

        # RS-485 통신장비 세차장 ID 변경
        if (device_type == str(gls_config.SELF) or device_type == str(gls_config.AIR)
                or device_type == str(gls_config.MATE) or device_type == str(gls_config.READER)
                or device_type == str(gls_config.CHARGER) or device_type == str(gls_config.GARAGE)):
            try:
                # RS-485 연결
                ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

                # 세차장 ID 변경 프로토콜 생성
                trans = "GL021ID"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(device_type).rjust(2, '0')
                trans += str(device_addr)
                trans += shop_no
                trans += self.get_checksum(trans)  # checksum
                trans += "CH"
                trans = trans.encode("utf-8")
                # 세차장 ID 변경 명령 전송
                state = ser.readline(ser.write(bytes(trans)) + 100)

                if state:
                    res = "성공"

            except Exception as e:
                print("From update_shop_no for RS-485 except : ", e)
                res = "실패"
        # 터치 충전기 ID 변경
        elif device_type == str(gls_config.TOUCH):
            try:
                with conn.cursor():
                    # device_no 추출
                    get_device_no_qry = "SELECT `no`, `ip` FROM gl_device_list WHERE `type` = %s and `addr` = %s"
                    curs.execute(get_device_no_qry, (device_type, device_addr))
                    get_device_no_res = curs.fetchall()

                    for device in get_device_no_res:
                        # 데이터 수집 장치 업데이트
                        update_shop_no_qry = "UPDATE gl_charger_config SET `shop_no` = %s WHERE `device_no` = %s"
                        curs.execute(update_shop_no_qry, (shop_no, device['no']))
                        conn.commit()
                        # 터치 충전기 업데이트
                        pi_conn = pymysql.connect(host=device['ip'], user=gls_config.PI_MYSQL_USER, password=gls_config.PI_MYSQL_PWD,
                                                  charset=gls_config.MYSQL_SET, db=gls_config.PI_MYSQL_DB)
                        pi_curs = pi_conn.cursor(pymysql.cursors.DictCursor)
                        update_touch_shop_no_q = "UPDATE config SET `id` = %s"
                        pi_curs.execute(update_touch_shop_no_q, shop_no)
                        pi_conn.commit()
                        res = "성공"
            except Exception as e:
                print('From update_shop_no for charger except : ', e)
                res = "실패"
        # 키오스크 ID 변경
        elif device_type == str(gls_config.KIOSK):
            try:
                with conn.cursor():
                    # device_no 추출
                    get_device_no_qry = "SELECT `no` FROM gl_device_list WHERE `type` = %s and `addr` = %s"
                    curs.execute(get_device_no_qry, (device_type, device_addr))
                    get_device_no_res = curs.fetchall()

                    for device in get_device_no_res:
                        update_shop_no_qry = "UPDATE gl_charger_config SET `shop_no` = %s WHERE `device_no` = %s"
                        curs.execute(update_shop_no_qry, (shop_no, device['no']))
                        conn.commit()
                        res = "성공"
            except Exception as e:
                print('From update_shop_no for charger except : ', e)
                res = "실패"
        conn.close()
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    15. 체크섬
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_checksum(self, req):
        res = 0
        for i in req:
            temp = ord(i)
            res += temp
            # print(" temp :" + str(temp) + "     res : ", str(res))

        res = res % 100
        res = str(res).rjust(2, ' ')
        return res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    16. 스레드 감시
    메인 스레드를 종료시키는 기능을 사용 후 프로그램을 종료했을 때 다시 메인 스레드를
    실행시키지 않기 때문에 이를 감시하기 위해서 만듬.
    10분에 한번씩 작동하며, 10초이상 get_device_state가 실행중이지 않다고 판단되면
    메인 스레드를 호출함.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def thread_monitor(self):
        res = 0
        for i in range(1,13):
            print("loop : ", i)
            print("FLAG_MAIN", self.FLAG_MAIN)
            print("FLAG_STATE", self.FLAG_STATE)
            if self.FLAG_MAIN == 'cancel' and self.FLAG_STATE == 'stop':
                res += 1
        if res >= 10:
            self.main_thread(1)
            res = 0
        else:
            res = 0
        # self.state_monitor = threading.Timer(second, self.thread_monitor)
        # self.state_monitor.daemon = True
        # self.state_monitor.start()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    17. 게러지 설정 불러오기
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_garage_config(self):
        # 반환 값
        garage_config_list = []

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT * FROM gl_garage_config WHERE `device_addr` = %s ORDER BY `input_date` DESC " \
                               "LIMIT 1"

                    # 장비 주소 추출
                    curs.execute(query, gls_config.GARAGE)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        garage_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_garage_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)  # 회사 분류
                        trans += str(gls_config.GARAGE).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)  # 체크섬
                        trans += "CH"  # ETX + 개행문자
                        trans = trans.encode("utf-8")
                        print(trans)
                        try:
                            # 485 명령 전송
                            ser.write(bytes(trans))

                            line = []

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            # 체크섬 정보
                            res_len = len(res)
                            stx = res[0:2]
                            etx = res[95:97]
                            check_sum = str(self.get_checksum(orgin[:93])).replace(" ", "0")
                            res_check_sum = res[93:95]

                            if stx == 'GL' and etx == 'CH' and res_len == 97 and res_check_sum == check_sum:
                                print("get_garage_config : ", res)

                                # 응답 프르토콜 분할
                                # 디바이스 정보
                                garage_config['device_addr'] = res[9:11]  # 장비 주소
                                garage_config['state'] = '1'              # 통신 상태

                                # 금액 및 시간 설정
                                garage_config['btn1_init_money'] = int(res[11:15]) * 100  # 버튼1 동작 금액
                                garage_config['btn1_init_time'] = res[15:20]              # 버튼1 동작 시간
                                garage_config['btn2_init_money'] = int(res[20:24]) * 100  # 버튼2 동작 금액
                                garage_config['btn2_init_time'] = res[24:29]              # 버튼2 동작 시간
                                garage_config['con_money'] = int(res[29:33]) * 100        # 연속 동작 금액
                                garage_config['con_time'] = res[33:38]                    # 연속 동작 시간

                                # 동작 설정
                                garage_config['self_time'] = res[38:43]      # 고압 1회 사용 시간
                                garage_config['self_count'] = res[43:46]     # 고압 한 사이클 사용 횟수
                                garage_config['foam_time'] = res[46:51]      # 스노우폼 1회 사용 시간
                                garage_config['foam_count'] = res[51:54]     # 스노우폼 한 사이클 사용 횟수
                                garage_config['under_time'] = res[54:59]     # 하부 1회 사용 시간
                                garage_config['under_count'] = res[59:62]    # 하부 한 사이클 사용 횟수
                                garage_config['coating_time'] = res[62:67]   # 발수 1회 사용 시간
                                garage_config['coating_count'] = res[67:70]  # 발수 한 사이클 사용 횟수
                                garage_config['air_time'] = res[70:75]       # 진공 1회 사용 시간
                                garage_config['air_count'] = res[75:78]      # 진공 한 사이클 사용 횟수
                                garage_config['airgun_time'] = res[78:83]    # 에어 1회 사용 시간
                                garage_config['airgun_count'] = res[83:86]   # 에어 한 사이클 사용 횟수

                                # 기타 설정
                                garage_config['cycle_money'] = int(res[86:90]) * 100   # 한 사이클 사용 금액
                                garage_config['coating_type'] = res[90]     # 코팅 사용 타입 선택
                                garage_config['buzzer_time'] = res[91:93]   # 부져 동작 시간

                                # 예비
                                garage_config['btn3_init_money'] = '1'
                                garage_config['btn3_init_time'] = '1'
                                garage_config['pause_time'] = '1'
                                garage_config['pause_count'] = '1'

                            else:
                                garage_config['device_addr'] = str(row['addr'])  # 장비 주소
                                garage_config['state'] = '0'  # 통신 상태
                        # except Exception as e:
                        #     print("From get_garage_config except : ", e)
                        finally:
                            pass

                        # 반환할 리스트에 저장
                        garage_config_list.append(garage_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, row['addr'])
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            db_garage_config['device_addr'] = db_row['device_addr']
                            db_garage_config['btn1_init_money'] = int(db_row['btn1_init_money']) * 100
                            db_garage_config['btn1_init_time'] = db_row['btn1_init_time']
                            db_garage_config['btn2_init_money'] = int(db_row['btn2_init_money']) * 100
                            db_garage_config['btn2_init_time'] = db_row['btn2_init_time']
                            db_garage_config['con_money'] = int(db_row['con_money']) * 100
                            db_garage_config['con_time'] = db_row['con_time']

                            # 사용 설정
                            db_garage_config['self_time'] = db_row['self_time']
                            db_garage_config['self_count'] = db_row['self_count']
                            db_garage_config['foam_time'] = db_row['foam_time']
                            db_garage_config['foam_count'] = db_row['foam_count']
                            db_garage_config['under_time'] = db_row['under_time']
                            db_garage_config['under_count'] = db_row['under_count']
                            db_garage_config['coating_time'] = db_row['coating_time']
                            db_garage_config['coating_count'] = db_row['coating_count']
                            db_garage_config['air_time'] = db_row['air_time']
                            db_garage_config['air_count'] = db_row['air_count']
                            db_garage_config['airgun_time'] = db_row['airgun_time']
                            db_garage_config['airgun_count'] = db_row['airgun_count']

                            # 기타 설정
                            db_garage_config['cycle_money'] = db_row['cycle_money']
                            db_garage_config['coating_type'] = db_row['coating_type']
                            db_garage_config['buzzer_time'] = db_row['buzzer_time']

                            if garage_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                diff = '0'  # 설정 이상 비교 플래그
                                diff_set = OrderedDict()  # 설정 이상 정보 저장 딕셔너리
                                # 기본 설정
                                if db_garage_config['device_addr'] != garage_config['device_addr']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_addr'] = db_garage_config['device_addr']
                                    diff_set['garage_addr'] = garage_config['device_addr']

                                if db_garage_config['btn1_init_money'] != garage_config['btn1_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_btn1_init_money'] = db_garage_config['btn1_init_money']
                                    diff_set['garage_btn1_init_money'] = garage_config['btn1_init_money']

                                if db_garage_config['btn1_init_time'] != garage_config['btn1_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_btn1_init_time'] = db_garage_config['btn1_init_time']
                                    diff_set['garage_btn1_init_time'] = garage_config['btn1_init_time']

                                if db_garage_config['btn2_init_money'] != garage_config['btn2_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_btn2_init_money'] = db_garage_config['btn2_init_money']
                                    diff_set['garage_btn2_init_money'] = garage_config['btn2_init_money']

                                if db_garage_config['btn2_init_time'] != garage_config['btn2_init_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_btn2_init_time'] = db_garage_config['btn2_init_time']
                                    diff_set['garage_btn2_init_time'] = garage_config['btn2_init_time']

                                if db_garage_config['con_money'] != garage_config['con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_con_money'] = db_garage_config['con_money']
                                    diff_set['garage_con_money'] = garage_config['con_money']

                                if db_garage_config['con_time'] != garage_config['con_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_con_time'] = db_garage_config['con_time']
                                    diff_set['garage_con_time'] = garage_config['con_time']

                                if db_garage_config['self_time'] != garage_config['self_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_time'] = db_garage_config['self_time']
                                    diff_set['garage_self_time'] = garage_config['self_time']

                                if db_garage_config['self_count'] != garage_config['self_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_self_count'] = db_garage_config['self_count']
                                    diff_set['garage_self_count'] = garage_config['self_count']

                                if db_garage_config['foam_time'] != garage_config['foam_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_time'] = db_garage_config['foam_time']
                                    diff_set['garage_foam_time'] = garage_config['foam_time']

                                if db_garage_config['foam_count'] != garage_config['foam_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_foam_count'] = db_garage_config['foam_count']
                                    diff_set['garage_foam_count'] = garage_config['foam_count']

                                if db_garage_config['under_time'] != garage_config['under_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_time'] = db_garage_config['under_time']
                                    diff_set['garage_under_time'] = garage_config['under_time']

                                if db_garage_config['under_count'] != garage_config['under_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_under_count'] = db_garage_config['under_count']
                                    diff_set['garage_under_count'] = garage_config['under_count']

                                if db_garage_config['coating_time'] != garage_config['coating_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_time'] = db_garage_config['coating_time']
                                    diff_set['garage_coating_time'] = garage_config['coating_time']

                                if db_garage_config['coating_count'] != garage_config['coating_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_count'] = db_garage_config['coating_count']
                                    diff_set['garage_coating_count'] = garage_config['coating_count']

                                if db_garage_config['air_time'] != garage_config['air_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_time'] = db_garage_config['air_time']
                                    diff_set['garage_air_time'] = garage_config['air_time']

                                if db_garage_config['air_count'] != garage_config['air_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_air_count'] = db_garage_config['air_count']
                                    diff_set['garage_air_count'] = garage_config['air_count']

                                if db_garage_config['airgun_time'] != garage_config['airgun_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_airgun_time'] = db_garage_config['airgun_time']
                                    diff_set['garage_airgun_time'] = garage_config['airgun_time']

                                if db_garage_config['airgun_count'] != garage_config['airgun_count']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_airgun_count'] = db_garage_config['airgun_count']
                                    diff_set['garage_airgun_count'] = garage_config['airgun_count']

                                # 기타 설정
                                if db_garage_config['buzzer_time'] != garage_config['buzzer_time']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_buzzer_time'] = db_garage_config['buzzer_time']
                                    diff_set['garage_buzzer_time'] = garage_config['buzzer_time']

                                if db_garage_config['coating_type'] != garage_config['coating_type']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_coating_type'] = db_garage_config['coating_type']
                                    diff_set['garage_coating_type'] = garage_config['coating_type']

                                if db_garage_config['cycle_money'] != garage_config['cycle_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_cycle_money'] = db_garage_config['cycle_money']
                                    diff_set['garage_cycle_money'] = garage_config['cycle_money']

                                # 장비 설정값이 데이터베이스와 다를 때
                                if diff == '1':
                                    insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    new_garage_config_qry = "INSERT INTO gl_garage_config(`device_addr`, " \
                                                          "`btn1_init_money`, `btn1_init_time`, `btn2_init_money`, " \
                                                          "`btn2_init_time`, " \
                                                          "`con_money`, `con_time`, `self_time`, `self_count`, " \
                                                          "`foam_time`, `foam_count`, `under_time`, `under_count`, " \
                                                          "`coating_time`, `coating_count`, `air_time`, `air_count`, " \
                                                          "`airgun_time`, `airgun_count`, `buzzer_time`, " \
                                                          "`coating_type`, `cycle_money`, `input_date`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                                          "%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    curs.execute(new_garage_config_qry, (garage_config['device_addr'],
                                                                         str(garage_config['btn1_init_money'] // 100).rjust(3, '0'),
                                                                         garage_config['btn1_init_time'],
                                                                         str(garage_config['btn2_init_money'] // 100).rjust(3, '0'),
                                                                         garage_config['btn2_init_time'],
                                                                         str(garage_config['con_money'] // 100).rjust(3, '0'),
                                                                         garage_config['con_time'],
                                                                         garage_config['self_time'], garage_config['self_count'],
                                                                         garage_config['foam_time'], garage_config['foam_count'],
                                                                         garage_config['under_time'], garage_config['under_count'],
                                                                         garage_config['coating_time'], garage_config['coating_count'],
                                                                         garage_config['air_time'], garage_config['air_count'],
                                                                         garage_config['airgun_time'], garage_config['airgun_count'],
                                                                         garage_config['buzzer_time'], garage_config['coating_type'],
                                                                         garage_config['cycle_money'], insert_input_date))
                                    conn.commit()
            finally:
                conn.close()
        # except UnboundLocalError as ex:
        #     print('엑세스 거부', ex)
        # except FileNotFoundError as ex:
        #     print('지정된 포트를 찾을 수 없습니다.', ex)
        # except UnicodeDecodeError as ex1:
        #     print('디코딩 오류', ex1)
        # except Exception as ex1:
        #     print('오류를 알 수 없습니다.', ex1)
        finally:
            pass
        return {'result': garage_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    18. 게러지 설정
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_garage_config(self, args):
        returun_res = '1'
        print(args)

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')                      # 장비 번호
        btn1_init_money = str(int(args['btn1_init_money']) // 100).rjust(4, '0')  # 버튼1 동작 금액
        btn1_init_time = str(args['btn1_init_time']).rjust(5, '0')                # 버튼1 동작 시간
        btn2_init_money = str(int(args['btn2_init_money']) // 100).rjust(4, '0')  # 버튼2 동작 금액
        btn2_init_time = str(args['btn2_init_time']).rjust(5, '0')                # 버튼2 동작 시간
        con_money = str(int(args['con_money']) // 100).rjust(4, '0')              # 연속 동작 금액
        con_time = str(args['con_time']).rjust(5, '0')                            # 연속 동작 시간
        self_time = str(args['self_time']).rjust(5, '0')
        self_count = str(args['self_count']).rjust(3, '0')
        foam_time = str(args['foam_time']).rjust(5, '0')
        foam_count = str(args['foam_count']).rjust(3, '0')
        under_time = str(args['under_time']).rjust(5, '0')
        under_count = str(args['under_count']).rjust(3, '0')
        coating_time = str(args['coating_time']).rjust(5, '0')
        coating_count = str(args['coating_count']).rjust(3, '0')
        air_time = str(args['air_time']).rjust(5, '0')
        air_count = str(args['air_count']).rjust(3, '0')
        airgun_time = str(args['airgun_time']).rjust(5, '0')
        airgun_count = str(args['airgun_count']).rjust(3, '0')
        buzzer_time = str(args['buzzer_time']).rjust(2, '0')  # 부저 동작 시간
        coating_type = str(args['coating_type']) # 일시 정지 시간
        cycle_money = str(int(args['cycle_money']) // 100).rjust(4, '0')  # 일시 정지 횟수

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                # 입력 날짜 생성
                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # DB 저장
                new_garage_config_qry = "INSERT INTO gl_garage_config(`device_addr`, " \
                                        "`btn1_init_money`, `btn1_init_time`, `btn2_init_money`, " \
                                        "`btn2_init_time`, " \
                                        "`con_money`, `con_time`, `self_time`, `self_count`, " \
                                        "`foam_time`, `foam_count`, `under_time`, `under_count`, " \
                                        "`coating_time`, `coating_count`, `air_time`, `air_count`, " \
                                        "`airgun_time`, `airgun_count`, `buzzer_time`, " \
                                        "`cycle_money`, `coating_type`, `input_date`) " \
                                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                        "%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                curs.execute(new_garage_config_qry, (device_addr,
                                                     btn1_init_money, btn1_init_time, btn2_init_money, btn2_init_time,
                                                     con_money, con_time,
                                                     self_time, self_count, foam_time, foam_count, under_time, under_count,
                                                     coating_time, coating_count, air_time, air_count, airgun_time, airgun_count,
                                                     buzzer_time, cycle_money, coating_type, insert_input_date))
                conn.commit()

                # 485 장비 저장
                trans = "GL099GS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.GARAGE).rjust(2, "0")
                trans += device_addr
                trans += btn1_init_money
                trans += btn1_init_time
                trans += btn2_init_money
                trans += btn2_init_time
                trans += con_money
                trans += con_time
                trans += self_time
                trans += self_count
                trans += foam_time
                trans += foam_count
                trans += under_time
                trans += under_count
                trans += coating_time
                trans += coating_count
                trans += air_time
                trans += air_count
                trans += airgun_time
                trans += airgun_count
                trans += cycle_money
                trans += coating_type
                trans += buzzer_time
                trans += self.get_checksum(trans)
                trans += "CH\r\n"  # ETX + 개행문자
                trans = trans.encode("utf-8")
                print("trans : ", trans)

                try:
                    res = ser.readline(ser.write(bytes(trans)) + 120)
                    print("res : ", res)

                except Exception as e:
                    print("From set_garage_config : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
            returun_res = '0'
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
            returun_res = '0'
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
            returun_res = '0'
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            returun_res = '0'
        finally:
            pass
        return returun_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    19. 장비 설정 복사
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # noinspection PyMethodMayBeStatic
    def copy_device_config(self, type, copy, target):

        print(type)
        print(copy)
        print(target)



        try:
            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                # 입력 날짜 생성
                # insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # self
                if str(type) == str(gls_config.SELF):
                    get_self = "SELECT * FROM gl_self_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                    curs.execute(get_self, copy)
                    res_self_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_self_config:
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
                        if row['use_type']:
                            config['use_type'] = row['use_type']
                        if row['speedier_enable']:
                            config['speedier_enable'] = row['speedier_enable']
                        if row['set_coating_output']:
                            config['set_coating_output'] = row['set_coating_output']
                        if row['wipping_enable']:
                            config['wipping_enable'] = row['wipping_enable']
                        if row['wipping_temperature']:
                            config['wipping_temperature'] = row['wipping_temperature']

                    get_res = self.set_self_config(config)
                # air
                if str(type) == str(gls_config.AIR):
                    get_air = "SELECT * FROM gl_air_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                    curs.execute(get_air, copy)
                    res_air_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_air_config:
                        if row['air_init_money']:
                            config['air_init_money'] = int(row['air_init_money']) * 100
                        if row['air_init_time']:
                            config['air_init_time'] = row['air_init_time']
                        if row['air_con_money']:
                            config['air_con_money'] = int(row['air_con_money']) * 100
                        if row['air_con_time']:
                            config['air_con_time'] = row['air_con_time']
                        if row['air_cycle_money']:
                            config['cycle_money'] = int(row['air_cycle_money']) * 100
                        if row['air_buzzer_time']:
                            config['buzzer_time'] = row['air_buzzer_time']
                        if row['air_con_enable']:
                            config['air_con_enable'] = row['air_con_enable']
                        if row['air_pay_free']:
                            config['pay_free'] = row['air_pay_free']
                        if row['air_key_enable']:
                            config['key_enable'] = row['air_key_enable']

                    get_res = self.set_air_config(config)
                # mate
                if str(type) == str(gls_config.MATE):
                    get_mate = "SELECT * FROM gl_mate_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                    curs.execute(get_mate, copy)
                    res_mate_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_mate_config:
                        if row['mate_init_money']:
                            config['mate_init_money'] = int(row['mate_init_money']) * 100
                        if row['mate_init_time']:
                            config['mate_init_time'] = row['mate_init_time']
                        if row['mate_con_money']:
                            config['mate_con_money'] = int(row['mate_con_money']) * 100
                        if row['mate_con_time']:
                            config['mate_con_time'] = row['mate_con_time']
                        if row['mate_cycle_money']:
                            config['cycle_money'] = int(row['mate_cycle_money']) * 100
                        if row['mate_buzzer_time']:
                            config['buzzer_time'] = row['mate_buzzer_time']
                        if row['mate_con_enable']:
                            config['mate_con_enable'] = row['mate_con_enable']
                        if row['mate_pay_free']:
                            config['pay_free'] = row['mate_pay_free']
                        if row['mate_key_enable']:
                            config['key_enable'] = row['mate_key_enable']
                        if row['mate_relay_delay']:
                            config['relay_delay'] = row['mate_relay_delay']

                    get_res = self.set_mate_config(config)
                # charger
                if str(type) == str(gls_config.CHARGER):
                    get_charger = "SELECT * FROM gl_charger_config AS charger " \
                                  "INNER JOIN gl_device_list AS list ON charger.device_no = list.`no` " \
                                  "INNER JOIN gl_charger_bonus AS bonus ON charger.default_bonus_no = bonus.`no` " \
                                  "WHERE list.addr = %s AND list.type = %s ORDER BY 	charger.input_date DESC LIMIT 1"
                    curs.execute(get_charger, (copy, gls_config.CHARGER))
                    res_charger_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_charger_config:
                        if row['card_price']:
                            config['card_price'] = row['card_price'] * 100
                        if row['card_min_price']:
                            config['card_min_price'] = row['card_min_price'] * 100
                        if row['auto_charge_enable']:
                            config['auto_charge_enable'] = row['auto_charge_enable']
                        if row['auto_charge_price']:
                            config['auto_charge_price'] = row['auto_charge_price'] * 100
                        if row['bonus1']:
                            config['bonus1'] = row['bonus1'] * 100
                        if row['bonus2']:
                            config['bonus2'] = row['bonus2'] * 100
                        if row['bonus3']:
                            config['bonus3'] = row['bonus3'] * 100
                        if row['bonus4']:
                            config['bonus4'] = row['bonus4'] * 100
                        if row['bonus5']:
                            config['bonus5'] = row['bonus5'] * 100
                        if row['bonus6']:
                            config['bonus6'] = row['bonus6'] * 100
                        if row['bonus7']:
                            config['bonus7'] = row['bonus7'] * 100
                        if row['bonus8']:
                            config['bonus8'] = row['bonus8'] * 100
                        if row['bonus9']:
                            config['bonus9'] = row['bonus9'] * 100
                        if row['bonus10']:
                            config['bonus10'] = row['bonus10'] * 100

                    get_res = self.set_charger_config(config)
                # touch
                if str(type) == str(gls_config.TOUCH):
                    tch = touch_charger.TouchCharger()
                    get_touch = "SELECT * FROM gl_charger_config AS charger " \
                                "INNER JOIN gl_device_list AS list ON charger.`device_no` = list.`no` " \
                                "INNER JOIN gl_charger_bonus AS bonus ON charger.`default_bonus_no` = bonus.`no` " \
                                "INNER JOIN gl_shop_info AS info ON charger.`shop_no` = info.`no`" \
                                "WHERE list.addr = %s AND list.type = %s ORDER BY 	charger.input_date DESC LIMIT 1"
                    curs.execute(get_touch, (copy, gls_config.TOUCH))
                    res_touch_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_touch_config:
                        if row['card_price']:
                            config['card_price'] = row['card_price'] * 100
                        if row['card_min_price']:
                            config['card_min_price'] = row['card_min_price'] * 100
                        if row['auto_charge_enable']:
                            config['auto_charge_enable'] = row['auto_charge_enable']
                        if row['auto_charge_price']:
                            config['auto_charge_price'] = row['auto_charge_price'] * 100
                        if row['bonus1']:
                            config['bonus1'] = row['bonus1'] * 100
                        if row['bonus2']:
                            config['bonus2'] = row['bonus2'] * 100
                        if row['bonus3']:
                            config['bonus3'] = row['bonus3'] * 100
                        if row['bonus4']:
                            config['bonus4'] = row['bonus4'] * 100
                        if row['bonus5']:
                            config['bonus5'] = row['bonus5'] * 100
                        if row['bonus6']:
                            config['bonus6'] = row['bonus6'] * 100
                        if row['bonus7']:
                            config['bonus7'] = row['bonus7'] * 100
                        if row['bonus8']:
                            config['bonus8'] = row['bonus8'] * 100
                        if row['bonus9']:
                            config['bonus9'] = row['bonus9'] * 100
                        if row['bonus10']:
                            config['bonus10'] = row['bonus10'] * 100
                        if row['rf_reader_type']:
                            config['rf_reader_type'] = row['rf_reader_type']
                        if row['shop_no']:
                            config['shop_no'] = row['shop_no']
                        if row['name']:
                            config['name'] = row['name']
                        if row['shop_pw']:
                            config['shop_pw'] = row['shop_pw']

                    get_res = tch.set_touch_config(config)
                # kiosk
                if str(type) == str(gls_config.KIOSK):
                    ps = pos.Pos()
                    get_kiosk = "SELECT * FROM gl_charger_config AS charger " \
                                "INNER JOIN gl_device_list AS list ON charger.`device_no` = list.`no` " \
                                "INNER JOIN gl_charger_bonus AS bonus ON charger.`default_bonus_no` = bonus.`no` " \
                                "INNER JOIN gl_shop_info AS info ON charger.`shop_no` = info.`no`" \
                                "WHERE list.addr = %s AND list.type = %s ORDER BY 	charger.input_date DESC LIMIT 1"
                    curs.execute(get_kiosk, (copy, gls_config.KIOSK))
                    res_kiosk_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_kiosk_config:
                        if row['card_price']:
                            config['card_price'] = row['card_price'] * 100
                        if row['card_min_price']:
                            config['card_min_price'] = row['card_min_price'] * 100
                        if row['auto_charge_enable']:
                            config['auto_charge_enable'] = row['auto_charge_enable']
                        if row['auto_charge_price']:
                            config['auto_charge_price'] = row['auto_charge_price'] * 100
                        if row['bonus1']:
                            config['bonus1'] = row['bonus1'] * 100
                        if row['bonus2']:
                            config['bonus2'] = row['bonus2'] * 100
                        if row['bonus3']:
                            config['bonus3'] = row['bonus3'] * 100
                        if row['bonus4']:
                            config['bonus4'] = row['bonus4'] * 100
                        if row['bonus5']:
                            config['bonus5'] = row['bonus5'] * 100
                        if row['bonus6']:
                            config['bonus6'] = row['bonus6'] * 100
                        if row['bonus7']:
                            config['bonus7'] = row['bonus7'] * 100
                        if row['bonus8']:
                            config['bonus8'] = row['bonus8'] * 100
                        if row['bonus9']:
                            config['bonus9'] = row['bonus9'] * 100
                        if row['bonus10']:
                            config['bonus10'] = row['bonus10'] * 100
                        if row['rf_reader_type']:
                            config['rf_reader_type'] = row['rf_reader_type']
                        if row['shop_no']:
                            config['shop_no'] = row['shop_no']
                        if row['name']:
                            config['name'] = row['name']
                        if row['shop_pw']:
                            config['shop_pw'] = row['shop_pw']
                        if row['exhaust_charge_enable']:
                            config['exhaust_charge_enable'] = row['exhaust_charge_enable']

                    get_res = ps.set_kiosk_config(config)
                # garage
                if str(type) == str(gls_config.GARAGE):
                    get_garage = "SELECT * FROM gl_garage_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                    curs.execute(get_garage, copy)
                    res_garage_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_garage_config:
                        if row['btn1_init_money']:
                            config['btn1_init_money'] = int(row['btn1_init_money']) * 100
                        if row['btn1_init_time']:
                            config['btn1_init_time'] = row['btn1_init_time']
                        if row['btn2_init_money']:
                            config['btn2_init_money'] = int(row['btn2_init_money']) * 100
                        if row['btn2_init_time']:
                            config['btn2_init_time'] = row['btn2_init_time']
                        if row['btn3_init_money']:
                            config['btn3_init_money'] = int(row['btn3_init_money']) * 100
                        if row['btn3_init_time']:
                            config['btn3_init_time'] = row['btn3_init_time']
                        if row['con_money']:
                            config['con_money'] = int(row['con_money']) * 100
                        if row['con_time']:
                            config['con_time'] = row['con_time']
                        if row['self_time']:
                            config['self_time'] = row['self_time']
                        if row['self_count']:
                            config['self_count'] = row['self_count']
                        if row['foam_time']:
                            config['foam_time'] = row['foam_time']
                        if row['foam_count']:
                            config['foam_count'] = row['foam_count']
                        if row['under_time']:
                            config['under_time'] = row['under_time']
                        if row['under_count']:
                            config['under_count'] = row['under_count']
                        if row['coating_time']:
                            config['coating_time'] = row['coating_time']
                        if row['coating_count']:
                            config['coating_count'] = row['coating_count']
                        if row['air_time']:
                            config['air_time'] = row['air_time']
                        if row['air_count']:
                            config['air_count'] = row['air_count']
                        if row['airgun_time']:
                            config['airgun_time'] = row['airgun_time']
                        if row['airgun_count']:
                            config['airgun_count'] = row['airgun_count']
                        if row['buzzer_time']:
                            config['buzzer_time'] = row['buzzer_time']
                        if row['cycle_money']:
                            config['cycle_money'] = row['cycle_money']
                        if row['coating_type']:
                            config['coating_type'] = row['coating_type']
                        if row['pause_time']:
                            config['pause_time'] = row['pause_time']
                        if row['pause_count']:
                            config['pause_count'] = row['pause_count']

                    get_res = self.set_garage_config(config)
                # reader
                if str(type) == str(gls_config.READER):
                    get_reader = "SELECT * FROM gl_reader_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
                    curs.execute(get_reader, copy)
                    res_reader_config = curs.fetchall()

                    config = OrderedDict()
                    config['device_addr'] = target

                    for row in res_reader_config:
                        if row['reader_init_money']:
                            config['reader_init_money'] = int(row['reader_init_money']) * 100
                        if row['reader_con_money']:
                            config['reader_con_money'] = int(row['reader_con_money']) * 100
                        if row['reader_cycle_money']:
                            config['reader_cycle_money'] = int(row['reader_cycle_money']) * 100
                        if row['reader_con_enable']:
                            config['reader_con_enable'] = row['reader_con_enable']
                        if row['reader_init_pulse']:
                            config['reader_init_pulse'] = row['reader_init_pulse']
                        if row['reader_con_pulse']:
                            config['reader_con_pulse'] = row['reader_con_pulse']
                        if row['reader_pulse_duty']:
                            config['reader_pulse_duty'] = row['reader_pulse_duty']

                    get_res = self.set_reader_config(config)
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            get_res = '0'
        finally:
            conn.close()
        return get_res

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    20. 리더기 설정 불러오기
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def get_reader_config(self):
        # 반환 값
        reader_config_list = []
        time.sleep(1)

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=0.1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            try:
                with conn.cursor():
                    # 장비 주소 추출 쿼리
                    query = "SELECT `addr` FROM gl_device_list WHERE `type` = %s"
                    # 장비 설정 추출 쿼리
                    db_query = "SELECT * FROM gl_reader_config WHERE `device_addr` = %s ORDER BY `input_date` DESC " \
                               "LIMIT 1"

                    # 장비 주소 추출
                    curs.execute(query, gls_config.READER)
                    addr_res = curs.fetchall()

                    # 각 주소별 PCB로부터 설정 값 불러오기
                    for row in addr_res:
                        # PCB 설정 저장 딕셔너리
                        reader_config = OrderedDict()
                        # DB 설정 저장 딕셔너리
                        db_reader_config = OrderedDict()
                        trans = "GL017CL"
                        trans += str(gls_config.MANAGER_CODE)
                        trans += str(gls_config.reader).rjust(2, '0')
                        trans += row['addr']
                        trans += self.get_checksum(trans)
                        trans += "CH"
                        trans = trans.encode("utf-8")
                        try:
                            ser.write(bytes(trans))

                            line = []

                            while 1:
                                temp = ser.read()
                                if temp:
                                    line.append(temp.decode('utf-8'))
                                else:
                                    orgin = ''.join(line)
                                    res = orgin.replace(" ", "0")
                                    break

                            # 체크섬 정보
                            res_len = len(res)
                            stx = res[0:2]
                            etx = res[31:33]
                            res_check_sum = res[29:31]
                            check_sum = str(self.get_checksum(orgin[:29])).replace(" ", "0")

                            if stx == 'GL' and etx == 'CH' and res_len == 33 and res_check_sum == check_sum:
                                print("get_reader_config : ", res)

                                # 응답 프르토콜 분할
                                # 디바이스 정보
                                reader_config['device_addr'] = res[9:11]  # 장비 주소
                                reader_config['state'] = '1'  # 통신 상태

                                # 설정 값
                                reader_config['reader_init_money'] = int(res[11:14]) * 100  # 초기 동작 금액
                                reader_config['reader_con_money'] = int(res[14:17]) * 100  # 연속 동작 금액
                                reader_config['reader_cycle_money'] = int(res[17:20]) * 100  # 한 사이클 이용 금액
                                reader_config['reader_con_enable'] = int(res[20])  # 연속 차감 유무
                                reader_config['reader_init_pulse'] = int(res[21:23])  # 초기 출력 펄스
                                reader_config['reader_con_pulse'] = int(res[23:25])  # 연속 출력 펄스
                                reader_config['reader_pulse_duty'] = int(res[25:29])  # 펄스 듀티

                                # CheckSum
                                reader_config['check_sum'] = res[35:37]
                            else:
                                reader_config['device_addr'] = str(row['addr'])  # 장비 주소
                                reader_config['state'] = '0'  # 통신 상태
                        except Exception as e:
                            print("From get_air_config except : ", e)

                        # 반환할 리스트에 저장
                        reader_config_list.append(reader_config)

                        # DB 에서 주소별 설정값 불러오기
                        curs.execute(db_query, row['addr'])
                        db_config = curs.fetchall()
                        for db_row in db_config:
                            # 기본 설정
                            db_reader_config['device_addr'] = db_row['device_addr']

                            # 설정 값
                            db_reader_config['reader_init_money'] = int(db_row['reader_init_money']) * 100
                            db_reader_config['reader_con_money'] = int(db_row['reader_con_money']) * 100
                            db_reader_config['reader_cycle_money'] = int(db_row['reader_cycle_money']) * 100
                            db_reader_config['reader_con_enable'] = db_row['reader_con_enable']
                            db_reader_config['reader_init_pulse'] = db_row['reader_init_pulse']
                            db_reader_config['reader_con_pulse'] = db_row['reader_con_pulse']
                            db_reader_config['reader_pulse_duty'] = db_row['reader_pulse_duty']

                            if reader_config['state'] != '0':
                                # DB - PCB 설정값 비교
                                diff = '0'  # 설정 이상 비교 플래그
                                diff_set = OrderedDict()  # 설정 이상 정보 저장 딕셔너리
                                # 설정 값
                                if db_reader_config['device_addr'] != reader_config['device_addr']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_addr'] = db_reader_config['device_addr']
                                    diff_set['reader_addr'] = reader_config['device_addr']

                                if db_reader_config['reader_init_money'] != reader_config['reader_init_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_init_money'] = db_reader_config['reader_init_money']
                                    diff_set['reader_init_money'] = reader_config['reader_init_money']

                                if db_reader_config['reader_con_money'] != reader_config['reader_con_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_con_money'] = db_reader_config['reader_con_money']
                                    diff_set['reader_con_money'] = reader_config['reader_con_money']

                                if db_reader_config['reader_cycle_money'] != reader_config['reader_cycle_money']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_cycle_money'] = db_reader_config['reader_cycle_money']
                                    diff_set['reader_cycle_money'] = reader_config['reader_cycle_money']

                                if db_reader_config['reader_con_enable'] != reader_config['reader_con_enable']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_con_enable'] = db_reader_config['reader_con_enable']
                                    diff_set['reader_con_enable'] = reader_config['reader_con_enable']

                                if db_reader_config['reader_init_pulse'] != reader_config['reader_init_pulse']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_init_pulse'] = db_reader_config['reader_init_pulse']
                                    diff_set['reader_init_pulse'] = reader_config['reader_init_pulse']

                                if db_reader_config['reader_con_pulse'] != reader_config['reader_con_pulse']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_con_pulse'] = db_reader_config['reader_con_pulse']
                                    diff_set['reader_con_pulse'] = reader_config['reader_con_pulse']
                                if db_reader_config['reader_pulse_duty'] != reader_config['reader_pulse_duty']:
                                    diff = '1'
                                    diff_set['state'] = '2'
                                    diff_set['device_addr'] = row['addr']
                                    diff_set['db_reader_pulse_duty'] = db_reader_config['reader_pulse_duty']
                                    diff_set['reader_pulse_duty'] = reader_config['reader_pulse_duty']

                                if diff == '1':
                                    insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                    new_reader_config_qry = "INSERT INTO gl_reader_config(`device_addr`, `reader_init_money`, `reader_con_money`, " \
                                                            "`reader_cycle_money`, `reader_init_pulse`, `reader_con_pulse`, `reader_pulse_duty`, `input_date`) " \
                                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    curs.execute(new_reader_config_qry, (reader_config['device_addr'],
                                                                       str(reader_config['reader_init_money'] // 100).rjust(3, '0'),
                                                                       str(reader_config['reader_con_money'] // 100).rjust(3, '0'),
                                                                       str(reader_config['cycle_money'] // 100).rjust(3, '0'),
                                                                       reader_config['reader_con_enable'],
                                                                       reader_config['reader_init_pulse'],
                                                                       reader_config['reader_con_pulse'],
                                                                       reader_config['reader_pulse_duty'],
                                                                       insert_input_date))
                                    conn.commit()
            finally:
                conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
        finally:
            pass
        return {'result': reader_config_list}

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    20. 리더기 설정 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # noinspection PyMethodMayBeStatic
    def set_reader_config(self, args):
        # 반환 값
        returun_res = '1'
        time.sleep(1)

        print(args)

        # args 파싱
        device_addr = str(args['device_addr']).rjust(2, '0')  # 장비 주소
        reader_init_money = str(int(args['reader_init_money']) // 100).rjust(3, '0')  # 매트 초기 동작 금액
        reader_con_money = str(int(args['reader_con_money']) // 100).rjust(3, '0')  # 매트 연속 동작 금액
        reader_cycle_money = str(int(args['reader_cycle_money']) // 100).rjust(3, '0')  # 한 사이클 이용 금액
        reader_con_enable = args['reader_con_enable']  # 매트 연속 동장 유무
        reader_init_pulse = str(args['reader_init_pulse']).rjust(2, '0')  # 초기 출력 펄스
        reader_con_pulse = str(args['reader_con_pulse']).rjust(2, '0')  # 연속 출력 펄스
        reader_pulse_duty = str(args['reader_pulse_duty']).rjust(4, '0')  # 펄스 듀티

        try:
            # 485 연결
            ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

            # 데이터 수집 장치 접속 설정
            conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                                   charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
            curs = conn.cursor(pymysql.cursors.DictCursor)

            with conn.cursor():

                # 입력 날짜 생성
                insert_input_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

                # DB 저장
                insert_reader_config_q = "INSERT INTO gl_reader_config(`device_addr`, `reader_init_money`, " \
                                       "`reader_con_money`,`reader_cycle_money`, " \
                                       "`reader_con_enable`, `reader_init_pulse`, `reader_con_pulse`, " \
                                       "`reader_pulse_duty`, `input_date`) " \
                                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                curs.execute(insert_reader_config_q, (device_addr, reader_init_money, reader_con_money,
                                                    reader_cycle_money, reader_con_enable, reader_init_pulse,
                                                    reader_con_pulse, reader_pulse_duty, insert_input_date))
                conn.commit()

                trans = "GL041MS"
                trans += str(gls_config.MANAGER_CODE)
                trans += str(gls_config.reader).rjust(2, '0')
                trans += device_addr
                trans += reader_init_money
                trans += reader_con_money
                trans += reader_cycle_money
                trans += reader_con_enable
                trans += reader_init_pulse
                trans += reader_con_pulse
                trans += reader_pulse_duty
                trans += self.get_checksum(trans)
                trans += "CH"  # ETX
                trans = trans.encode("utf-8")

                print("reader_set : ", trans)

                try:
                    ser.readline(ser.write(bytes(trans)))

                except Exception as e:
                    print("transErr : ", e)
                    returun_res = '0'
                finally:
                    conn.close()
        except UnboundLocalError as ex:
            print('엑세스 거부', ex)
            returun_res = '0'
        except FileNotFoundError as ex:
            print('지정된 포트를 찾을 수 없습니다.', ex)
            returun_res = '0'
        except UnicodeDecodeError as ex1:
            print('디코딩 오류', ex1)
            returun_res = '0'
        except Exception as ex1:
            print('오류를 알 수 없습니다.', ex1)
            returun_res = '0'
        finally:
            pass
        return returun_res