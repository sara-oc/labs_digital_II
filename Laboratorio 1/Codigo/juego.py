from machine import Pin, mem32 #importar librerias
import time, random 

#buzz = Pin 23
#led1 = Pin 22
#led2 = Pin 21
#led3 = Pin 19


GPIO_OUT_REG = 0x3FF44004 #configurar direccion de los pines como salida
GPIO_ENABLE_REG = 0x3FF44020 # Voltaje pines

mem32[GPIO_ENABLE_REG] = 0b111010000000000000000000 # habilitar salidas

pul_inicio = Pin(32, Pin.IN, Pin.PULL_DOWN) #definir pines de pulasdores y tipo de entrada/salida

pul1_1 = Pin(27, Pin.IN, Pin.PULL_DOWN)
pul1_2 = Pin(26, Pin.IN, Pin.PULL_DOWN)
pul1_3 = Pin(25, Pin.IN, Pin.PULL_DOWN)
pul1_4 = Pin(33, Pin.IN, Pin.PULL_DOWN)

pul2_1 = Pin(2, Pin.IN, Pin.PULL_DOWN)
pul2_2 = Pin(4, Pin.IN, Pin.PULL_DOWN)
pul2_3 = Pin(5, Pin.IN, Pin.PULL_DOWN)
pul2_4 = Pin(18, Pin.IN, Pin.PULL_DOWN)

inter1 = Pin(14, Pin.IN, Pin.PULL_UP)
inter2 = Pin(13, Pin.IN, Pin.PULL_UP)

#INICIO

while True:

    print("Sistema listo. Presiona el botón para iniciar.")

    while pul_inicio.value() == 0:
        pass

    time.sleep(0.3)  # anti-rebote básico

    print("¿1 jugador o 2 jugadores? Presiona una vez para 1 jugador, dos veces para 2 jugadores")

    conteo = 0
    inicio_tiempo = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), inicio_tiempo) < 6000:
        if pul_inicio.value() == 1:
            conteo += 1
            print("Pulsación detectada:", conteo)
            while pul_inicio.value() == 1: 
                pass
            time.sleep(0.2) # esperar a que suelte (antirrebote)

    if conteo == 1:
        jugadores = 1
    elif conteo >= 2:
        jugadores = 2
    else:
        jugadores = 1  # por defecto

    print("Jugadores:", jugadores)



    print("Juego iniciado")

    estado_inter1 = False

    def simon_dice(pin):
        global estado_inter1
        estado_inter1 = True

    inter1.irq(trigger=Pin.IRQ_FALLING, handler=simon_dice)

    estado_inter2 = False

    def parar_juego(pin):
        global estado_inter2
        estado_inter2 = True

    inter2.irq(trigger=Pin.IRQ_FALLING, handler=parar_juego)

    puntaje1 = 0
    puntaje2 = 0
    ronda = 1

    while not estado_inter2:

        print("\nRONDA", ronda)
        mem32[GPIO_OUT_REG] = 0 #apagar pines
        time.sleep(random.randint(1, 10)) # tiempo aleatorio
        estimulo = random.randint(1, 4) # estimulo aleatorio

        if estimulo == 1:
            mem32[GPIO_OUT_REG] = 0b100000000000000000000000
        elif estimulo == 2:
            mem32[GPIO_OUT_REG] = 0b10000000000000000000000
        elif estimulo == 3:
            mem32[GPIO_OUT_REG] = 0b1000000000000000000000
        else:
            mem32[GPIO_OUT_REG] = 0b10000000000000000000

        inicio = time.ticks_ms()

        tiempo1 = None
        tiempo2 = None

        while not estado_inter1 and not estado_inter2: # while del juego de reflejos
            ahora = time.ticks_ms()

            if tiempo1 is None:

                if estimulo == 1 and pul1_1.value():
                    tiempo1 = time.ticks_diff(ahora, inicio)
                elif estimulo == 2 and pul1_2.value():
                    tiempo1 = time.ticks_diff(ahora, inicio)
                elif estimulo == 3 and pul1_3.value():
                    tiempo1 = time.ticks_diff(ahora, inicio)
                elif estimulo == 4 and pul1_4.value():
                    tiempo1 = time.ticks_diff(ahora, inicio)

                elif (pul1_1.value() or pul1_2.value() or pul1_3.value() or pul1_4.value()):
                    tiempo1 = 10000

            time.sleep(0.02)

            # -------- JUGADOR 2 --------
            if jugadores == 2 and tiempo2 is None:

                if estimulo == 1 and pul2_1.value():
                    tiempo2 = time.ticks_diff(ahora, inicio)
                elif estimulo == 2 and pul2_2.value():
                    tiempo2 = time.ticks_diff(ahora, inicio)
                elif estimulo == 3 and pul2_3.value():
                    tiempo2 = time.ticks_diff(ahora, inicio)
                elif estimulo == 4 and pul2_4.value():
                    tiempo2 = time.ticks_diff(ahora, inicio)

                elif (pul2_1.value() or pul2_2.value() or pul2_3.value() or pul2_4.value()):
                    tiempo2 = 10000

            time.sleep(0.02)

            if jugadores == 1 and tiempo1 is not None:
                tiempo2 = 0
                break

            if jugadores == 2 and tiempo1 is not None and tiempo2 is not None:
                break
            
        if estado_inter1:
            mem32[GPIO_OUT_REG] = 0
            print("Ronda interrumpida")
            time.sleep(2)
        

        while estado_inter1 and not estado_inter2: # while de simon dice

            estado_inter1 = False

            leds = [
                0b10000000000000000000000,  # LED GPIO22
                0b1000000000000000000000,   # LED GPIO21
                0b10000000000000000000      # LED GPIO19
            ]

            def mostrar_secuencia(secuencia):
                for num in secuencia:
                    mem32[GPIO_OUT_REG] = leds[num]
                    time.sleep(1)
                    mem32[GPIO_OUT_REG] = 0
                    time.sleep(0.3)

            def leer_boton(tiempo_maximo=5000):
                global estado_inter2
                inicio_espera = time.ticks_ms() # Momento en que empieza a esperar
                
                while True:
                    tiempo_inicio = time.ticks_ms()
                    if pul1_2.value():
                        time.sleep(0.1)
                        return 0
                    if pul1_3.value():
                        time.sleep(0.1)
                        return 1
                    if pul1_4.value():
                        time.sleep(0.1)
                        return 2
                    if estado_inter2: 
                        time.sleep(0.1)
                        return 99
                    if time.ticks_diff(tiempo_inicio, inicio_espera) > tiempo_maximo:
                        time.sleep(0.1)
                        return 88


            secuencia = []
            ronda_sd = 1
            derrota= False

            print("\nSimon Dice iniciado")

            time.sleep(1)

            while not derrota and not estado_inter2:

                print("RONDA", ronda_sd, "DE SIMON DICE")

                time.sleep(3)

                # Agregar nuevo número aleatorio (0 a 2)
                secuencia.append(random.randint(0, 2))

                # Mostrar secuencia
                mostrar_secuencia(secuencia)

                # Leer respuesta del jugador
                for esperado in secuencia:
                    boton = leer_boton()
                    
                    if boton == 99: 
                        derrota = True
                        break

                    if boton != esperado:
                        if boton == 88:
                            print("Tiempo maximo excedido, no has presionado ningun boton o has presionado alguno no permitido")
                        else:
                            print("¡Boton incorrecto! \nPERDISTE")
                        
                        derrota = True
                        for _ in range(3): # Parpadeo de derrota
                            mem32[GPIO_OUT_REG] = leds[0] | leds[1] | leds[2]
                            time.sleep(0.2)
                            mem32[GPIO_OUT_REG] = 0
                            time.sleep(0.2)
                        break
                    else:
                        print("Correcto")

                    time.sleep(0.2)

                ronda_sd += 1

                time.sleep(1)
            
            print("Saliendo de Simon Dice | Volviendo al juego inicial")
            
            ronda -= 1
            tiempo1= 0
            tiempo2= 0

        # Apagar pines
        mem32[GPIO_OUT_REG] = 0

        #CÁLCULO DE PUNTOS
        if tiempo1: 
            puntos1 = max(0, int((10000 - tiempo1) * 0.1))
            puntos2 = max(0, int((10000 - tiempo2) * 0.1))

            puntaje1 += puntos1
            puntaje2 += puntos2

            # RESULTADOS
            tiempos=[tiempo1, tiempo2]
            puntos = [puntos1, puntos2]
            puntaje = [puntaje1, puntaje2]

            for i in range(jugadores):
                print(
                    "Tiempo J", i+1, ":", tiempos[i], "ms | puntos:", puntos[i],
                    "| Puntaje total:", puntaje [i]
                )

        time.sleep(2)

        if estado_inter2:
            print("Juego terminado ¡Gracias por participar!")
            time.sleep(1)
            print("Reiniciando sistema")
            break
        else:
            
            ronda += 1
