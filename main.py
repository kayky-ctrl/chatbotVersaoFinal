# =================================================
# 1. Importações
# =================================================
from vosk import Model, KaldiRecognizer  # Reconhecimento de voz offline
import pyaudio  # Captura de áudio do microfone
import json  # Processamento de arquivos JSON
import pyttsx3  # Síntese de voz
import serial  # Comunicação com Arduino
import time  # Controle de tempo/delays
from serial.tools import list_ports  # Listar portas seriais disponíveis
import sys  # Sistema (para sair em caso de erro)
import argparse  # Argumentos de linha de comando
import threading  # Processamento assíncrono

# ==============================================
# 2. CONFIGURAÇÕES PRINCIPAIS
# ==============================================
parser = argparse.ArgumentParser()  # Cria parser de argumentos
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino')  # Argumento para porta manual
args = parser.parse_args()  # Processa argumentos

# Configurações da comunicação serial
BAUD_RATE = 9600  # Velocidade de comunicação
TIMEOUT = 0.5 # Timeout curto para não bloquear
RECONNECT_INTERVAL = 30  # Intervalo entre tentativas de reconexão (segundos)

# ==============================================
# 3. Inicialização do Sistema de Voz
# ==============================================
try:
    model = Model("vosk-model-small-pt")  # Carrega modelo em português
    recognizer = KaldiRecognizer(model, 16000)  # Configura reconhecedor (16kHz)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)  # Sai se falhar

engine = pyttsx3.init()  # Inicializa sintetizador de voz
engine.setProperty('rate', 150)  # Velocidade da fala (150 palavras/min)

# ==============================================
# 4. Classe ArduinoController
# ==============================================

class ArduinoController:
    def __init__(self):
        self.arduino = None  # Conexão serial
        self.last_connection_attempt = 0  # Última tentativa de conexão
        self.command_queue = []  # Fila de comandos
        self.lock = threading.Lock()  # Trava para thread-safe
        
    def connect(self, porta_manual=None):
        """Tenta conectar ao Arduino"""
        try:
            if porta_manual:  # Tenta conexão manual primeiro
                try:
                    self.arduino = serial.Serial(porta_manual, BAUD_RATE, timeout=TIMEOUT)
                    time.sleep(1)  # Espera inicialização
                    return True
                except Exception as e:
                    print(f"Falha na conexão manual: {e}")
            
            # Autodetecção de portas
            portas_possiveis = [
                p.device for p in list_ports.comports()
                if any(key in p.description for key in ['Arduino', 'USB', 'ACM'])
            ]
            
            for porta in portas_possiveis:  # Tenta cada porta
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
        """Verifica se está conectado"""
        return self.arduino is not None and self.arduino.is_open
    
    def send_command_async(self, command):
        """Adiciona comando à fila (thread-safe)"""
        with self.lock:  # Bloqueia acesso concorrente
            self.command_queue.append(command)
    
    def process_queue(self):
        """Processa fila de comandos"""
        with self.lock:
            print(f"[DEBUG] Fila atual: {len(self.command_queue)} comandos")  # Debug
            if not self.command_queue or not self.is_connected():
                return
            
            try:
                command = self.command_queue.pop(0)  # Pega primeiro comando
                self.arduino.write(f"{command}\n".encode())  # Envia
                print(f"Comando enviado: {command}")
            except Exception as e:
                print(f"Erro ao enviar comando: {e}")
                try:
                    self.arduino.close()  # Tenta fechar conexão
                except:
                    pass
                self.arduino = None  # Reseta conexão
    
    def try_reconnect(self):
        """Tenta reconectar periodicamente"""
        now = time.time()
        if now - self.last_connection_attempt > RECONNECT_INTERVAL:
            self.last_connection_attempt = now
            if not self.is_connected():
                print("Tentando reconectar...")
                self.connect(args.porta)


# ==============================================
# 5. FUNÇÕES PRINCIPAIS
# ==============================================

def falar_async(texto):
        def falar():
            engine.say(texto)
            engine.runAndWait()
        threading.Thread(target=falar).start()

def carregar_dialogos():
    """Carrega diálogos do arquivo JSON"""
    try:
        with open("respostas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        sys.exit(1)

def encontrar_resposta(fala, dialogos):
    """Encontra resposta baseada em palavras-chave"""
    fala = fala.lower()  # Padroniza para minúsculas
    for dialogo in dialogos:
        if any(palavra.lower() in fala for palavra in dialogo.get("palavras_chave", [])):
            return dialogo
    return None  # Nenhuma correspondência

# ==============================================
# 6. LOOP PRINCIPAL
# ==============================================

def main():
    arduino = ArduinoController()  # Cria controlador
    arduino.connect(args.porta)  # Tenta conectar
    dialogos = carregar_dialogos()  # Carrega diálogos

    # Configura captura de áudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,  # Formato 16-bit
        channels=1,  # Mono
        rate=16000,  # Taxa de amostragem
        input=True,  # Modo entrada
        frames_per_buffer=8192  # Tamanho do buffer
    )

    print("\n🎭 SISTEMA PRONTO - Diga 'desligar' para sair 🎭")

    try:
        while True:  # Loop infinito
            try:
                arduino.process_queue()  # Processa comandos pendentes
                arduino.try_reconnect()  # Tenta reconectar se necessário
                
                # Captura áudio
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):  # Se reconheceu fala
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:  # Se tem texto válido
                        fala = result['text']
                        print(f"👂 Você disse: {fala}")
                        
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            # PRIORIDADE PARA A VOZ
                            falar_async(resposta)  # Fala resposta
                            
                            # Envia ações para Arduino
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):  # Converte para lista se necessário
                                acoes = [acoes]
                                
                            for acao in acoes:  # Enfileira comandos
                                arduino.send_command_async(acao)
                            
                            if "desligar" in fala.lower():  # Comando de saída
                                break
                                
            except KeyboardInterrupt:  # Ctrl+C
                break
            except Exception as e:  # Outros erros
                print(f"⚠️ Erro temporário: {e}")
                time.sleep(0.1)  # Previne loop de erro
                
    finally:  # Executa sempre ao sair
        print("\n🧹 Encerrando...")
        stream.stop_stream()  # Para captura de áudio
        stream.close()
        p.terminate()
        if arduino.is_connected():  # Fecha conexão serial
            arduino.arduino.close()
        print("✅ Sistema encerrado.")

if __name__ == "__main__":
    main()  # Ponto de entrada
