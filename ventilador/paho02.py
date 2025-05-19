import random,time
from i2c_iotv import *
#from din00 import boto
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt
import paho.mqtt.properties as properties

def v2aout(voltage0_10):
	retV = round((voltage0_10*4095)/10)
	if retV < 0:
		retV = 0
	if retV > 4095:
		retV = 4095
	return retV
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,'idClient-'+str(random.randrange(100000,999999)))
# mqttc.username_pw_set("usuari","contrasenya");
mqttc.connect("broker.emqx.io", 1883)

def on_message(clientId, userdata, message):
   msg = str(message.payload.decode("utf-8"))
   print('topic = ', message.topic)
   print('payload = ', msg)
   # Luz verde
   if message.topic == "/70B8F662BC7C/dout/verd":
      if msg == '1':
         doutbit('0000','B',4,1)
      else:
         doutbit('0000','B',4,0)
   # Luz roja
   if message.topic == "/70B8F662BC7C/dout/vermell":
      if msg == '1':
         doutbit('0000','B',5,1)
      else:
         doutbit('0000','B',5,0)
   # Luz naranja
   if message.topic == "/70B8F662BC7C/dout/emergencia":
      if msg == '1':
         aout("0000","B",1,v2aout(10))
         aout("0000","B",2,v2aout(5))
      else:
         aout("0000","B",1,v2aout(0))
         aout("0000","B",2,v2aout(0))

   if message.topic == "/70B8F662BC7C/dout/stop":
      if msg == '1':
         doutbit("0000","B",2,1)
      else:
         doutbit("0000","B",2,0)

   # Ventilador
   if message.topic == "/70B8F662BC7C/dout/ventilador":
      if msg == '1':
          doutbit("0000","B",1,1)
      else:
          doutbit("0000","B",1,0)
      
mqttc.on_message = on_message
# El hastag sirve para decir que se suscriba a todos los temas
time.sleep(5)
mqttc.subscribe('/70B8F662BC7C/#')

mqttc.loop_start()
# n = 0
while True:
   print("",end="")
   time.sleep(1)

