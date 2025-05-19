import random, time, threading, json, signal
from i2c_iotv import *
import paho.mqtt.client as mqtt
from primary import loop_principal, apagar_solo_salida, v2aout, stop_event, apagar_salida
from primary import leer_potenciometros, gestionar_boton_stop, gestionar_emergencia

# Crear cliente MQTT
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 'idClient-' + str(random.randrange(100000, 999999)))

# Control de estado para iniciar solo una vez
principal_corriendo = threading.Event()
principal_thread = None

# Callback al recibir mensaje
def on_message(clientId, userdata, message):
    global principal_thread
    global apagar_solo_salida
    global apagar_salida
	
    msg = str(message.payload.decode("utf-8"))
    print('topic = ', message.topic)
    print('payload = ', msg)

    try:
        data = json.loads(msg)
        msg_data = data.get('msg', [])

        if isinstance(msg_data, list) and len(msg_data) > 3:
            item4 = msg_data[3]
            invertido = ~item4 & 0xFF
            bin_inv = format(invertido, '08b')

            print(f"Invertido: {bin_inv}")

            if bin_inv[6] == '1':  # Encender sistema
                print("Encés")
                if not principal_thread or not principal_thread.is_alive():
                    stop_event.clear()
                    threading.Thread(target=leer_potenciometros, daemon=True).start()
                    threading.Thread(target=gestionar_boton_stop, daemon=True).start()
                    threading.Thread(target=gestionar_emergencia, daemon=True).start() #
                    principal_thread = threading.Thread(target=loop_principal, daemon=True)
                    principal_thread.start()
                    principal_corriendo.set()

            elif bin_inv[7] == '1':  # Apagar sistema
                print("Apagat")
                apagar_solo_salida()
                principal_corriendo.clear()
            else:
                print("Repós")
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Callback al conectar
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        print("Connectat!")
        mqttc.subscribe('/70B8F662BC7C/#')

# Configurar cliente
mqttc.on_connect = on_connect
mqttc.on_message = on_message

# Conectar al broker
mqttc.connect("broker.emqx.io", 1883)
mqttc.loop_start()
print("Petició per a connectar-se")

# Registrar señales en el hilo principal
signal.signal(signal.SIGINT, apagar_salida)
signal.signal(signal.SIGTERM, apagar_salida)
              
# Mantener el hilo principal activo
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    apagar_salida(None, None)
