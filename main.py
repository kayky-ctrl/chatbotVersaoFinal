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
import os
import platform

# ==============================================
# Configurações
# ==============================================
parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino')
args = parser.parse_args()

BAUD_RATE = 9600
TIMEOUT = 0.5
RECONNECT_INTERVAL = 30

# ==============================================
# Sistema de Voz Ultra-Robusto
# ==============================================
class VoiceSystem:
    def __init__(self):
        self.engine = None
        self._initialize_count = 0
        self._initialize_engine()
        
    def _initialize_engine(self):
        try:
            if self.engine:
                try:
                    self.engine.stop()
                    del self.engine
                except:
                    pass

            if platform.system() == 'Windows':
                self.engine = pyttsx3.init(driverName='sapi5')
            elif platform.system() == 'Linux':
                self.engine = pyttsx3.init(driverName='espeak')
            else:
                self.engine = pyttsx3.init()

            self.engine.setProperty('rate', 150)
            voices = self.engine.getProperty('voices')
            
            for voice in voices:
                if 'portuguese' in voice.languages or 'pt' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            self._initialize_count += 1
            return True
            
        except Exception as e:
            print(f"Falha crítica ao inicializar voz (tentativa {self._initialize_count}): {str(e)}")
            return False
    
    def speak(self, text, max_retries=5):
        for attempt in range(max_retries):
            try:
                if not self.engine or self._initialize_count > 10:
                    if not self._initialize_engine():
                        time.sleep(1)
                        continue
                
                if platform.system() == 'Windows':
                    os.system('taskkill /f /im pythonw.exe 2>nul')
                
                self.engine.say(text)
                self.engine.runAndWait()
                return True
                
            except RuntimeError as e:
                print(f"Erro de runtime na fala (tentativa {attempt + 1}): {str(e)}")
                self._initialize_engine()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Erro inesperado na fala: {str(e)}")
                self._initialize_engine()
                time.sleep(1)
        
        print(f"Falha definitiva ao falar após {max_retries} tentativas")
        return False

voice_system = VoiceSystem()

# ==============================================
# Reconhecimento de Voz
# ==============================================
try:
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)

# ==============================================
# Controle do Arduino
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
# Funções Auxiliares
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
# Loop Principal
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
                arduino.process_queue()
                arduino.try_reconnect()
                
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
                            
                            # Sistema de fala aprimorado
                            if not voice_system.speak(resposta):
                                print("⚠️ A resposta não pôde ser falada, mas o sistema continua funcionando")
                            
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
