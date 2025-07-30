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
# CONFIGURAÇÕES GLOBAIS
# ==============================================
parser = argparse.ArgumentParser(description='Sistema de Controle Robótico por Voz')
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino (ex: COM3 ou /dev/ttyACM0)')
args = parser.parse_args()

# Parâmetros ajustáveis
BAUD_RATE = 9600
SERIAL_TIMEOUT = 0.5
RECONNECT_INTERVAL = 15  # segundos
HEARTBEAT_INTERVAL = 8   # segundos
HEARTBEAT_TIMEOUT = 1.0  # segundos
HEARTBEAT_RETRIES = 3
COMMAND_DELAY = 0.15     # segundos entre comandos

# ==============================================
# SISTEMA DE VOZ
# ==============================================
class VoiceSystem:
    def __init__(self):
        self.engine = None
        self._initialize_count = 0
        self._initialize_engine()
        
    def _initialize_engine(self):
        try:
            # Limpeza prévia
            if self.engine:
                try:
                    self.engine.stop()
                    del self.engine
                except:
                    pass

            # Configuração específica por SO
            if platform.system() == 'Windows':
                self.engine = pyttsx3.init(driverName='sapi5')
            elif platform.system() == 'Linux':
                self.engine = pyttsx3.init(driverName='espeak')
            else:
                self.engine = pyttsx3.init()

            # Configurações de voz
            self.engine.setProperty('rate', 150)
            voices = self.engine.getProperty('voices')
            
            # Seleciona voz em Português
            for voice in voices:
                if 'portuguese' in voice.languages or 'pt' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            self._initialize_count += 1
            return True
            
        except Exception as e:
            print(f"Falha ao inicializar voz (tentativa {self._initialize_count}): {str(e)}")
            return False
    
    def speak(self, text, max_retries=3):
        for attempt in range(max_retries):
            try:
                # Reinicializa se necessário
                if not self.engine or self._initialize_count > 5:
                    if not self._initialize_engine():
                        time.sleep(1)
                        continue
                
                # Limpeza de processos no Windows
                if platform.system() == 'Windows':
                    os.system('taskkill /f /im pythonw.exe 2>nul')
                
                # Executa a fala
                self.engine.say(text)
                self.engine.runAndWait()
                return True
                
            except RuntimeError as e:
                print(f"Erro na fala (tentativa {attempt + 1}): {str(e)}")
                self._initialize_engine()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Erro inesperado na fala: {str(e)}")
                self._initialize_engine()
                time.sleep(1)
        
        print(f"Falha ao falar após {max_retries} tentativas")
        return False

# ==============================================
# RECONHECIMENTO DE VOZ
# ==============================================
try:
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)

# ==============================================
# CONTROLE DO ARDUINO (ROBUSTO)
# ==============================================
class ArduinoController:
    def __init__(self):
        self.arduino = None
        self.last_connection_attempt = 0
        self.last_heartbeat = 0
        self.command_queue = []
        self.lock = threading.Lock()
        self.connection_status = False
        self.heartbeat_fail_count = 0
        
    def connect(self, porta_manual=None):
        try:
            # Fecha conexão existente
            self._safe_close()
            
            # Lista portas disponíveis para debug
            print("\n[ARDUINO] Portas disponíveis:")
            ports = list_ports.comports()
            for port in ports:
                print(f" - {port.device}: {port.description}")
            
            # Conexão manual
            if porta_manual:
                print(f"\n[ARDUINO] Tentando conexão manual em {porta_manual}...")
                return self._connect_to_port(porta_manual)
            
            # Conexão automática
            print("\n[ARDUINO] Tentando conexão automática...")
            for port in ports:
                if any(key in port.description for key in ['Arduino', 'USB', 'ACM']):
                    if self._connect_to_port(port.device):
                        return True
            
            print("[ARDUINO] Nenhuma porta válida encontrada!")
            return False
            
        except Exception as e:
            print(f"[ARDUINO] Erro geral na conexão: {str(e)}")
            return False
    
    def _connect_to_port(self, port):
        """Tenta conectar a uma porta específica"""
        try:
            self.arduino = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
            time.sleep(2)  # Tempo crítico para inicialização
            
            # Sincronização e teste inicial
            if self._sync_arduino() and self._test_connection():
                print(f"[ARDUINO] Conectado com sucesso em {port}!")
                self.connection_status = True
                self.heartbeat_fail_count = 0
                return True
            
            # Falha no teste de conexão
            self._safe_close()
            print(f"[ARDUINO] Conexão em {port} falhou no teste inicial")
            return False
            
        except Exception as e:
            print(f"[ARDUINO] Falha ao conectar em {port}: {str(e)}")
            self._safe_close()
            return False
    
    def _safe_close(self):
        """Fecha a conexão serial com segurança"""
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
            self.arduino = None
        self.connection_status = False
        time.sleep(1)
    
    def _sync_arduino(self):
        """Sincroniza a comunicação com o Arduino"""
        try:
            self.arduino.reset_input_buffer()
            self.arduino.reset_output_buffer()
            self.arduino.write(b"\n")  # Pulso de sincronização
            self.arduino.flush()
            time.sleep(0.1)
            return True
        except:
            return False
    
    def _test_connection(self):
        """Testa a conexão com o Arduino"""
        for _ in range(3):  # 3 tentativas
            if self.send_heartbeat():
                return True
            time.sleep(0.5)
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
            print(f"[ARDUINO] Comando na fila: {command} (Total: {len(self.command_queue)})")
    
    def send_heartbeat(self):
        if not self.is_connected():
            return False
            
        for attempt in range(HEARTBEAT_RETRIES):
            try:
                self._sync_arduino()
                self.arduino.write("ping\n".encode())
                self.arduino.flush()
                
                start_time = time.time()
                while time.time() - start_time < HEARTBEAT_TIMEOUT:
                    if self.arduino.in_waiting:
                        response = self.arduino.readline().decode().strip()
                        if response == "pong":
                            self.heartbeat_fail_count = 0
                            return True
                
                print(f"[ARDUINO] Heartbeat sem resposta (tentativa {attempt + 1})")
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ARDUINO] Erro no heartbeat: {str(e)}")
                self._safe_close()
                time.sleep(0.1)
        
        self.heartbeat_fail_count += 1
        return False
    
    def process_queue(self):
        with self.lock:
            if not self.command_queue or not self.is_connected():
                return
            
            try:
                self._sync_arduino()
                command = self.command_queue.pop(0)
                self.arduino.write(f"{command}\n".encode())
                self.arduino.flush()
                print(f"[ARDUINO] Comando enviado: {command} (Fila: {len(self.command_queue)})")
                time.sleep(COMMAND_DELAY)
                
            except Exception as e:
                print(f"[ARDUINO] ERRO ao enviar comando: {str(e)}")
                self._safe_close()
    
    def check_connection(self):
        now = time.time()
        if now - self.last_heartbeat > HEARTBEAT_INTERVAL:
            self.last_heartbeat = now
            
            if not self.send_heartbeat():
                print("[ARDUINO] Heartbeat falhou - verificando conexão...")
                self.connection_status = False
                
                if self.heartbeat_fail_count >= 3:
                    print("[ARDUINO] Tentando reconexão...")
                    self.try_reconnect()
            else:
                self.connection_status = True
    
    def try_reconnect(self):
        now = time.time()
        if now - self.last_connection_attempt > RECONNECT_INTERVAL:
            self.last_connection_attempt = now
            self.connect(args.porta)

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================
def carregar_dialogos():
    try:
        with open("respostas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível carregar respostas.json - {str(e)}")
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
    # Inicializa sistemas
    voice_system = VoiceSystem()
    arduino = ArduinoController()
    dialogos = carregar_dialogos()

    # Configura áudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192,
        stream_callback=lambda *args: None
    )

    print("\n🔊 SISTEMA PRONTO - Diga 'desligar' para sair 🔊")
    last_status_print = time.time()

    try:
        while True:
            try:
                # Gerenciamento de conexão
                arduino.check_connection()
                arduino.process_queue()
                
                # Status periódico
                if time.time() - last_status_print > 30:
                    last_status_print = time.time()
                    status = "✅ ATIVA" if arduino.connection_status else "❌ INATIVA"
                    print(f"\n[STATUS] Conexão Arduino: {status} | Fila: {len(arduino.command_queue)}")
                
                # Processamento de voz
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:
                        fala = result['text']
                        print(f"\n🎤 Você disse: {fala}")
                        
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            voice_system.speak(resposta)
                            
                            # Processa ações
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                arduino.send_command_async(acao)
                                time.sleep(COMMAND_DELAY)
                            
                            if "desligar" in fala.lower():
                                print("🛑 Comando de desligamento recebido...")
                                break
                                
            except KeyboardInterrupt:
                print("\n🛑 Interrupção pelo teclado detectada...")
                break
            except Exception as e:
                print(f"⚠️ Erro temporário: {str(e)}")
                time.sleep(0.1)
                
    finally:
        print("\n🧹 Encerrando sistema...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        arduino._safe_close()
        print("✅ Sistema encerrado corretamente.\n")

if __name__ == "__main__":
    main()
