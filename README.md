# ProjetoFinal_C213

# Controle Fuzzy de Drone

Este projeto implementa um controlador fuzzy para um drone usando Python e interfaces gráficas. Ele inclui a integração de um sistema fuzzy, MQTT para comunicação e uma interface gráfica desenvolvida com Tkinter.

## Descrição

O objetivo deste projeto é controlar a altitude de um drone utilizando lógica fuzzy, ajustando a potência dos motores de acordo com a diferença da altitude desejada (setpoint) e a altitude atual. Além disso, o sistema suporta comunicação MQTT para monitorar dados do drone, como altitude e nível de bateria.

### Principais Funcionalidades

- **Controle Fuzzy de Altura**: Ajuste da altitude do drone com base em um controlador fuzzy que considera o erro e a variação do erro.
- **Interface Gráfica (GUI)**: Criação de uma GUI para controlar o drone, definir setpoints, iniciar retorno à origem (RtH) e ativar pouso de emergência.
- **Trajetória do Drone**: Visualização gráfica da trajetória do drone, exibindo a altitude ao longo do tempo.
- **Integração com MQTT**: Envio de informações da altitude e bateria do drone através de um broker MQTT.

## Tecnologias Utilizadas

- **Python 3.x**
- **Tkinter**: Para a interface gráfica.
- **Matplotlib**: Para visualização da trajetória do drone.
- **Scikit-Fuzzy**: Para implementação do controlador fuzzy.
- **Paho MQTT**: Para comunicação do drone via protocolo MQTT.
- **PIL (Pillow)**: Para manipulação de imagens na GUI.

## Requisitos

Para rodar este projeto, é necessário ter instalado:

- Python 3.x
- As seguintes bibliotecas Python:
  - `tkinter`
  - `matplotlib`
  - `Pillow`
  - `scikit-fuzzy`
  - `paho-mqtt`
  
Para instalar as bibliotecas necessárias, execute:

bash
pip install matplotlib Pillow scikit-fuzzy paho-mqtt

### Interface Gráfica

A interface gráfica foi desenvolvida utilizando a biblioteca Tkinter e permite interagir com o drone por meio de botões e entradas de texto. As funcionalidades principais são:

- **Definir o SetPoint**: O usuário pode informar a altura desejada para que o drone se mova.
- **Mover para SetPoint**: O drone ajustará sua altura com base no setpoint informado, respeitando o controle fuzzy.
- **Return to Home (RtH)**: Com um clique, o drone retorna à altitude inicial de origem.
- **Ativar Emergência**: O modo de emergência realiza um pouso imediato do drone de forma controlada.
- **Exibir Trajetória**: Abre uma janela gráfica que mostra a trajetória do drone com base em suas alterações de altitude.

  
Regras do Controle Fuzzy
- O sistema utiliza uma base de regras definidas para determinar a potência do motor:

- Se o erro for negativo e a variação do erro for negativa, a potência será alta.
- Se o erro for negativo e a variação do erro for zero, a potência será média.
- Se o erro for negativo e a variação do erro for positiva, a potência será baixa.
- Se o erro for zero, a potência será média.
- Se o erro for positivo e a variação do erro for negativa, a potência será baixa.
- Se o erro for positivo e a variação do erro for zero, a potência será média.
- Se o erro for positivo e a variação do erro for positiva, a potência será alta.
