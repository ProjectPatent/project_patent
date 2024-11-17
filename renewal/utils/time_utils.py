from datetime import datetime
import pytz


def get_today_yyyymmdd(timezone="Asia/Seoul"):
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y%m%d")


def get_timestamp(timezone="Asia/Seoul"):
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def is_yyyymmdd_format(date_str):
    # yyyymmdd 형식이며 유효한 날짜인지 확인
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False
