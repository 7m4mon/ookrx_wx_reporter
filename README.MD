[ookrx_wx_reporter]はRaspberry Pi上で動作するPythonプログラムです。実行にはPython 3.7以上が必要です。
[wx_usb_bme280]で生成された電文をシリアルポートで受信し、解析・チェックして、正しければ APRSサーバーに気象情報を送信します。

![](https://github.com/7m4mon/ookrx_wx_reporter/blob/main/ookrx_wx_reporter-block.png)

APRS網に気象データを送信するプログラムは
https://github.com/marsolla/Raspberry-APRS-Weather-Submit


電文のCRC（データの誤り検出）や宛先（自局宛かどうか）、気象データの数値範囲などを確認し、  
正しければ raspi-aprs-weather-submitに以下のコマンドを発行します。なお、APRS網に登録されるには、
APRSサーバーから発行されたユーザー名と認証コードが必要です。  

os.system(wx_submit_string) にて Raspberry-APRS-Weather-Submit 例えば以下のコマンドを発行します。

```
~/Raspberry-APRS-Weather-Submit/raspi-aprs-weather-submit --server japan.aprs2.net --port 14579 --username 7M4MON --password 99999 --callsign JM1ZLK --latitude 35.6866 --longitude 139.7911 --altitude 2.0 --temperature-celsius 22.3 --humidity 34.2 --pressure 1020.4
```
