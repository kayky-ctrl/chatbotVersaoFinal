# ==============================================
# IMPORTAÇÕES
# ==============================================
from vosk import Model, KaldiRecognizer  # Reconhecimento de voz offline
import pyaudio  # Captura de áudio do microfone
import json  # Manipulação de arquivos JSON
import pyttsx3  # Síntese de voz (TTS)
import serial  # Comunicação serial com Arduino
import time  # Controle de tempo e delays
from serial.tools import list_ports  # Listar portas seriais disponíveis
import sys  # Sistema e saída de erros
import argparse  # Parsing de argumentos de linha de comando
import threading  # Processamento assíncrono
import os  # Operações do sistema
import platform  # Identificação do sistema operacional

# ==============================================
# CONFIGURAÇÕES GLOBAIS
# ==============================================
# Configuração do parser de argumentos de linha de comando
parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino')
args = parser.parse_args()

# Constantes de configuração
BAUD_RATE = 9600  # Velocidade de comunicação serial
TIMEOUT = 0.5  # Timeout para comunicação serial
RECONNECT_INTERVAL = 30  # Intervalo para tentar reconexão (segundos)
HEARTBEAT_INTERVAL = 10  # Intervalo para verificar conexão com Arduino

# ==============================================
# SISTEMA DE VOZ (TTS - TEXT TO SPEECH)
# ==============================================
class VoiceSystem:
    def __init__(self):
        self.engine = None  # Motor de síntese de voz
        self._initialize_count = 0  # Contador de tentativas de inicialização
        self._initialize_engine()  # Inicializa o motor na criação
        
    def _initialize_engine(self):
        """Inicializa o motor de síntese de voz com configurações específicas por plataforma"""
        try:
            # Limpeza segura do motor existente
            if self.engine:
                try:
                    self.engine.stop()
                    del self.engine
                except:
                    pass

            # Configuração específica por sistema operacional
            if platform.system() == 'Windows':
                self.engine = pyttsx3.init(driverName='sapi5')  # Usa SAPI5 no Windows
            elif platform.system() == 'Linux':
                self.engine = pyttsx3.init(driverName='espeak')  # Usa eSpeak no Linux
            else:
                self.engine = pyttsx3.init()  # Configuração padrão para outros sistemas

            # Configurações de voz
            self.engine.setProperty('rate', 150)  # Velocidade da fala
            voices = self.engine.getProperty('voices')
            
            # Seleciona voz em português se disponível
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
        """Sintetiza o texto em fala com múltiplas tentativas e tratamento de erros"""
        for attempt in range(max_retries):
            try:
                # Reinicializa se necessário
                if not self.engine or self._initialize_count > 10:
                    if not self._initialize_engine():
                        time.sleep(1)
                        continue
                
                # Limpeza de processos no Windows
                if platform.system() == 'Windows':
                    os.system('taskkill /f /im pythonw.exe 2>nul')
                
                # Sintetiza e reproduz a fala
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

# Instância global do sistema de voz
voice_system = VoiceSystem()

# ==============================================
# RECONHECIMENTO DE VOZ (STT - SPEECH TO TEXT)
# ==============================================
try:
    # Carrega o modelo de reconhecimento de voz em português
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)  # Configura para taxa de amostragem de 16kHz
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)  # Encerra o programa se não carregar o modelo

# ==============================================
# CONTROLE DO ARDUINO (COMUNICAÇÃO SERIAL)
# ==============================================
class ArduinoController:
    def __init__(self):
        self.arduino = None  # Objeto de conexão serial
        self.last_connection_attempt = 0  # Última tentativa de conexão
        self.last_heartbeat = 0  # Último heartbeat
        self.command_queue = []  # Fila de comandos pendentes
        self.lock = threading.Lock()  # Lock para thread-safe
        self.connection_status = False  # Status atual da conexão
        
    def connect(self, porta_manual=None):
        """Tenta conectar ao Arduino, priorizando porta manual se fornecida"""
        try:
            # Tentativa de conexão manual
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
            
            # Busca automática por portas possíveis
            portas_possiveis = [
                p.device for p in list_ports.comports()
                if any(key in p.description for key in ['Arduino', 'USB', 'ACM'])
            ]
            
            # Tenta conectar em cada porta disponível
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
        """Verifica se a conexão está ativa"""
        if self.arduino is None:
            return False
        try:
            return self.arduino.is_open
        except:
            return False
    
    def send_command_async(self, command):
        """Adiciona comando à fila de processamento (thread-safe)"""
        with self.lock:
            self.command_queue.append(command)
            print(f"Comando adicionado à fila: {command} (Tamanho da fila: {len(self.command_queue)})")
    
    def send_heartbeat(self):
        """Envia sinal de vida para verificar conexão"""
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
        """Processa o próximo comando na fila (thread-safe)"""
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
                
                # Remove e envia o próximo comando
                command = self.command_queue.pop(0)
                self.arduino.write(f"{command}\n".encode())
                print(f"Comando enviado: {command} (Fila restante: {len(self.command_queue)})")
                
                time.sleep(0.1)  # Pequena pausa para garantir processamento
                
            except Exception as e:
                print(f"ERRO ao enviar comando: {e}")
                try:
                    self.arduino.close()
                except:
                    pass
                self.arduino = None
                self.connection_status = False
    
    def try_reconnect(self):
        """Tenta reconectar após intervalo configurado"""
        now = time.time()
        if now - self.last_connection_attempt > RECONNECT_INTERVAL:
            self.last_connection_attempt = now
            if not self.is_connected():
                print("Tentando reconectar ao Arduino...")
                self.connect(args.porta)
    
    def check_connection(self):
        """Verifica a conexão periodicamente com heartbeat"""
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
# FUNÇÕES AUXILIARES
# ==============================================
def carregar_dialogos():
    """Carrega os diálogos e respostas do arquivo JSON"""
    try:
        with open("respostas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        sys.exit(1)

def encontrar_resposta(fala, dialogos):
    """Encontra a resposta adequada para o texto reconhecido"""
    fala = fala.lower()
    for dialogo in dialogos:
        if any(palavra.lower() in fala for palavra in dialogo.get("palavras_chave", [])):
            return dialogo
    return None

# ==============================================
# LOOP PRINCIPAL
# ==============================================
def main():
    # Inicializa controlador do Arduino
    arduino = ArduinoController()
    if not arduino.connect(args.porta):
        print("AVISO: Não foi possível conectar ao Arduino inicialmente - continuando em modo sem movimentos")
    
    # Carrega diálogos
    dialogos = carregar_dialogos()

    # Configura captura de áudio
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
                
                # Reconhece fala
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:
                        fala = result['text']
                        print(f"\n👂 Você disse: {fala}")
                        
                        # Encontra resposta adequada
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            # Sintetiza resposta em voz
                            if not voice_system.speak(resposta):
                                print("⚠️ A resposta não pôde ser falada, mas o sistema continua funcionando")
                            
                            # Processa ações associadas
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                arduino.send_command_async(acao)
                                time.sleep(0.1)  # Pequena pausa entre comandos
                            
                            # Comando especial para desligar
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
        # Rotina de encerramento
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

# Ponto de entrada do programa
if __name__ == "__main__":
    main()
