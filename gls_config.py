import base64

# 데이터 수집 장치 접속 설정
MYSQL_HOST = "localhost"
MYSQL_USER = "pi"
MYSQL_PWD = "gls08300"
MYSQL_DB = "db_datacollect"
MYSQL_SET = "utf8mb4"

# 데이터 수집 장치 버전
DC_VERSION = "1.0.2"


# 디바이스 타입 넘버
SELF = 0
AIR = 1
MATE = 2
CHARGER = 3
COIN = 4
BILL = 5
TOUCH = 6
KIOSK = 7
POS = 8
READER = 9
GARAGE = 10

# 관리 업체
MANAGER_CODE = '01'

# 충전기 기본 보너스 설정
DEFAULT_BONUS = 2

# 신용카드 보너스 설정
CREDIT_BONUS = 1

# 등록카드 사용 기능 제어 변수
ENABLE_CARD = False

# 관리자 암호 설정
ADMIN_PW = base64.b64encode("gls12q23w".encode('utf-8'))
MANAGER_PW = base64.b64encode("gil190401".encode('utf-8'))

# 터치 충전기 접속 정보
PI_MYSQL_USER = "pi"
PI_MYSQL_PWD = "1234"
PI_MYSQL_DB = "glstech"