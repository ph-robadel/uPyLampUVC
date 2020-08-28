### Hardware Utilizado ###

- ESP8266 Wemos d1 mini
- Wemos OLED SHIELD
- LED da placa para simular a luz UVC

### Informações do software ###

- Para escolher o modo do WI-FI, deve-se a atribuir a variável ``AP_MODE`` o valor 'True' para o modo AP e 'False' para o modo Station.
- Será informado via serial qual endereço IP deverá ser acessado para se conectar ao servidor web do ESP8266. Ao digitar este endereço em qualquer navegador, a página será carregada. Desde que esteja na mesma rede WI-FI. Caso a tela OLED esteja habilitada, também será informado o endereço IP na tela OLED. 
- **Depois de informar o tempo e ligar a luz UVC na página web, mantenha a página aberta até terminar o tempo.** Caso a página seja fechada antes, a luz permanecerá acesa enquanto não houver uma nova requisição da página.