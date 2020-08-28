from machine import Pin
from machine import I2C
import time
import socket
import network
import ure
import ssd1306

OLED = False  # Se a tela OLED será utilizada
PIR = False   # Se o sensor PIR será utilizado

AP_MODE = 0
STA_MODE = 1

# wifiMode = AP_MODE 
wifiMode = STA_MODE 

SSID = 'Robadel'
PWD = '09092004'

# ============ CONFIGURAÇÃO OLED ===============
if OLED: 
    i2c = I2C(scl=Pin(5), sda = Pin(4), freq = 100000)
    oled = ssd1306.SSD1306_I2C(64, 48, i2c)
    oled.fill(0)
    oled.show()

    oled_x = 64   # Dimensão da tela no eixo x
    oled_y = 48   # Dimensão da tela no eixo y
    fontSize = 8  # Tamanho do caractere em pixel

    def centerX(msg):
        if len(msg) > (oled_x / fontSize):
            return 0
        
        return int((oled_x - len(msg)*fontSize)/2)


    def oledUvcInf(isOn, tempo = 0):
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
            oled.text(adr, 0, fontSize*(posicao+1)+2)
        oled.show()
else:
    def centerX(msg):
        pass

    def oledUvcInf(isOn, tempo=0):
        pass

    def oledShowIP(ip):
        pass

# ============ CONFIGURAÇÃO WIFI ===============
if wifiMode == STA_MODE:
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(SSID, PWD)
    print("Conectando em '%s' .." % SSID, end='')
    
    while not sta.isconnected():
        time.sleep(1)
        print('.', end='')

    print('\nConectado!')
    print('listening on', sta.ifconfig()[0])
    oledShowIP(sta.ifconfig()[0])

elif wifiMode == AP_MODE:
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PWD)
    ap.active(True)
    time.sleep(2)
    print('listening on', ap.ifconfig()[0])
    oledShowIP(ap.ifconfig()[0])



# ========== CONFIGURAÇÃO LUZ UVC ==============
UVC = Pin(2, Pin.OUT)
UVC.value(1)

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
fileHtml = open('index.html','r')
html = fileHtml.read()
fileHtml.close()

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

mensagemHTML = '' # Mensagem que será mostrada na página HTML
timeFim = 0  # Tempo final para a luz UVC estar ligada
isReload = ''  # comando javascript para a página recarregar automaticamente em 1s


flagFim = True

while True:
    cl, addr = s.accept()
    isReqGet = False
    print('client connected from', addr)
    cl_file = cl.makefile('rwb', 0)

    while True:
        line = cl_file.readline()
        print(str(line))

        # Se achou a linha que contém o tempo que a luz UVC ficará ligada
        if ure.search('GET /\?Tempo=', line):
            isReqGet = True
            tempo = str(line).split(' ')[1].split('=')[1]
            
            # Se o tempo for vazio AND se a luz UVC estiver desligada
            if tempo == '' and (time.time() > timeFim):
                mensagemHTML = "O campo 'Tempo' está vazio!<br>"+\
                               "Preencha-o corretamente e tente novamente!"
                print("O campo 'Tempo' está vazio!")
            
            # Se a luz UVC estiver desligada AND se a 'página final' já foi carregada
            elif time.time() > timeFim and flagFim:
                try:
                    tempo = int(tempo)
                    timeFim = time.time() + tempo
                    flagFim = False
                except ValueError:
                    print("O tempo informado possui caracteres inválidos!")
                    mensagemHTML = "O campo 'Tempo' possui caracteres inválidos!"
        
        # Se chegou ao final da requisição
        elif not line or line == b'\r\n':
            # Se não foi encontrado movimento no sensor PIR
            if motion:
                flagFim = True
                motion = False
                isReload = ''
                
                UVC.on() # Desligar luz UVC
                oledUvcInf(False)
                mensagemHTML = 'A luz UVC foi desligada!<br>'+\
                               'Foi detectado algum movimento próximo ao equipamento'
            
            # Se o tempo ainda não se esgotou
            elif time.time() < timeFim:
                UVC.off()
                isReload = "onload=\"window.setTimeout('location.reload()', 900)\""
                mensagemHTML = '%d s' % (timeFim - time.time())
                oledUvcInf(True, timeFim - time.time())            

            # (Se o tempo da luz ligada já acabou) AND
            # (Se a 'página final' foi carregada - página sem o reload e sem mensagem) AND
            # (Se o comando send() corresponde a requsição GET)
            elif (not flagFim) and (isReqGet):
                flagFim = True
                isReload = ''
                mensagemHTML = ''
                UVC.on() # Desligar luz UVC
                oledUvcInf(False)

            else:
                UVC.on() # Desligar luz UVC
                oledUvcInf(False)
            
            #Enviar a página html
            cl.send(html % (isReload, mensagemHTML))
            mensagemHTML = ''
            break
        
    cl.close()
    print()