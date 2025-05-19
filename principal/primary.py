from i2c_iotv import *
import time
import signal
import threading

luz_naranja_lock = threading.Lock()

puertas_abriendo_lock = threading.Lock()
puertas_abriendo = False
emergencia = False


def v2aout(voltage0_10):
	retV = round((voltage0_10*4095)/10)
	if retV < 0:
		retV = 0
	if retV > 4095:
		retV = 4095
	return retV
    
def ain2v(ainValue):
	return round((((20 * float(ainValue)) / 26624) - 10) * 100) / 100


# Se abren las puertas en caso de emergencia
def abrir_puertasE():
    global puertas_abriendo
    with puertas_abriendo_lock:
        if puertas_abriendo:
            print("Puertas ya están siendo abiertas. Emergencia ignorada.")
            return
        puertas_abriendo = True
    try:
        for _ in range(4):
            doutbit("0000", "B", 5, 1)
            time.sleep(0.5)
            doutbit("0000", "B", 5, 0)
            time.sleep(0.5)
        doutbit("0000", "B", 4, 1)
        
    finally:
        with puertas_abriendo_lock:
            puertas_abriendo = False

# Emergencia boton
def gestionar_emergencia():
    global emergencia
    while not stop_event.is_set():
        try:
            boton = din("0000", "A")[4]
            if str(boton) == "1" and not emergencia:
                # Activar emergencia
                emergencia = True
                print("Emergencia activada")

                # Apagar luz blanca
                aout("0000", "B", 4, v2aout(0))
                aout("0000", "B", 3, v2aout(0))
                time.sleep(0.2)

                while emergencia and not stop_event.is_set():
                    # Luz naranja
                    with luz_naranja_lock:
                        aout("0000", "B", 1, v2aout(10))
                        time.sleep(0.2)
                        aout("0000", "B", 2, v2aout(5))
                    # Abrir puertas en emergencia en un hilo
                    abrir_puertasE()
                    #threading.Thread(target=abrir_puertasE).start()
                    # Mantener la luz verde encendida
                    time.sleep(8)
                    doutbit("0000", "B", 4, 1)

            elif emergencia and str(boton) == "0":
                # Fin de emergencia
                emergencia = False
                print("Emergencia desactivada")
                doutbit("0000", "B", 2, 0)
                aout("0000", "B", 1, v2aout(0))
                aout("0000", "B", 2, v2aout(0))

        except Exception as e:
            print("Error en gestión de emergencia:", e)

        time.sleep(1)
		
# Se abren las puertas de forma normal
def abrir_puertas():
    global puertas_abriendo
    with puertas_abriendo_lock:
        if puertas_abriendo:
            print("Puertas ya están siendo abiertas. Acción normal ignorada.")
            return
        puertas_abriendo = True
    try:
        for _ in range(4):
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 1)
            time.sleep(0.5)
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 0)
            time.sleep(0.5)
        if stop_event.is_set(): return
        doutbit("0000", "B", 4, 1)
        if stop_event.is_set(): return
        time.sleep(10)
        if stop_event.is_set(): return
        doutbit("0000", "B", 4, 0)
        for _ in range(4):
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 1)
            time.sleep(0.5)
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 0)
            time.sleep(0.5)
    finally:
        with puertas_abriendo_lock:
            puertas_abriendo = False

# Se abren las puertas mas despacio cuando se pulsa el boton STOP            
def abrir_puertas_STOP():
    global puertas_abriendo
    with puertas_abriendo_lock:
        if puertas_abriendo:
            print("Puertas ya están siendo abiertas. Acción STOP ignorada.")
            return
        puertas_abriendo = True
    try:
        for _ in range(4):
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 1)
            time.sleep(0.5)
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 0)
            time.sleep(0.5)
        if stop_event.is_set(): return
        doutbit("0000", "B", 4, 1)
        if stop_event.is_set(): return
        time.sleep(20)
        if stop_event.is_set(): return
        doutbit("0000", "B", 4, 0)
        for _ in range(4):
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 1)
            time.sleep(0.5)
            if stop_event.is_set(): return
            doutbit("0000", "B", 5, 0)
            time.sleep(0.5)
    finally:
        with puertas_abriendo_lock:
            doutbit("0000", "B", 2, 0)
            puertas_abriendo = False

# Boton STOP  
def gestionar_boton_stop():
    ultimo_abrir_tiempo = 0
    while not stop_event.is_set():
        try:
            boton = din("0000", "A")[5]
            if str(boton) == "1":
                print("Botón STOP pulsado")
                doutbit("0000", "B", 2, 1)
                tiempo_actual = time.time()
                if tiempo_actual - ultimo_abrir_tiempo >= 30:
                    threading.Thread(target=abrir_puertas_STOP).start()
                    ultimo_abrir_tiempo = tiempo_actual

        except Exception as e:
            print("Error en gestión STOP:", e)

        time.sleep(0.5)  # Espera corta para mayor sensibilidad

# Cambia la intensidad y color de las luces del techo
def leer_potenciometros():
	while not stop_event.is_set():
		if emergencia:
			# Durante emergencia, no se controla luz blanca
			time.sleep(0.5)
			continue

		try:
			# Potenciómetro 2 (Temperatura)
			pot2 = ain2v(ain("0000", "A", 2))
			if valor_anterior2[0] != pot2:
				time.sleep(0.2)
				aout("0000", "B", 3, v2aout(pot2))  # Luz blanca parte 1
				time.sleep(0.2)
				aout("0000", "B", 1, 0)
				aout("0000", "B", 2, 0)
				valor_anterior2[0] = pot2
		except Exception as e:
			print("Error en potenciometro2:", e)

		try:
			# Potenciómetro 1 (Brillo)
			pot1 = ain2v(ain("0000", "A", 1))
			if valor_anterior1[0] != pot1:
				time.sleep(0.2)
				aout("0000", "B", 4, v2aout(pot1))  # Luz blanca parte 2
				time.sleep(0.2)
				aout("0000", "B", 1, 0)
				aout("0000", "B", 2, 0)
				valor_anterior1[0] = pot1
		except Exception as e:
			print("Error en potenciometro1:", e)

		if stop_event.wait(1.0):
			break

    
valor_anterior1 = [None]
valor_anterior2 = [None]
stop_event = threading.Event()

def loop_principal():
	global emergencia
	ultimo_abrir_tiempo = 0
	while not stop_event.is_set():
		# Spotlight
		try:
			doutbit("0000","B",6,1)
		except Exception as e:
			print("Error en spotlight:", e)
		
		# Abrir puerta normal
		try:
			tiempo_actual = time.time()
			if tiempo_actual - ultimo_abrir_tiempo >= 30:
				with puertas_abriendo_lock:
					if not puertas_abriendo:
						threading.Thread(target=abrir_puertas).start()
						ultimo_abrir_tiempo = tiempo_actual
		except Exception as e:
				print("Error en puerta:", e)		
		#if stop_event.wait(180):  # Espera 3 minutos (180 segundos) o hasta que se active el stop
		if stop_event.wait(10):
				break
			
		
		print("loop_principal terminado")
		if stop_event.wait(1.0):
			break

# Nuevas versiones
def apagar_solo_salida():
	global emergencia
	print("\nApagando salida analógica...")
	stop_event.set()
	try:
		# Apagar luz blanca
		aout("0000", "B", 3, 0)
		aout("0000", "B", 4, 0)
		# Apagar luz naranja
		aout("0000", "B", 1, 0)
		aout("0000", "B", 2, 0)
		emergencia = False
		# Apagar botón STOP
		doutbit("0000", "B", 2, 0)
		# Apagar salidas digitales
		doutbit("0000", "B", 6, 0)
		doutbit("0000", "B", 5, 0)
		doutbit("0000", "B", 4, 0)
		
	except Exception as e:
		print("Error al apagar salida:", e)
        
def apagar_salida(signal_num, frame):
	apagar_solo_salida()
	print("Saliendo del programa.")
	exit(0)



"""
# Conectar señales de salida (Ctrl+C o kill)
signal.signal(signal.SIGINT, apagar_salida)
signal.signal(signal.SIGTERM, apagar_salida)

# Iniciar el hilo principal
threading.Thread(target=loop_principal, daemon=True).start()

signal.pause()
"""
