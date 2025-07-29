from vosk import Model, KaldiRecognizer
import pyaudio
import json
import pyttsx3
import serial
import time
from serial.tools import list_ports
import sys
import argparse
import threading

# ==============================================
# CONFIGURAÇÕES PRINCIPAIS
# ==============================================

parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino (ex: COM3 ou /dev/ttyUSB0)')
args = parser.parse_args()

# Configurações do Arduino
BAUD_RATE = 9600
TIMEOUT = 0.1  # Reduzido para não bloquear
RECONNECT_INTERVAL = 30

try:
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)

# Inicializa o engine de voz em modo thread-safe
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# ==============================================
# FUNÇÕES AUXILIARES - ARDUINO (NÃO-BLOQUEANTES)
# ==============================================

class ArduinoController:
    def __init__(self):
        self.arduino = None
        self.last_connection_attempt = 0
        self.command_queue = []
        self.lock = threading.Lock()
        
    def connect(self, porta_manual=None):
        try:
            if porta_manual:
                try:
                    self.arduino = serial.Serial(porta_manual, BAUD_RATE, timeout=TIMEOUT)
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"Falha na conexão manual: {e}")
            
            portas_possiveis = [
                p.device for p in list_ports.comports()
                if any(key in p.description for key in ['Arduino', 'USB', 'ACM'])
            ]
            
            for porta in portas_possiveis:
                try:
                    self.arduino = serial.Serial(porta, BAUD_RATE, timeout=TIMEOUT)
                    time.sleep(1)
                    return True
                except:
                    continue
            return False
        except:
            return False
    
    def is_connected(self):
        return self.arduino is not None and self.arduino.is_open
    
    def send_command_async(self, command):
        with self.lock:
            self.command_queue.append(command)
    
    def process_queue(self):
        with self.lock:
            if not self.command_queue or not self.is_connected():
                return
            
            try:
                command = self.command_queue.pop(0)
                self.arduino.write(f"{command}\n".encode())
                print(f"Comando enviado: {command}")
            except Exception as e:
                print(f"Erro ao enviar comando: {e}")
                try:
                    self.arduino.close()
                except:
                    pass
                self.arduino = None
    
    def try_reconnect(self):
        now = time.time()
        if now - self.last_connection_attempt > RECONNECT_INTERVAL:
            self.last_connection_attempt = now
            if not self.is_connected():
                print("Tentando reconectar...")
                self.connect(args.porta)

# ==============================================
# FUNÇÕES PRINCIPAIS
# ==============================================

def carregar_dialogos():
    try:
        with open("respostas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        sys.exit(1)

def encontrar_resposta(fala, dialogos):
    fala = fala.lower()
    for dialogo in dialogos:
        if any(palavra.lower() in fala for palavra in dialogo.get("palavras_chave", [])):
            return dialogo
    return None

# ==============================================
# LOOP PRINCIPAL
# ==============================================

def main():
    arduino = ArduinoController()
    arduino.connect(args.porta)
    dialogos = carregar_dialogos()

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192
    )

    print("\n🎭 SISTEMA PRONTO - Diga 'desligar' para sair 🎭")

    try:
        while True:
            try:
                # Processa a fila de comandos do Arduino
                arduino.process_queue()
                
                # Tenta reconectar periodicamente
                arduino.try_reconnect()
                
                # Captura áudio
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:
                        fala = result['text']
                        print(f"👂 Você disse: {fala}")
                        
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            # PRIORIDADE PARA A VOZ
                            engine.say(resposta)
                            engine.runAndWait()
                            
                            # Envia comandos para Arduino (assincronamente)
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                arduino.send_command_async(acao)
                            
                            if "desligar" in fala.lower():
                                break
                                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Erro temporário: {e}")
                time.sleep(0.1)
                
    finally:
        print("\n🧹 Encerrando...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if arduino.is_connected():
            arduino.arduino.close()
        print("✅ Sistema encerrado.")

if __name__ == "__main__":
    main()
