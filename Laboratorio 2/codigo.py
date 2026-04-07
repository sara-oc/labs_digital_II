

from machine import Pin, ADC, PWM
import time

# PINES 
PIN_SERVO_BASE = 13
PIN_SERVO_ARM1 = 12
PIN_SERVO_ARM2 = 14

PIN_POT1 = 34
PIN_POT2 = 35

PIN_BTN_LEFT = 25
PIN_BTN_RIGHT = 26
PIN_BTN_HOME = 27
PIN_BTN_SEQ = 33

PIN_LED_GREEN = 4
PIN_LED_RED = 19
PIN_BUZZER = 18

# SERVOS
servo_base = PWM(Pin(PIN_SERVO_BASE), freq=50)
servo_arm1 = PWM(Pin(PIN_SERVO_ARM1), freq=50)
servo_arm2 = PWM(Pin(PIN_SERVO_ARM2), freq=50)

def write_servo(pwm, angle):

    # evitar valores fuera de rango
    angle = max(0, min(180, angle))

    min_duty = 30
    max_duty = 120

    duty = min_duty + (angle / 180) * (max_duty - min_duty)

    # evitar error de PWM
    duty = max(0, min(1023, int(duty)))

    pwm.duty(duty)
    
# CONVERSION ANALOGA DIGITAL
pot1 = ADC(Pin(PIN_POT1))
pot1.width(ADC.WIDTH_12BIT)

pot2 = ADC(Pin(PIN_POT2))
pot2.width(ADC.WIDTH_12BIT)

# BOTONES 
btn_left = Pin(PIN_BTN_LEFT, Pin.IN, Pin.PULL_UP)
btn_right = Pin(PIN_BTN_RIGHT, Pin.IN, Pin.PULL_UP)
btn_home = Pin(PIN_BTN_HOME, Pin.IN, Pin.PULL_UP)
btn_seq = Pin(PIN_BTN_SEQ, Pin.IN, Pin.PULL_UP)

#LED Y BUZZER
led_green = Pin(PIN_LED_GREEN, Pin.OUT)
led_red = Pin(PIN_LED_RED, Pin.OUT)
buzzer = Pin(PIN_BUZZER, Pin.OUT)

# ESTADOS
MANUAL = 0
RETURN_HOME = 1
SEQUENCE = 2

current_state = MANUAL

# POSICIONES
base_pos = 90
arm1_pos = 90
arm2_pos = 90

# CONTROL RELATIVO
deadband = 10
sinc = False
umbral = 15

# INTERRUPCIONES
last_home = 0
last_seq = 0
debounce = 200

def isr_home(pin):
    global current_state, last_home
    if time.ticks_diff(time.ticks_ms(), last_home) > debounce:
        current_state = RETURN_HOME
        last_home = time.ticks_ms()

def isr_seq(pin):
    global current_state, last_seq
    if time.ticks_diff(time.ticks_ms(), last_seq) > debounce:
        current_state = SEQUENCE
        last_seq = time.ticks_ms()

btn_home.irq(trigger=Pin.IRQ_FALLING, handler=isr_home)
btn_seq.irq(trigger=Pin.IRQ_FALLING, handler=isr_seq)

# BUZZER
last_beep = time.ticks_ms()
buzzer_state = False

def beep():
    global last_beep, buzzer_state
    if time.ticks_diff(time.ticks_ms(), last_beep) > 300:
        buzzer_state = not buzzer_state
        buzzer.value(buzzer_state)
        last_beep = time.ticks_ms()

# FUNCIONES
def pot_to_angle(adc):
    raw = adc.read()
    return raw * 180 / 4095
    
def manual_control():
    global base_pos, arm1_pos, arm2_pos,sinc

    led_green.value(1)
    led_red.value(0)

    # Base con botones
    if not btn_left.value():
        base_pos -= 1
    if not btn_right.value():
        base_pos += 1

    base_pos = max(0, min(180, base_pos))

    target1 = pot_to_angle(pot1)
    target2 = pot_to_angle(pot2)

    if sinc:
        # Calculamos que tan lejos está el pot de la posición actual del servo
        
        
        diff1 = abs(target1 - arm1_pos)
        diff2 = abs(target2 - arm2_pos)
        # Si se mueve el potenciometro cerca de la posición actual, retomamos control
        if diff1 < umbral and diff2 < umbral:
            sinc = False
            arm1_pos = target1
            arm2_pos = target2
            # Opcional: Beep corto para avisar que ya tienes el control
    else:
        # Si no estamos esperando, el movimiento es suave (Filtro Alpha)
        alpha = 0.01 # Aumenta un poco para menos lag, baja para menos vibración
        arm1_pos = arm1_pos + alpha * (target1 - arm1_pos)
        arm2_pos = arm2_pos + alpha * (target2 - arm2_pos)
        
        arm1_pos = max(0, min(180, arm1_pos))
        arm2_pos = max(0, min(180, arm2_pos))
        
def return_home():
    global base_pos, arm1_pos, arm2_pos, current_state, sinc

    led_green.value(0)
    led_red.value(1)

    while True:
        beep()
        
        # Calculamos qué tan lejos estamos de 90
        d_base = 90 - base_pos
        d_arm1 = 90 - arm1_pos
        d_arm2 = 90 - arm2_pos

        # Si TODOS estan a menos de 5 grado de diferencia, salimos del bucle
        if abs(d_base) < 5 and abs(d_arm1) < 5 and abs(d_arm2) < 5:
            # Forzamos el valor exacto al final
            base_pos, arm1_pos, arm2_pos = 90, 90, 90
            break 

        # Movimiento paso a paso
        if base_pos < 90: base_pos += 1
        elif base_pos > 90: base_pos -= 1

        if arm1_pos < 90: arm1_pos += 1
        elif arm1_pos > 90: arm1_pos -= 1

        if arm2_pos < 90: arm2_pos += 1
        elif arm2_pos > 90: arm2_pos -= 1

        # Actualizar servos físicamente
        write_servo(servo_base, base_pos)
        write_servo(servo_arm1, arm1_pos)
        write_servo(servo_arm2, arm2_pos)

        time.sleep_ms(50)

    buzzer.value(0)
    sinc = True
    time.sleep_ms(500)
    current_state = MANUAL

def run_sequence():
    global base_pos, arm1_pos, arm2_pos, current_state, sinc

    led_green.value(0)
    led_red.value(1)
    beep()

    base_pos = 90
    arm1_pos = 112
    arm2_pos = 118

    write_servo(servo_base, base_pos)
    write_servo(servo_arm1, arm1_pos)
    write_servo(servo_arm2, arm2_pos)
    time.sleep_ms(500)
    
    for i in range(3):
        beep()
        arm2_pos=90
        write_servo(servo_arm2, arm2_pos)
        time.sleep_ms(20)

        for _ in range(60):
            beep()
            arm1_pos -=1
            arm2_pos -=1
            write_servo(servo_arm1, arm1_pos)
            write_servo(servo_arm2, arm2_pos)
            time.sleep_ms(50)

        beep()
        time.sleep_ms(200)    
        arm2_pos= 65
        write_servo(servo_arm2, arm2_pos)
        time.sleep_ms(200)  
            
        for _ in range(60):
            beep()
            arm1_pos += 1
            arm2_pos +=1
            write_servo(servo_arm1, arm1_pos)
            write_servo(servo_arm2, arm2_pos)
            time.sleep_ms(50)

        for _ in range(50):
            beep()
            base_pos += 1
            write_servo(servo_base, base_pos)
            time.sleep_ms(50)
        
        beep()
        time.sleep_ms(200)
        arm2_pos= 60
        write_servo(servo_arm2, arm2_pos)
        time.sleep_ms(2000)

        beep()
        arm2_pos= 118
        write_servo(servo_arm2, arm2_pos)
        time.sleep_ms(1500)

        beep()
        base_pos = 90
        write_servo(servo_base, base_pos)
        time.sleep_ms(1000) 
        
    
    base_pos = 90
    arm1_pos = 90
    arm2_pos = 90

    write_servo(servo_base, base_pos)
    write_servo(servo_arm1, arm1_pos)
    write_servo(servo_arm2, arm2_pos)

    buzzer.value(0)
    sinc = True
    time.sleep_ms(500)
    current_state = MANUAL

# BUCLE PRINCIPAL
while True:

    if current_state == MANUAL:
        manual_control()
        
    elif current_state == RETURN_HOME:
        return_home()

    elif current_state == SEQUENCE:
        run_sequence()

    write_servo(servo_base, base_pos)
    write_servo(servo_arm1, arm1_pos)
    write_servo(servo_arm2, arm2_pos)

    time.sleep_ms(20)