from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
import pymysql
import gls_config
import device
import touch_charger
import pos
import time


# App Class 목록
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
1. 메인 스레드 시작          # StartThread
2. 포스 설정 불러오기
3. 포스 설정
4. 셀프 설정 불러오기
5. 셀프 설정
6. 진공 설정 불러오기
7. 진공 설정
8. 매트 설정 불러오기
9. 매트 설정
10. 충전기 설정 불러오기
11. 충전기 설정
12. 터치 설정 불러오기
13. 터치 설정
14. 키오스크 설정 불러오기
15. 키오스크 설정

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


# 임포트 python 정의
app = Flask(__name__)
api = Api(app)
dv = device.Device()
tch = touch_charger.TouchCharger()
ps = pos.Pos()

try :
    # 데이터베이스 접속 설정
    conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
                       charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
    curs = conn.cursor(pymysql.cursors.DictCursor)
    with conn.cursor():

        # 데이터수집장치 버전 업그레이드
        dc_ver_qry = "UPDATE gl_shop_info SET dc_version = %s"
        curs.execute(dc_ver_qry, gls_config.DC_VERSION)
        conn.commit()

        # 등록카드 사용 옵션 불러오기
        query = "SELECT `enable_card` FROM gl_pos_config"
        curs.execute(query)
        res = curs.fetchone()
        if str(res['enable_card']) == '1':
            gls_config.ENABLE_CARD = False
        elif str(res['enable_card']) == '0':
            gls_config.ENABLE_CARD = True

        # 485 쓰레드 설정
        get_charger_state = tch.get_charger_state(10)
        # update_vip = ps.update_vip(10)
        dv.set_time()
        dv.main_thread(1)
        # dv.thread_monitor(10)

finally:
    conn.close()


# 메인 스레드 시작
class StartThread(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        # dv.USE = True
        # dv.USE_EACH = False
        # dv.TIME_USE = True
        # dv.TIME_USE_EACH = False
        # dv.device_state_thread.cancel()
        # dv.FLAG_MAIN = 'cancel'
        # dv.main_thread(1)
        dv.thread_monitor()
        pass


# 포스 설정 불러오기
class GetPosConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        pos_config = ps.get_pos_config()
        return {"pos_config": pos_config}


# 누적금액 초기화
class ResetTotalMoney(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_type', type=str)
        parser.add_argument('device_addr', type=str)
        args = parser.parse_args()
        device_type = args['device_type']
        device_addr = args['device_addr']
        time.sleep(0.5)
        res = dv.reset_total_money(device_type, device_addr)
        # time.sleep(0.1)
        # dv.main_thread(1)
        return {'result': res}


# 기기 주소 변경
class ChangeDeviceAddr(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        # 디바이스 정보
        parser.add_argument('device_type', type=str)
        parser.add_argument('before_addr', type=str)
        parser.add_argument('after_addr', type=str)
        args = parser.parse_args()
        device_type = args['device_type']
        before_addr = args['before_addr']
        after_addr = args['after_addr']
        time.sleep(0.5)
        res = dv.change_device_addr(device_type, before_addr, after_addr)
        time.sleep(0.6)
        dv.main_thread(1)
        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 게러지 설정 불러오기 (PCB->DB->POS)
class GetGarageConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        garage_config = dv.get_garage_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return garage_config


# 셀프 세차기 설정 불러오기 (PCB->DB->POS)
class GetSelfConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        self_config = dv.get_self_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return self_config


# 진공 청소기 설정 불러오기 (PCB->DB->POS)
class GetAirConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        air_config = dv.get_air_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return air_config


# 매트 청소기 설정 불러오기 (PCB->DB->POS)
class GetMateConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        mate_config = dv.get_mate_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return mate_config


# 카드 충전기 설정 불러오기 (PCB->DB->POS)
class GetChargerConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        config = dv.get_charger_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return config


# 리더기 매트 설정 불러오기 (PCB->DB->POS)
class GetReaderConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        reader_config = dv.get_reader_config()
        # time.sleep(0.1)
        # dv.main_thread(1)
        return reader_config


# 터치 충전기 설정 불러오기 (device->DB->POS)
class GetTouchConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        res = tch.get_touch_config()
        time.sleep(0.1)
        dv.main_thread(1)
        return {"result": res}


# 키오스크 설정 불러오기 (device->DB->POS)
class GetKioskConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        res = ps.get_kiosk_config()
        time.sleep(0.1)
        dv.main_thread(1)
        return {'result': res}


# 게러지 설정 (POS->DB->PCB)
class SetGarageConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        # 디바이스 정보
        parser.add_argument('device_addr', type=str)
        # 셀프 설정
        parser.add_argument('btn1_init_money', type=str)
        parser.add_argument('btn1_init_time', type=str)
        parser.add_argument('btn2_init_money', type=str)
        parser.add_argument('btn2_init_time', type=str)
        parser.add_argument('con_money', type=str)
        parser.add_argument('con_time', type=str)

        parser.add_argument('self_time', type=str)
        parser.add_argument('self_count', type=str)
        parser.add_argument('foam_time', type=str)
        parser.add_argument('foam_count', type=str)
        parser.add_argument('under_time', type=str)
        parser.add_argument('under_count', type=str)
        parser.add_argument('coating_time', type=str)
        parser.add_argument('coating_count', type=str)
        parser.add_argument('air_time', type=str)
        parser.add_argument('air_count', type=str)
        parser.add_argument('airgun_time', type=str)
        parser.add_argument('airgun_count', type=str)

        # 기타 설정
        parser.add_argument('buzzer_time', type=str)
        parser.add_argument('cycle_money', type=str)
        parser.add_argument('coating_type', type=str)

        args = parser.parse_args()
        res = dv.set_garage_config(args)
        time.sleep(1)
        return {'result': res}


# 셀프 세차기 설정 (POS->DB->PCB)
class SetSelfConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        # 디바이스 정보
        parser.add_argument('device_addr', type=str)
        # 셀프 설정
        parser.add_argument('self_init_money', type=str)
        parser.add_argument('self_init_time', type=str)
        parser.add_argument('self_con_enable', type=str)
        parser.add_argument('self_con_money', type=str)
        parser.add_argument('self_con_time', type=str)
        parser.add_argument('self_pause_time', type=str)
        # 폼 설정
        parser.add_argument('foam_enable', type=str)
        parser.add_argument('foam_con_enable', type=str)
        parser.add_argument('foam_speedier', type=str)
        parser.add_argument('foam_init_money', type=str)
        parser.add_argument('foam_init_time', type=str)
        parser.add_argument('foam_con_money', type=str)
        parser.add_argument('foam_con_time', type=str)
        parser.add_argument('foam_pause_time', type=str)
        parser.add_argument('foam_end_delay', type=str)
        # 하부 설정
        parser.add_argument('under_enable', type=str)
        parser.add_argument('under_con_enable', type=str)
        parser.add_argument('under_speedier', type=str)
        parser.add_argument('under_init_money', type=str)
        parser.add_argument('under_init_time', type=str)
        parser.add_argument('under_con_money', type=str)
        parser.add_argument('under_con_time', type=str)
        parser.add_argument('under_pause_time', type=str)
        # 코팅 설정
        parser.add_argument('coating_enable', type=str)
        parser.add_argument('coating_con_enable', type=str)
        parser.add_argument('coating_speedier', type=str)
        parser.add_argument('coating_init_money', type=str)
        parser.add_argument('coating_init_time', type=str)
        parser.add_argument('coating_con_money', type=str)
        parser.add_argument('coating_con_time', type=str)
        parser.add_argument('coating_pause_time', type=str)
        # 기타 설정
        parser.add_argument('cycle_money', type=str)
        parser.add_argument('speedier_enable', type=str)
        parser.add_argument('use_type', type=str)
        parser.add_argument('pay_free', type=str)
        parser.add_argument('buzzer_time', type=str)
        parser.add_argument('pause_count', type=str)
        parser.add_argument('set_coating_output', type=str)
        parser.add_argument('secret_enable', type=str)
        parser.add_argument('secret_date', type=str)
        parser.add_argument('wipping_enable', type=str)
        parser.add_argument('wipping_temperature', type=str)

        args = parser.parse_args()

        res = dv.set_self_config(args)
        time.sleep(1)

        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 진공 청소기 설정 (POS->DB->PCB)
class SetAirConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('air_init_money', type=str)
        parser.add_argument('air_init_time', type=str)
        parser.add_argument('air_con_money', type=str)
        parser.add_argument('air_con_time', type=str)
        parser.add_argument('cycle_money', type=str)
        parser.add_argument('buzzer_time', type=str)
        parser.add_argument('air_con_enable', type=str)
        parser.add_argument('pay_free', type=str)
        parser.add_argument('key_enable', type=str)

        args = parser.parse_args()

        res = dv.set_air_config(args)
        time.sleep(1)

        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 매트 청소기 설정
class SetMateConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('mate_init_money', type=str)
        parser.add_argument('mate_init_time', type=str)
        parser.add_argument('mate_con_money', type=str)
        parser.add_argument('mate_con_time', type=str)
        parser.add_argument('cycle_money', type=str)
        parser.add_argument('buzzer_time', type=str)
        parser.add_argument('mate_con_enable', type=str)
        parser.add_argument('pay_free', type=str)
        parser.add_argument('key_enable', type=str)
        parser.add_argument('relay_delay', type=str)

        args = parser.parse_args()

        res = dv.set_mate_config(args)
        time.sleep(1)

        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 카드 충전기 설정
class SetChargerConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('card_min_price', type=str)
        parser.add_argument('card_price', type=str)
        parser.add_argument('auto_charge_enable', type=str)
        parser.add_argument('auto_charge_price', type=str)
        parser.add_argument('bonus1', type=str)
        parser.add_argument('bonus2', type=str)
        parser.add_argument('bonus3', type=str)
        parser.add_argument('bonus4', type=str)
        parser.add_argument('bonus5', type=str)
        parser.add_argument('bonus6', type=str)
        parser.add_argument('bonus7', type=str)
        parser.add_argument('bonus8', type=str)
        parser.add_argument('bonus9', type=str)
        parser.add_argument('bonus10', type=str)

        args = parser.parse_args()

        res = dv.set_charger_config(args)
        time.sleep(1)

        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 리더기 매트 설정
class SetReaderConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('reader_init_money', type=str)
        parser.add_argument('reader_con_money', type=str)
        parser.add_argument('reader_cycle_money', type=str)
        parser.add_argument('reader_con_enable', type=str)
        parser.add_argument('reader_init_pulse', type=str)
        parser.add_argument('reader_con_pulse', type=str)
        parser.add_argument('reader_pulse_duty', type=str)

        args = parser.parse_args()

        res = dv.set_reader_config(args)
        time.sleep(1)

        # 디바이스에서 전송된 값 전송
        return {'result': res}


# 터치 충전기 설정
class SetTouchConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('device_addr', type=str)
        parser.add_argument('shop_pw', type=str)
        parser.add_argument('card_price', type=str)
        parser.add_argument('card_min_price', type=str)
        parser.add_argument('bonus1', type=str)
        parser.add_argument('bonus2', type=str)
        parser.add_argument('bonus3', type=str)
        parser.add_argument('bonus4', type=str)
        parser.add_argument('bonus5', type=str)
        parser.add_argument('bonus6', type=str)
        parser.add_argument('bonus7', type=str)
        parser.add_argument('bonus8', type=str)
        parser.add_argument('bonus9', type=str)
        parser.add_argument('bonus10', type=str)
        parser.add_argument('auto_charge_enable', type=str)
        parser.add_argument('auto_charge_price', type=str)
        parser.add_argument('exhaust_charge_enable', type=str)
        parser.add_argument('rf_reader_type', type=str)
        parser.add_argument('shop_no', type=str)
        parser.add_argument('name', type=str)

        args = parser.parse_args()

        res = tch.set_touch_config(args)

        return {'result': res}


# 키오스크 설정
class SetKioskConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('shop_pw', type=str)
        parser.add_argument('card_price', type=str)
        parser.add_argument('card_min_price', type=str)
        parser.add_argument('bonus1', type=str)
        parser.add_argument('bonus2', type=str)
        parser.add_argument('bonus3', type=str)
        parser.add_argument('bonus4', type=str)
        parser.add_argument('bonus5', type=str)
        parser.add_argument('bonus6', type=str)
        parser.add_argument('bonus7', type=str)
        parser.add_argument('bonus8', type=str)
        parser.add_argument('bonus9', type=str)
        parser.add_argument('bonus10', type=str)
        parser.add_argument('credit_bonus1', type=str)
        parser.add_argument('credit_bonus2', type=str)
        parser.add_argument('credit_bonus3', type=str)
        parser.add_argument('credit_bonus4', type=str)
        parser.add_argument('credit_bonus5', type=str)
        parser.add_argument('credit_bonus6', type=str)
        parser.add_argument('credit_bonus7', type=str)
        parser.add_argument('credit_bonus8', type=str)
        parser.add_argument('credit_bonus9', type=str)
        parser.add_argument('credit_bonus10', type=str)
        parser.add_argument('auto_charge_enable', type=str)
        parser.add_argument('auto_charge_price', type=str)
        parser.add_argument('exhaust_charge_enable', type=str)
        parser.add_argument('rf_reader_type', type=str)
        parser.add_argument('shop_no', type=str)
        parser.add_argument('name', type=str)
        args = parser.parse_args()
        res = ps.set_kiosk_config(args)
        return {'result': res}


# POS 설정
class SetPosConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        # 기기 설정
        parser.add_argument('self_count', type=str)       # 셀프 세차기 수량
        parser.add_argument('air_count', type=str)        # 진공 청소기 수량
        parser.add_argument('mate_count', type=str)       # 매트 세척기 수량
        parser.add_argument('charger_count', type=str)    # 카드 충전기 수량
        parser.add_argument('coin_count', type=str)       # 동전 교환기 수량
        parser.add_argument('bill_count', type=str)       # 지폐 교환기 수량
        parser.add_argument('touch_count', type=str)      # 터치 충전기 수량
        parser.add_argument('kiosk_count', type=str)      # 키오스크 수량
        parser.add_argument('reader_count', type=str)     # 매트 리더기 수량
        parser.add_argument('garage_count', type=str)     # 게러지 수량

        # 기본 설정
        parser.add_argument('shop_id', type=str)          # 세차장 아이디
        parser.add_argument('shop_pw', type=str)          # 세차장 패스워드
        parser.add_argument('shop_no', type=str)          # 세차장 관리번호
        parser.add_argument('shop_name', type=str)        # 세차장 상호
        parser.add_argument('shop_tel', type=str)         # 세차장 전화번호
        parser.add_argument('addr', type=str)             # 세차장 주소
        parser.add_argument('ceo', type=str)              # 세차장 대표
        parser.add_argument('business_number', type=str)  # 세차장 사업자 번호
        parser.add_argument('manager_no', type=str)       # 관리 업체 번호

        # 기타 설정
        parser.add_argument('encry', type=str)            # 매출자료 암호 사용
        parser.add_argument('list_enable', type=str)      # 매출계 표시
        parser.add_argument('weather_area', type=str)     # 날씨 지역
        parser.add_argument('weather_url', type=str)      # 날씨 URL
        parser.add_argument('master_card_num', type=str)  # 마스터 카드
        parser.add_argument('set_vip', type=str)          # 우수회원 시스템 사용 여부

        args = parser.parse_args()
        res = ps.set_pos_config(args)

        return {"result": res}


# 동작상태 전송(485)
class GetDeviceState(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        # dv.USE = True
        # dv.USE_EACH = False
        # dv.TIME_USE = True
        # dv.TIME_USE_EACH = False
        # dv.device_state_thread.cancel()
        # dv.device_state_thread.join()
        dv.USE = False
        dv.USE_EACH = True
        # dv.FLAG_MAIN = "monitor"
        res = dv.get_device_state()
        return {'result': res}


# 동작상태 전송(LAN)
class GetLanDeviceState(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_lan_device_state()
        return {'result': res}


# 월간 매출 리스트
class GetMonthlySales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        args = parser.parse_args()
        year = args['year']
        month = args['month']
        res = ps.get_monthly_sales(year, month)
        return {'result': res}


# 일간 매출 리스트
class GetDaysSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        parser.add_argument('days', type=str)
        args = parser.parse_args()
        year = args['year']
        month = args['month']
        days = args['days']
        res = ps.get_days_sales(year, month, days)
        return {'result': res}


# 기기별 일간 매출 리스트
class GetDeviceSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        parser.add_argument('days', type=str)
        args = parser.parse_args()
        year = args['year']
        month = args['month']
        days = args['days']
        res = ps.get_device_sales(year, month, days)
        return {'result': res}


# 메인화면 세차장비 매출
class GetTodayDeviceSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_today_device_sales()
        return {'result': res}


# 메인화면 충전장비 매출
class GetTodayChargerSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_today_charger_sales()
        return {'result': res}


# 메인화면 매출 총계
class GetTodaySalesTotal(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_today_sales_total()
        return {'result': res}


# 회원 목록 조회
class GetMemberList(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_member_list()
        return {'result': res}


# 회원 레벨 조회
class GetMemberLevel(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_member_level()
        return {'result': res}


# 회원 정보 조회
class GetMemberDetail(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('mb_no', type=str)
        args = parser.parse_args()
        mb_no = args['mb_no']
        res = ps.get_member_detail(mb_no)
        return {'result': res}


# 회원 등록 및 수정
class SetMember(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('no', type=str)
        parser.add_argument('level', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('birth', type=str)
        parser.add_argument('mobile', type=str)
        parser.add_argument('car_num', type=str)
        parser.add_argument('addr', type=str)
        parser.add_argument('group', type=str)
        parser.add_argument('card_num', type=str)
        parser.add_argument('vip_set', type=str)
        args = parser.parse_args()

        res = ps.set_member(args)
        return {'result': res}


# 회원 삭제
class DeleteMember(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('no', type=str)
        args = parser.parse_args()
        no = args['no']
        res = ps.delete_member(no)
        return {'result': res}


# 회원 이력
class GetMemberHistory(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_member_history()
        return {'result': res}


# 회원 상세 이력
class GetMemberHistoryDetail(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('mb_no', type=str)
        args = parser.parse_args()
        mb_no = args['mb_no']
        res = ps.get_member_history_detail(mb_no)
        return {'result': res}


# 회원 검색
class SearchMember(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('mobile', type=str)
        parser.add_argument('car_num', type=str)
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        name = args['name']
        mobile = args['mobile']
        car = args['car_num']
        card = args['card_num']
        res = ps.search_member(name, mobile, car, card)
        return {'result': res}


# 장비 이력 조회
class GetUseDevice(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_use_device()
        return {'result': res}


# 장비 세부 이력 조회
class GetUseDeviceDetail(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_type', type=str)
        parser.add_argument('device_addr', type=str)
        args = parser.parse_args()
        type = args['device_type']
        addr = args['device_addr']
        res = ps.get_use_device_detail(type, addr)
        return {'result': res}


# 장비 전체 이력 초기화
class ResetDeviceHistory(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.reset_device_history()
        return {'result': res}


# 카드 등록
class SetCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        res = ps.set_card(card_num)
        return {'result': res}


# 카드 정보 읽기
class ReadCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        res = ps.read_card(card_num)
        return {'result': res}


# 카드 이력 조회
class GetCardHistory(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_card_history()
        return {'result': res}


# 카드 상세 이력 조회
class GetCardHistoryDetail(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        res = ps.get_card_history_detail(card_num)
        return {'result': res}


# 카드 검색
class SearchCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        parser.add_argument('mb_no', type=str)
        parser.add_argument('end_time', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        mb_no = args['mb_no']
        input_date = args['end_time']
        res = ps.search_card(card_num, mb_no, input_date)
        return {'result': res}


# 카드 이력 초기화
class ResetCardHistory(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        res = ps.reset_card_history(card_num)
        return {'result': res}


# 정지 카드 조회
class GetBlackCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_black_card()
        return {'result': res}


# 정지 카드 등록
class SetBlackCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        parser.add_argument('content', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        content = args['content']
        res = ps.set_black_card(card_num, content)
        return {'result': res}


# 정지 카드 해제
class DeleteBlackCard(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('no', type=str)
        args = parser.parse_args()
        card_num = args['no']
        res = ps.delete_black_card(card_num)
        return {'result': res}


# 카드충전
class SetCharge(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)  # 카드번호
        parser.add_argument('charge', type=str)    # 충전 금액
        parser.add_argument('minus', type=str)     # 차감 금액
        parser.add_argument('bonus', type=str)     # 보너스 금액
        parser.add_argument('remain', type=str)    # 카드 잔액
        parser.add_argument('use', type=str)       # 사용처
        parser.add_argument('sales', type=str)     # 매출여부
        parser.add_argument('income', type=str)    # 수입여부
        args = parser.parse_args()
        res = ps.set_charge(args)
        return {'result': res}


# 세차장 ID 변경
class UpdateShopNo(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        dv.USE = True
        dv.USE_EACH = False
        dv.TIME_USE = True
        dv.TIME_USE_EACH = False
        dv.device_state_thread.cancel()
        dv.FLAG_MAIN = 'cancel'
        dv.FLAG_STATE = 'stop'
        parser = reqparse.RequestParser()
        parser.add_argument('device_type', type=str)
        parser.add_argument('device_addr', type=str)
        args = parser.parse_args()
        device_type = args['device_type']
        device_addr = args['device_addr']
        time.sleep(0.5)
        res = dv.update_shop_no(device_type, device_addr)
        # time.sleep(0.1)
        # dv.main_thread(1)
        return {'result': res}


# 관리 업체 정보 불러오기
class GetManagerInfo(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_manager_info()
        return {'result': res}


# 관리 업체 리스트 불러오기
class GetManagerList(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_manager_list()
        return {'result': res}


# CRC 테이블 불러오기
class GetCRC(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_crc()
        return {'result': res}


# 등록된 장비 목록 불러오기
class GetDeviceList(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_device_list()
        return {'result': res}


# 우수회원 보너스 가져오기
class GetVipBonus(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('card_num', type=str)
        args = parser.parse_args()
        card_num = args['card_num']
        res = ps.get_vip_bonus(card_num)
        return res


# 회원 보너스 가져오기
class GetMemberBonus(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_member_bonus()
        return {'result': res}


# 회원 보너스 설정
class SetMemberBonus(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('period', type=str)
        parser.add_argument('lv1_name', type=str)
        parser.add_argument('lv2_name', type=str)
        parser.add_argument('lv3_name', type=str)
        parser.add_argument('lv1_money', type=str)
        parser.add_argument('lv2_money', type=str)
        parser.add_argument('lv3_money', type=str)
        parser.add_argument('lv1_bonus1', type=str)
        parser.add_argument('lv2_bonus1', type=str)
        parser.add_argument('lv3_bonus1', type=str)
        parser.add_argument('lv1_bonus2', type=str)
        parser.add_argument('lv2_bonus2', type=str)
        parser.add_argument('lv3_bonus2', type=str)
        parser.add_argument('lv1_bonus3', type=str)
        parser.add_argument('lv2_bonus3', type=str)
        parser.add_argument('lv3_bonus3', type=str)
        parser.add_argument('lv1_bonus4', type=str)
        parser.add_argument('lv2_bonus4', type=str)
        parser.add_argument('lv3_bonus4', type=str)
        parser.add_argument('lv1_bonus5', type=str)
        parser.add_argument('lv2_bonus5', type=str)
        parser.add_argument('lv3_bonus5', type=str)
        parser.add_argument('lv1_bonus6', type=str)
        parser.add_argument('lv2_bonus6', type=str)
        parser.add_argument('lv3_bonus6', type=str)
        parser.add_argument('lv1_bonus7', type=str)
        parser.add_argument('lv2_bonus7', type=str)
        parser.add_argument('lv3_bonus7', type=str)
        parser.add_argument('lv1_bonus8', type=str)
        parser.add_argument('lv2_bonus8', type=str)
        parser.add_argument('lv3_bonus8', type=str)
        parser.add_argument('lv1_bonus9', type=str)
        parser.add_argument('lv2_bonus9', type=str)
        parser.add_argument('lv3_bonus9', type=str)
        parser.add_argument('lv1_bonus10', type=str)
        parser.add_argument('lv2_bonus10', type=str)
        parser.add_argument('lv3_bonus10', type=str)
        args = parser.parse_args()
        res = ps.set_member_bonus(args)
        return {'result': res}


# 마스터 카드 이력 조회
class GetMasterCardHistory(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_master_card_history()
        return {'result': res}


# 마스터 설정 불러오기
class GetMasterConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('auth_code', type=str)
        args = parser.parse_args()
        auth_code = args['auth_code']
        res = ps.get_master_config(auth_code)
        return {'result': res}


# 마스터 설정
class SetMasterConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('auth_code', type=str)
        parser.add_argument('manager_no', type=str)
        parser.add_argument('enable_card', type=str)
        parser.add_argument('card_binary', type=str)
        args = parser.parse_args()
        auth_code = args['auth_code']
        manager_no = args['manager_no']
        enable_card = args['enable_card']
        card_binary = args['card_binary']
        res = ps.set_master_config(auth_code, manager_no, enable_card, card_binary)
        return {'result': res}


# 히든 설정 불러오기
class GetHiddenConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        args = parser.parse_args()
        device_addr = args['device_addr']
        res = ps.get_hidden_config(device_addr)
        return {'result': res}


# 히든 설정
class SetHiddenConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_addr', type=str)
        parser.add_argument('enable_type', type=str)
        parser.add_argument('pay_type', type=str)
        parser.add_argument('coating_type', type=str)
        parser.add_argument('wipping_enable', type=str)
        parser.add_argument('wipping_temp', type=str)
        args = parser.parse_args()
        res = ps.set_hidden_config(args)
        return {'result': res}


# 셀프 주소 불러오기
class GetSelfList(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        res = ps.get_self_list()
        return {'result': res}


# 장비 설정 복사
class CopyDeviceConfig(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('device_type', type=str)
        parser.add_argument('current_device_addr', type=str)
        parser.add_argument('copy_device_addr', type=str)
        args = parser.parse_args()
        type = args['device_type']
        copy = args['current_device_addr']
        target = args['copy_device_addr']
        res = dv.copy_device_config(type, copy, target)
        return {'result': res}


# 신용 카드 월간 매출
class GetCreditSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        args = parser.parse_args()
        year = args['year']
        month = args['month']
        res = ps.get_credit_sales(year, month)
        return {'result': res}


# 신용 카드 일간 매출
class GetCreditDaysSales(Resource):
    # noinspection PyMethodMayBeStatic
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('year', type=str)
        parser.add_argument('month', type=str)
        parser.add_argument('day', type=str)
        args = parser.parse_args()
        year = args['year']
        month = args['month']
        day = args['day']
        res = ps.get_credit_days_sales(year, month, day)
        return {'result': res}



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 ****************************** Uri Path 설정 *********************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
api.add_resource(StartThread, '/start_thread')                          # 메인 쓰레드 실행

api.add_resource(GetReaderConfig, '/get_reader_config')                 # 리더기 매트 설정 (PCB->DB->POS)
api.add_resource(SetReaderConfig, '/set_reader_config')                 # 리더기 매트 설정 (POS->DB->PCB)

api.add_resource(GetTouchConfig, '/get_touch_config')                   # 터치 충전기 설정 (device->DB->POS)
api.add_resource(SetTouchConfig, '/set_touch_config')                   # 터치 충전기 설정 (POS->DB->device)

api.add_resource(GetKioskConfig, '/get_kiosk_config')                   # 키오스크 설정 (DB->POS)
api.add_resource(SetKioskConfig, '/set_kiosk_config')                   # 키오스크 설정 (POS->DB)

api.add_resource(GetPosConfig, '/get_pos_config')                       # 포스 설정 (DB->POS)
api.add_resource(SetPosConfig, '/set_pos_config')                       # 포스 설정 (POS->DB)

api.add_resource(GetMonthlySales, '/get_monthly_sales')                 # 월간 매출 조회
api.add_resource(GetDaysSales, '/get_days_sales')                       # 일간 매출 조회
api.add_resource(GetDeviceSales, '/get_device_sales')                   # 기기별 일간 매출 조회
api.add_resource(GetTodayDeviceSales, '/get_today_device_sales')        # 금일 세차 매출 조회
api.add_resource(GetTodayChargerSales, '/get_today_charger_sales')      # 금일 충전 내역 조회
api.add_resource(GetTodaySalesTotal, '/get_today_sales_total')          # 금일 매출 총합

api.add_resource(GetUseDevice, '/get_use_device')                       # 장비 이력 조회
api.add_resource(GetUseDeviceDetail, '/get_use_device_detail')          # 장비 세부 이력 조회
api.add_resource(ResetDeviceHistory, '/reset_device_history')           # 장비 전체 이력 초기화

api.add_resource(SetCard, '/set_card')                                  # 카드 등록
api.add_resource(ReadCard, '/read_card')                                # 카드 정보 읽기
api.add_resource(SearchCard, '/search_card')                            # 카드 검색
api.add_resource(ResetCardHistory, '/reset_card_history')               # 카드 이력 초기화

api.add_resource(GetCardHistory, '/get_card_history')                   # 카드 사용 이력 조회
api.add_resource(GetCardHistoryDetail, '/get_card_history_detail')      # 카드 이력 상세 조회

api.add_resource(GetBlackCard, '/get_black_card')                       # 정지 카드 조회
api.add_resource(SetBlackCard, '/set_black_card')                       # 정지 카드 등록
api.add_resource(DeleteBlackCard, '/delete_black_card')                 # 정지 카드 해제

api.add_resource(GetMemberList, '/get_member_list')                     # 회원 조회
api.add_resource(GetMemberLevel, '/get_member_level')                   # 회원 레밸 조회
api.add_resource(GetMemberDetail, '/get_member_detail')                 # 회원 상세 조회
api.add_resource(SetMember, '/set_member')                              # 회원 등록
api.add_resource(DeleteMember, '/delete_member')                        # 회원 삭제
api.add_resource(GetMemberHistory, '/get_member_history')               # 회원 이력
api.add_resource(GetMemberHistoryDetail, '/get_member_history_detail')  # 회원 상세 이력
api.add_resource(SearchMember, '/search_member')                        # 회원 검색

api.add_resource(SetCharge, '/set_charge')                              # 수동 충전

api.add_resource(GetGarageConfig, '/get_garage_config')                 # 게러지 설정 (PCB->DB->POS)
api.add_resource(SetGarageConfig, '/set_garage_config')                 # 게러지 설정 (POS->DB->PCB)

api.add_resource(GetSelfConfig, '/get_self_config')                     # 셀프 세차기 설정 (PCB->DB->POS)
api.add_resource(SetSelfConfig, '/set_self_config')                     # 셀프 세차기 설정 (POS->DB->PCB)

api.add_resource(GetAirConfig, '/get_air_config')                       # 진공 청소기 설정 (PCB->DB->POS)
api.add_resource(SetAirConfig, '/set_air_config')                       # 진공 청소기 설정 (POS->DB->PCB)

api.add_resource(GetMateConfig, '/get_mate_config')                     # 매트 청소기 설정 (PCB->DB->POS)
api.add_resource(SetMateConfig, '/set_mate_config')                     # 매트 청소기 설정 (POS->DB->PCB)

api.add_resource(GetChargerConfig, '/get_charger_config')               # 카드 충전기 설정 (PCB->DB->POS)
api.add_resource(SetChargerConfig, '/set_charger_config')               # 카드 충전기 설정 (POS->DB->PCB)

api.add_resource(GetDeviceState, '/get_device_state')                   # 동작 상태 전송 (POS->DB->PCB)
api.add_resource(GetLanDeviceState, '/get_lan_device_state')            # 동작 상태 전송 (POS->DB->PCB)

api.add_resource(ChangeDeviceAddr, '/change_device_addr')               # 기기 주소 변경 (POS->DB->PCB)
api.add_resource(ResetTotalMoney, '/reset_total_money')                 # 누적금액초기화 (POS->DB->PCB)
api.add_resource(UpdateShopNo, '/update_shop_no')                       # 세차장 ID 변경 (POS->DB->PCB)

api.add_resource(GetManagerInfo, '/get_manager_info')                   # 관리 업체 정보 불러오기
api.add_resource(GetManagerList, '/get_manager_list')                   # 관리 업체 리스트 불러오기
api.add_resource(GetCRC, '/get_crc')                                    # CRC 테이블 불러오기
api.add_resource(GetDeviceList, '/get_device_list')                     # 등록된 장비 목록 불러오기

api.add_resource(GetVipBonus, '/get_vip_bonus')                         # 우수회원 보너스 불러오기
api.add_resource(GetMemberBonus, '/get_member_bonus')                   # 회원 보너스 설정 불러오기
api.add_resource(SetMemberBonus, '/set_member_bonus')                   # 회원 보너스 설정

api.add_resource(GetMasterCardHistory, '/get_master_card_history')      # 마스터 카드 이력 조회

api.add_resource(GetMasterConfig, '/get_master_config')                 # 마스터 설정 불러오기
api.add_resource(SetMasterConfig, '/set_master_config')                 # 마스터 설정

api.add_resource(GetHiddenConfig, '/get_hidden_config')                 # 히든 설정 불러오기
api.add_resource(SetHiddenConfig, '/set_hidden_config')                 # 히든 설정


api.add_resource(GetSelfList, '/get_self_list')                         # 셀프 주소 추출(히든)

api.add_resource(CopyDeviceConfig, '/copy_device_config')               # 장비 설정 복사

api.add_resource(GetCreditSales, '/get_credit_sales')                   # 신용 카드 월간 매출
api.add_resource(GetCreditDaysSales, '/get_credit_days_sales')          # 신용 카드 일간 매출



if __name__ == '__main__':
    app.run(host="0.0.0.0")

    # try:
    #     # 데이터베이스 접속 설정
    #     conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD,
    #                            charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
    #     curs = conn.cursor(pymysql.cursors.DictCursor)
    #     with conn.cursor():
    #
    #
    #         get_charger_state = tch.get_charger_state(10)
    #         update_vip = ps.update_vip(10)
    #         dv.thread_monitor(600)
    #
    # finally:
    #     conn.close()
