# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import smbus
from time import sleep
from twython import Twython
import json
 
# jsonファイルを読み込む
f = open("twitter_plant_twol.json")
# jsonデータを読み込んだファイルオブジェクトからPythonデータを作成
data = json.load(f)
# ファイルを閉じる
f.close()

#twitterの認証情報を入力
CONSUMER_KEY    = data["CK"]
CONSUMER_SECRET = data["CS"]
ACCESS_KEY      = data["AK"]
ACCESS_SECRET   = data["AS"]
api = Twython(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_KEY,ACCESS_SECRET)

# MCP3208からSPI通信で12ビットのデジタル値を取得。0から7の8チャンネル使用可
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	if adcnum > 7 or adcnum < 0:
		return -1
	GPIO.output(cspin, GPIO.HIGH)
	GPIO.output(clockpin, GPIO.LOW)
	GPIO.output(cspin, GPIO.LOW)

	commandout = adcnum
	commandout |= 0x18
	commandout <<= 3
	for i in range(5):
		# LSBから数えて8ビット目から4ビット目までを送信
		if commandout & 0x80:
			GPIO.output(mosipin, GPIO.HIGH)
		else:
			GPIO.output(mosipin, GPIO.LOW)
		commandout <<= 1
		GPIO.output(clockpin, GPIO.HIGH)
		GPIO.output(clockpin, GPIO.LOW)
	adcout = 0
	# 13ビット読む
	for i in range(13):
		GPIO.output(clockpin, GPIO.HIGH)
		GPIO.output(clockpin, GPIO.LOW)
		adcout <<= 1
		if i>0 and GPIO.input(misopin)==GPIO.HIGH:
			adcout |= 0x1
	GPIO.output(cspin, GPIO.HIGH)
	return adcout

# 気温を測る
def read_adt7410():
    word_data =  bus.read_word_data(address_adt7410, register_adt7410)
    data = (word_data & 0xff00)>>8 | (word_data & 0xff)<<8
    data = data>>3 # 13ビットデータ
    if data & 0x1000 == 0:  # 温度が正または0の場合
        temperature = data*0.0625
    else: # 温度が負の場合、 絶対値を取ってからマイナスをかける
        temperature = ( (~data&0x1fff) + 1)*-0.0625
    return temperature

GPIO.setmode(GPIO.BCM)
# ピンの名前を変数として定義
SPICLK = 11
SPIMOSI = 10
SPIMISO = 9
SPICS = 8
# SPI通信用の入出力を定義
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICS, GPIO.OUT)

bus = smbus.SMBus(1)
address_adt7410 = 0x48
register_adt7410 = 0x00

# LED
GPIO.setup(25, GPIO.OUT)

try:
	inputVal0 = readadc(0, SPICLK, SPIMOSI, SPIMISO, SPICS)
	temp = read_adt7410()
	print(inputVal0, temp)
	api.update_status(status= 'ただいまの温度は ' + str(temp) + ' 度です。潤い ' + str(inputVal0))
	# 土が乾いていたらLEDを点灯する
	if inputVal0 < 600:
		GPIO.output(25, GPIO.HIGH)
	else:
		GPIO.output(25, GPIO.LOW)

except KeyboardInterrupt:
	pass

GPIO.cleanup()
