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
HEARTBEAT_INTERVAL = 10  # Intervalo para verificar conexão com Arduino

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
# Controle do Arduino Aprimorado
# ==============================================
class ArduinoController:
    def __init__(self):
        self.arduino = None
        self.last_connection_attempt = 0
        self.last_heartbeat = 0
        self.command_queue = []
        self.lock = threading.Lock()
        self.connection_status = False
        
    def connect(self, porta_manual=None):
        try:
            if porta_manual:
                try:
                    self.arduino = serial.Serial(porta_manual, BAUD_RATE, timeout=TIMEOUT)
                    time.sleep(2)  # Tempo maior para inicialização
                    self.connection_status = True
                    print(f"Conexão estabelecida na porta {porta_manual}")
                    return True
                except Exception as e:
                    print(f"Falha na conexão manual: {e}")
                    self.connection_status = False
            
            portas_possiveis = [
                p.device for p in list_ports.comports()
                if any(key in p.description for key in ['Arduino', 'USB', 'ACM'])
            ]
            
            for porta in portas_possiveis:
                try:
                    self.arduino = serial.Serial(porta, BAUD_RATE, timeout=TIMEOUT)
                    time.sleep(2)  # Tempo maior para inicialização
                    self.connection_status = True
                    print(f"Conexão estabelecida na porta {porta}")
                    return True
                except Exception as e:
                    print(f"Falha ao conectar na porta {porta}: {e}")
                    continue
            
            self.connection_status = False
            return False
        except Exception as e:
            print(f"Erro geral na conexão: {e}")
            self.connection_status = False
            return False
    
    def is_connected(self):
        if self.arduino is None:
            return False
        try:
            return self.arduino.is_open
        except:
            return False
    
    def send_command_async(self, command):
        with self.lock:
            self.command_queue.append(command)
            print(f"Comando adicionado à fila: {command} (Tamanho da fila: {len(self.command_queue)})")
    
    def send_heartbeat(self):
        if self.is_connected():
            try:
                self.arduino.write("ping\n".encode())
                time.sleep(0.1)
                if self.arduino.in_waiting:
                    response = self.arduino.readline().decode().strip()
                    if response == "pong":
                        return True
            except:
                pass
        return False
    
    def process_queue(self):
        with self.lock:
            if not self.command_queue:
                return
            
            if not self.is_connected():
                print("AVISO: Tentando processar fila sem conexão ativa")
                return
            
            try:
                # Limpar buffers antes de enviar comandos
                self.arduino.reset_input_buffer()
                self.arduino.reset_output_buffer()
                
                command = self.command_queue.pop(0)
                self.arduino.write(f"{command}\n".encode())
                print(f"Comando enviado: {command} (Fila restante: {len(self.command_queue)})")
                
                # Pequena pausa para garantir processamento
                time.sleep(0.1)
                
            except Exception as e:
                print(f"ERRO ao enviar comando: {e}")
                try:
                    self.arduino.close()
                except:
                    pass
                self.arduino = None
                self.connection_status = False
    
    def try_reconnect(self):
        now = time.time()
        if now - self.last_connection_attempt > RECONNECT_INTERVAL:
            self.last_connection_attempt = now
            if not self.is_connected():
                print("Tentando reconectar ao Arduino...")
                self.connect(args.porta)
    
    def check_connection(self):
        now = time.time()
        if now - self.last_heartbeat > HEARTBEAT_INTERVAL:
            self.last_heartbeat = now
            if not self.send_heartbeat():
                print("AVISO: Heartbeat falhou - possível problema na conexão")
                self.connection_status = False
                self.try_reconnect()
            else:
                self.connection_status = True

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
# Loop Principal Aprimorado
# ==============================================
def main():
    arduino = ArduinoController()
    if not arduino.connect(args.porta):
        print("AVISO: Não foi possível conectar ao Arduino inicialmente - continuando em modo sem movimentos")
    
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
    last_status_print = time.time()

    try:
        while True:
            try:
                # Verificar e processar conexão com Arduino
                arduino.check_connection()
                arduino.process_queue()
                
                # Print status periódico para debug
                if time.time() - last_status_print > 30:
                    last_status_print = time.time()
                    print(f"\n[STATUS] Conexão Arduino: {'ATIVA' if arduino.connection_status else 'INATIVA'}")
                    print(f"[STATUS] Comandos na fila: {len(arduino.command_queue)}")
                
                # Processar áudio
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:
                        fala = result['text']
                        print(f"\n👂 Você disse: {fala}")
                        
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            if not voice_system.speak(resposta):
                                print("⚠️ A resposta não pôde ser falada, mas o sistema continua funcionando")
                            
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                arduino.send_command_async(acao)
                                time.sleep(0.1)  # Pequena pausa entre comandos
                            
                            if "desligar" in fala.lower():
                                print("Recebido comando para desligar...")
                                break
                                
            except KeyboardInterrupt:
                print("\nInterrupção pelo teclado detectada...")
                break
            except Exception as e:
                print(f"⚠️ Erro temporário: {e}")
                time.sleep(0.1)
                
    finally:
        print("\n🧹 Encerrando sistema...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if arduino.is_connected():
            try:
                arduino.arduino.close()
            except:
                pass
        print("✅ Sistema encerrado corretamente.")

if __name__ == "__main__":
    main()
