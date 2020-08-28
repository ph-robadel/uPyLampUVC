from time import sleep
from time import time
from machine import Pin
import network

import picoweb

OLED = False  # Se a tela OLED será utilizada
PIR = True   # Se o sensor PIR será utilizado

AP_MODE = False  # 'True' para modo AP; 'False' para modo Station
SSID = ''
PWD = ''

# ============ Inicialização do LED UV ============
led = Pin(2, Pin.OUT)
led.on()

# ============ CONFIGURAÇÃO OLED ===============
if OLED:
    from machine import I2C
    from ssd1306 import SSD1306_I2C

    i2c = I2C(scl=Pin(5), sda = Pin(4), freq = 100000)
    oled = SSD1306_I2C(64, 48, i2c)
    oled.fill(0)
    oled.show()

    oled_x = 64   # Dimensão da tela no eixo x
    oled_y = 48   # Dimensão da tela no eixo y
    fontSize = 8  # Tamanho do caractere em pixel

    def centerX(msg):
        if len(msg) > (oled_x / fontSize):
            return 0
        
        return int((oled_x - len(msg)*fontSize)/2)


    def oledUvcInf(isOn, tempo=0):
        if isOn:  # Se a luz UVC está ligada
            oled.fill(1)
            oled.text("Luz UVC", centerX("Luz UVC"), 4, 0)
            oled.text("Acesa", centerX("Acesa"), 16, 0)
            oled.text("%ds" % tempo, centerX("%ds" % tempo), 30, 0)
            oled.show()
        else:
            oled.fill(0)
            oled.text("Luz UVC", centerX("Luz UVC"), 4)
            oled.text("Apagada", centerX("Apagada"), 16)
            oled.show()

    def oledShowIP(ip):
        # Imprimindo endereço IP na tela OLED
        oled.text("IP", centerX("IP"), 1)
        for posicao, adr in enumerate(ip.split('.')):
            oled.text(adr, 0, fontSize * (posicao+1) + 2)
        oled.show()
else:

    def oledUvcInf(isOn, tempo=0):
        pass

    def oledShowIP(ip):
        pass

# ============ CONFIGURAÇÃO WIFI ===============
if AP_MODE:
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PWD)
    ap.active(True)
    time.sleep(2)
    print('listening on', ap.ifconfig()[0])
    oledShowIP(ap.ifconfig()[0])

else:
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(SSID, PWD)
    print("Conectando em '%s' .." % SSID, end='')
    
    while not sta.isconnected():
        sleep(1)
        print('.', end='')

    print('\nConectado!')
    print('Conecte-se em http://{}'.format(sta.ifconfig()[0]))
    oledShowIP(sta.ifconfig()[0])


# ========= CONFIGURAÇÃO SENSOR PIR ============
motion = False

if PIR:
    def handle_interrupt(pin):
        global motion
        motion = True
        global interrupt_pin
        interrupt_pin = pin
    
    pir = Pin(14, Pin.IN)
    pir.irq(trigger=Pin.IRQ_RISING, handler=handle_interrupt)


# ============ CONFIGURAÇÃO WEB SERVER ===============
app = picoweb.WebApp(__name__)
tempo_fim = 0
fim = True


@app.route("/")
def index(req, resp):
    global motion
    if motion:
        led.on()
        print('Sensor PIR detectou movimentos próximos a luz UV')
        oledUvcInf(False)
        yield from picoweb.start_response(resp)
        yield from resp.awrite('Sensor PIR detectou movimentos próximos a luz UV')
    
    else:
        global tempo_fim
        global fim

        html = '404 - Page not foud'
        onload = "onload=\"window.setTimeout('location.reload()', 800)\";"

        yield from picoweb.start_response(resp)

        try:
            with open('index.html', 'r') as arquivo:
                html = arquivo.read().replace('\n','').replace('    ','')
        except:
            yield from resp.awrite('404 - Page not foud')
            return
            print("Página não encontrada")

        if tempo_fim <= time() and fim:
            try:
                req.parse_qs()
                tempo_fim = time() + int(req.form["tempo"])
                yield from resp.awrite(html % (onload, str(tempo_fim - time())+'s'))
                led.off()
                fim = False
                oledUvcInf(True, tempo_fim - time())
            except ValueError:
                yield from resp.awrite(html % ("", "O campo 'Tempo' possui caracteres inválidos"))
            except:
                yield from resp.awrite(html % ('', ''))
        elif (tempo_fim <= time()):
            fim = True
            led.on()
            oledUvcInf(False)
            yield from resp.awrite(html % ("", ""))
        else:
            oledUvcInf(True, tempo_fim - time())
            yield from resp.awrite(html % (onload, str(tempo_fim - time())+'s'))
try:
    app.run(debug=-1)
except:
    led.on()