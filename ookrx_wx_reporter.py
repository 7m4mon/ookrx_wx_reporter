# -*- coding: utf-8 -*- 

# Raspberry Piで以下の電文をシリアルポートで受信・解析・チェックして、正しければ aprsサーバーに気象情報を送信する。
# "To,From,Latitude,Longtitude,Altitude,Tempreture(x10),Humidity(x10),Pressure(x10),CRC8(hex)"
# ex: 7M4MON,JM1ZLK,35.6866,139.7911,2.1,8,405,10011,fa
#
# CRCチェックは https://github.com/niccokunzmann/crc8 を使用
# APRS網に気象データを送信するプログラムは https://github.com/marsolla/Raspberry-APRS-Weather-Submit を使用
# 電文チェックに isascii() を使用しているので Python 3.7 以降が必要

import os
import serial   # pip install pyserial
import time
from enum import IntEnum, auto
import crc8     # https://github.com/niccokunzmann/crc8

WX_SUBMIT_PATH = '~/Raspberry-APRS-Weather-Submit/raspi-aprs-weather-submit'
WX_APRS_SERVER = 'japan.aprs2.net'
WX_APRS_PORT = '14579'
WX_USER_NAME = '7M4MON'             # Callsign registered on the APRS server
WX_VALIDATION_CODE = '99999'        # Set your Server Validation Code

# エラーコードの定義 (Enum)
class WX_PROC_ERROR(IntEnum):
    NO_ERROR = 0
    ERROR_FORMAT = auto()
    ERROR_CRC = auto()
    ERROR_NOT_MY_CALL = auto()
    ERROR_SENDER_INVALID = auto()
    ERROR_LATITUDE_INVALID = auto()
    ERROR_LONGTIDUDE_INVALID = auto()
    ERROR_ALTIDUDE_INVALID = auto()
    ERROR_TEMPRETURE_INVALID = auto()
    ERROR_HUMIDITY_INVALID = auto()
    ERROR_PRESSURE_INVALID = auto()
    ERROR_TEMPRETURE_OUTRANGE = auto()
    ERROR_HUMIDITY_OUTRANGE = auto()
    ERROR_PRESSURE_OUTRANGE = auto()

# 浮動小数点数値に変換可能かどうかを判定する
def isfloat(s):  
    try:
        float(s) 
    except ValueError:
        return False 
    else:
        return True 

# WXの値を入れるクラス（定義だけ）　set_wx_value()でセットされる
class WxList():
    pass
wx = WxList()

# wx 構造体に値をセットする
def set_wx_value(wx_str):
    if wx_str.count(',') != 8:    # 電文フォーマットが不正
        return WX_PROC_ERROR.ERROR_FORMAT
    wx_list = wx_str.split(',')
    wx.call_to = wx_list[0]
    wx.call_from = wx_list[1]
    wx.latitude = wx_list[2]
    wx.longtitude= wx_list[3]
    wx.altitude = wx_list[4]
    wx.tempreture = wx_list[5]
    wx.humidity = wx_list[6]
    wx.pressure = wx_list[7]
    wx.crc8 = wx_list[8]
    return 0

# 受信した電文（CRCや気象データやコールサイン）が正しいか検証する
def check_wx_value(wx_str):
    last_delimitter_index = wx_str.rfind(',')
    if wx.crc8 != get_crc8(wx_str[:last_delimitter_index+1]):   # CRCの計算範囲はカンマを含む
        return WX_PROC_ERROR.ERROR_CRC                          # CRC不一致
    if wx.call_to != WX_USER_NAME:
        return WX_PROC_ERROR.ERROR_NOT_MY_CALL                  # 自局宛でない
    if wx.call_from.isascii() == False:
        return WX_PROC_ERROR.ERROR_SENDER_INVALID               # 送り元のコールサインが不正
    if isfloat(wx.latitude) == False:
        return WX_PROC_ERROR.ERROR_LATITUDE_INVALID             # 緯度が数値でない
    if isfloat(wx.longtitude) == False:
        return WX_PROC_ERROR.ERROR_LONGTIDUDE_INVALID           # 経度が数値でない
    if isfloat(wx.altitude) == False:
        return WX_PROC_ERROR.ERROR_ALTIDUDE_INVALID             # 高度が数値でない
    if isfloat(wx.tempreture) == False:
        return WX_PROC_ERROR.ERROR_TEMPRETURE_INVALID           # 温度が数値でない
    if isfloat(wx.humidity) == False:
        return WX_PROC_ERROR.ERROR_HUMIDITY_INVALID             # 湿度が数値でない
    if isfloat(wx.pressure) == False:
        return WX_PROC_ERROR.ERROR_PRESSURE_INVALID             # 気圧が数値でない
    return 0

# 気温 湿度 気圧が範囲内か確認して正しければ値をセットする
def check_wx_range():
    tempreture = float(wx.tempreture)/10
    if tempreture < -90 or tempreture > 60 :    
        return WX_PROC_ERROR.ERROR_TEMPRETURE_OUTRANGE          # 温度が範囲外 
    humidity = float(wx.humidity)/10
    if humidity < 0 or humidity > 100 :         
        return WX_PROC_ERROR.ERROR_HUMIDITY_OUTRANGE            # 湿度が範囲外 
    pressure = float(wx.pressure)/10
    if pressure < 850 or pressure > 1100 :     
        return WX_PROC_ERROR.ERROR_PRESSURE_OUTRANGE            # 気圧が範囲外 
    wx.tempreture = '{:.1f}'.format(tempreture)
    wx.humidity = '{:.1f}'.format(humidity)
    wx.pressure = '{:.1f}'.format(pressure)
    return 0

# 受信した電文を解析・チェックして、正しければ aprsサーバーに気象情報を送信する
def proc_wx_data(wx_str):
    retval = set_wx_value(wx_str)
    if retval != 0:
        return retval
    retval = check_wx_value(wx_str)
    if retval != 0:
        return retval
    retval = check_wx_range()
    if retval != 0:
        return retval

    wx_submit_string = WX_SUBMIT_PATH \
                        + ' --server ' + WX_APRS_SERVER \
                        + ' --port ' + WX_APRS_PORT\
                        + ' --username ' + WX_USER_NAME \
                        + ' --password ' + WX_VALIDATION_CODE \
                        + ' --callsign ' + wx.call_from \
                        + ' --latitude ' + wx.latitude \
                        + ' --longitude ' + wx.longtitude \
                        + ' --altitude ' + wx.altitude \
                        + ' --temperature-celsius ' + wx.tempreture \
                        + ' --humidity ' + wx.humidity \
                        + ' --pressure ' + wx.pressure
    
    print(wx_submit_string)
    os.system(wx_submit_string)

    return 0

# CRC-8 を計算して hex (2文字) を返す
# Validated https://crccalc.com/
def get_crc8(data):
    hash = crc8.crc8()
    hash.update(data.encode('utf-8'))
    return hash.hexdigest()


def main():
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
    print('Waiting for receiving data...')
    try :
        while True:
            time.sleep(0.1)
            if ser.in_waiting > 0 :
                time.sleep(0.1)             # 受信中に読まないようにちょっと待つ
                read_str = ser.read_all().decode('utf-8')
                print("Rcv")
                print(read_str)
                print(proc_wx_data(read_str))
    except KeyboardInterrupt:
        ser.close()

if __name__ == "__main__":
    main()
