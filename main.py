from vosk import Model, KaldiRecognizer
import pyaudio
import json
import pyttsx3
import os
import sys
import serial
import time

# Configuração da comunicação serial com o Arduino
try:
    arduino = serial.Serial('COM18', 9600, timeout=1)
    time.sleep(2)  # Espera a conexão ser estabelecida
except serial.SerialException as e:
    print(f"Erro ao conectar ao Arduino: {e}")
    arduino = None

# Configurações do Vosk
model_path = "vosk-model-small-pt"
if not os.path.exists(model_path):
    print(f"Erro: Modelo Vosk não encontrado em {model_path}")
    sys.exit(1)

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# Inicializa o sintetizador de voz offline
engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Carrega os diálogos
try:
    with open("respostas.json", "r", encoding="utf-8") as f:
        dialogos = json.load(f)
except Exception as e:
    print(f"Erro ao carregar diálogos: {e}")
    sys.exit(1)

def encontrar_resposta(fala):
    fala = fala.lower()
    for dialogo in dialogos:
        if any(palavra.lower() in fala for palavra in dialogo.get("palavras_chave", [])):
            return dialogo
    return None

def enviar_comando_arduino(comando):
    if arduino:
        try:
            arduino.write(f"{comando}\n".encode())
            print(f"Comando enviado: {comando}")
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")

def processar_acoes(acoes):
    if not acoes:
        return
    for acao in acoes:
        enviar_comando_arduino(acao)
        time.sleep(1)  # Intervalo entre ações

# Configuração do microfone
p = None
stream = None

try:
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8192,
                    input_device_index=None)

    print("Sistema pronto. Fale algo... (Diga 'desligar' para sair)")

    while True:
        try:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                result_dict = json.loads(result)
                
                if 'text' in result_dict and result_dict['text']:
                    fala = result_dict['text']
                    print(f"Você disse: {fala}")
                    
                    dialogo = encontrar_resposta(fala)
                    if dialogo:
                        resposta = dialogo.get("resposta", "Não entendi o que você disse...")
                        print(f"Resposta: {resposta}")
                        
                        # Executa ações antes de falar (se houver)
                        acoes = dialogo.get("acoes", [])
                        if isinstance(acoes, str):  # Para compatibilidade com versões antigas
                            acoes = [acoes]
                        processar_acoes(acoes)
                        
                        engine.say(resposta)
                        engine.runAndWait()
                        
                        if "desligar" in fala.lower():
                            engine.say("Desativando sistema")
                            engine.runAndWait()
                            break

        except IOError as e:
            if e.errno == -9981:  # Input overflowed
                print("Aviso: Overflow de entrada ignorado")
                continue
            else:
                raise

except KeyboardInterrupt:
    print("\nEncerrando pelo usuário...")
except Exception as e:
    print(f"Erro inesperado: {e}")
finally:
    print("Limpando recursos...")
    try:
        if stream:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
        if p:
            p.terminate()
        if arduino:
            arduino.close()
    except Exception as e:
        print(f"Erro ao limpar recursos: {e}")

    print("Sistema encerrado.")