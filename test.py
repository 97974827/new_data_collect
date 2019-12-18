import serial
import gls_config
import device
import time
from datetime import datetime
import pymysql
from collections import OrderedDict
dv = device.Device()
ser = serial.Serial(dv.PORT, dv.BAUD, timeout=1)
# a = 'GL057CS0103011000200100010030050070100150050050050050' # 성공
# b = 'GL057CS0103011000100100010030050070100110050050050050' # 실패
# print("check_sum : ", dv.get_checksum("GL029TS010301490919295959"))

# res1 = dv.get_checksum("GL017CL011001")
# print("1번 : ", res1)
#
# res2 = dv.get_checksum("GL017CL010302")
# print("2번 : ", res2)
#
# res3 = dv.get_checksum("GL017CL010303")
# print("3번 : ", res3)
#
# res4 = dv.get_checksum("GL017CL010304")
# print("4번 : ", res4)
#
# res5 = dv.get_checksum("GL017CL010305")
# print("5번 : ", res5)
#
# res6 = dv.get_checksum("GL017CL011006")
# print("6번 : ", res6)
#
# res7 = dv.get_checksum("GL017CL011007")
# print("7번 : ", res7)
#
# res8 = dv.get_checksum("GL017CL011008")
# print("8번 : ", res8)
#
# res9 = dv.get_checksum("GL017CL011009")
# print("9번 : ", res9)
#
# res10 = dv.get_checksum("GL017CL011010")
# print("10번 : ", res10)

#
# before = "GL 91GW10 0  119 5 6 0 219 0 222c63b39e5    0   0   0  15    0    0    0    0    0    090CH"
# after = before.replace(" ", "0")
# print(after)


# 기본, 기타 설정 저장
# conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD, charset='utf8mb4', db=gls_config.MYSQL_DB)
# curs = conn.cursor(pymysql.cursors.DictCursor)

# try:
#     with conn.cursor():
#         device_addr = '01'
#         query = "SELECT * FROM gl_self_config WHERE `device_addr` = %s ORDER BY `input_date` DESC LIMIT 1"
#         curs.execute(query, device_addr)
#         get_config = curs.fetchall()
#
#         # config = OrderedDict()
#         # config['device+addr'] = str(device_addr)
#
#         # print(get_config['self_init_time'])
#         print(get_config)
#
#
#
#
# except Exception as e:
#     print("From set_hidden_config except : ", e)
#     res = 0
# finally:
#     conn.close()




# #TODO: test
# print("시작 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
#

# # ser.set_output_flow_control()
# trans = "GL017CL01100133CH"
# # trans += str(gls_config.MANAGER_CODE)  # 회사 분류
# # trans += str(gls_config.SELF)
# # trans += "01" # 장비번호
# # trans += dv.get_checksum(trans)  # 체크섬
# # trans += "CH\r\n"  # ETX + 개행문자
# # trans = trans.encode("utf-8")
# ser.write(bytes(trans))
# trans = "GL017CL"
# trans += "01"       # 관리업체 번호
# trans += "00"  # 장비 타입
# trans += "01"                # 장비 주소
# trans += dv.get_checksum(trans)           # 체크섬
# trans += "CH"                               # ETX
# # # trans += "CH\r\n"  # ETX + 개행문자
# trans = "GL017OK"
# trans += str(gls_config.MANAGER_CODE)
# trans += str(gls_config.GARAGE).rjust(2, '0')
# trans += str('01')
# trans += dv.get_checksum(trans)
# trans += "CH"  # ETX
# trans = trans.encode("utf-8")
# state = ser.readline(ser.write(bytes(trans)) + 20)
# print(state)
# res = res.decode('utf-8')
# res = res.replace(" ", "0")
# print(res)
# res = res.decode('utf-8')
# res = res.replace(" ", "0")
#
# print(res)
# print("종료 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))

# #
# for i in range(0, 100):
#     trans = "GL057CS0103011000100100010030050070100050050050050050"
#     trans += str(i).rjust(2, "0")
#     trans += "CH"
#     # trans += "CH\r\n"  # ETX + 개행문자
#     trans = trans.encode('utf-8')
#     res = ser.readline(ser.write(bytes(trans)) + 120)
# # print(res)
#
#     print("시도 : ", i)
#
#     if res:
#         print("체크섬 : ", str(i).rjust(2, "0"))
#         print("res : ", res)





# temp = ser.read()
# print(temp)
# line = []
# orgin = []



# ser.readline(120)

# while 1:
# for i in range(1, 110):
#     # temp = ser.read().decode('utf-8')
#     temp = ser.read(1)
#     if temp:
#         # print(temp)
#         line.append(temp.decode('utf-8'))
#         print("슬립 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
#         # print(temp)
#
#         # print(line)
#     else:
#         orgin_res = ''.join(line)
#         res = orgin_res.replace(" ", "0")
#         # time.sleep(0.05)
#
#         # print(res)
#
#         print("종료 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
#
#         # print("읽기 종료")
#         # print(line)
#         break
# print("종료 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
# print(res)
# print(res[:2])
# ser.close()
# orgin_res = ''.join(line)
# res = orgin_res.replace(" ", "0")
# print(res)
# print("종료 ::: " + str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
# stx = res[0:2]
# etx = res[106:108]
# res_len = len(res)
# res_check_sum = res[104:106]
# get_sum = dv.get_checksum(orgin_res[:104])
# print(stx, etx, res_len, res_check_sum, get_sum)


# temp = ''.join(line)
# temp = temp.replace(" ", "0")
# print(temp)


# for res in range(1, 109):
#     res = ser.read().decode('utf-8')
#     line.append(res)





# res1 = ser.read(1)

# res = ser.readline(ser.write(bytes(trans)) + 120)

# res = res.decode("utf-8")    # 받은 값에 대한 디코드
# res = res.replace(" ", "0")  # 공백 치환
#
# class TEST:
#
#     global temp
#     temp = OrderedDict()
#
#     def test_thread(self):
#         # temp = OrderedDict()
#         temp['device_addr'] = '01'
#         temp['device_type'] = 'self'
#
#         # print(temp)
#         # print("test_thread")
#
#     def test_print(self):
#         print(temp)
#
#
#
# t = TEST()
# t.test_thread()
# t.test_print()

conn = pymysql.connect(host=gls_config.MYSQL_HOST, user=gls_config.MYSQL_USER, password=gls_config.MYSQL_PWD, charset=gls_config.MYSQL_SET, db=gls_config.MYSQL_DB)
curs = conn.cursor(pymysql.cursors.DictCursor)

try:
    with conn.cursor():
        query = "SELECT card.`card_num`, card.input_date, IFNULL((select `mb_no` FROM gl_member_card WHERE `num` = card.card_num), 0) AS 'mb_no' " \
                "FROM gl_card as card WHERE NOT card.card_num in('00000000') ORDER BY input_date DESC"
        curs.execute(query)
        res = curs.fetchall()

        for r in res:
            qquery = "SELECT sum(`current_charge`) * 100 AS 'total_money' FROM gl_charger_state WHERE card_num = %s"
            curs.execute(qquery, r['card_num'])

        print(res)
finally:
    conn.close()