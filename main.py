from vosk import Model, KaldiRecognizer
import pyaudio
import json
import pyttsx3
import serial
import time
from serial.tools import list_ports
import sys
import argparse

# ==============================================
# CONFIGURAÇÕES PRINCIPAIS
# ==============================================

parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=str, help='Porta serial manual para o Arduino (ex: COM3 ou /dev/ttyUSB0)')
args = parser.parse_args()

# Configurações do Arduino
BAUD_RATE = 9600
TIMEOUT = 1
RECONNECT_INTERVAL = 30  # segundos entre tentativas de reconexão

try:
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz.\nErro: {e}")
    sys.exit(1)

engine = pyttsx3.init()
engine.setProperty('rate', 150)

# ==============================================
# FUNÇÕES AUXILIARES - ARDUINO
# ==============================================

def listar_portas_disponiveis():
    """Lista todas as portas seriais disponíveis com detalhes"""
    portas = list_ports.comports()
    print("\nPortas seriais disponíveis:")
    for porta in portas:
        print(f" - {porta.device}: {porta.description} | {porta.hwid}")
    return portas

def conectar_arduino(porta_manual=None):
    """Tenta conectar ao Arduino com tratamento robusto de erros"""
    try:
        if porta_manual:
            print(f"\nTentando conectar na porta manual: {porta_manual}")
            try:
                arduino = serial.Serial(porta_manual, BAUD_RATE, timeout=TIMEOUT)
                time.sleep(2)  # Tempo crítico para inicialização
                print(f"✅ Conexão estabelecida na porta {porta_manual}")
                return arduino
            except Exception as e:
                print(f"⚠️ Falha na conexão manual: {e}")
                listar_portas_disponiveis()

        # Autodetecção
        print("\nTentando autodetectar Arduino...")
        portas_possiveis = [
            p.device for p in list_ports.comports()
            if ('Arduino' in p.description or 
                'USB Serial Device' in p.description or
                'USB' in p.description or
                'ACM' in p.device)
        ]

        if not portas_possiveis:
            print("⚠️ Nenhuma porta compatível encontrada.")
            listar_portas_disponiveis()
            return None

        for porta in portas_possiveis:
            try:
                print(f"Tentando conectar em {porta}...")
                arduino = serial.Serial(porta, BAUD_RATE, timeout=TIMEOUT)
                time.sleep(2)
                print(f"✅ Arduino conectado em {porta}")
                return arduino
            except Exception as e:
                print(f"⚠️ Falha ao conectar em {porta}: {str(e)[:100]}")

        print("⚠️ Não foi possível conectar em nenhuma porta.")
        return None

    except Exception as e:
        print(f"⚠️ Erro inesperado na conexão: {e}")
        return None

def verificar_conexao_arduino(arduino):
    """Verifica se a conexão com o Arduino está ativa"""
    if arduino is None:
        return False
    try:
        return arduino.is_open
    except:
        return False

def enviar_comando_arduino(arduino, comando, tentar_reconectar=True):
    """Envia comando para Arduino com tratamento de erros"""
    if not verificar_conexao_arduino(arduino):
        if tentar_reconectar:
            print("⏳ Conexão perdida, tentando reconectar...")
            return None, conectar_arduino(args.porta)
        return None, arduino

    try:
        arduino.write(f"{comando}\n".encode())
        print(f"➡️ Comando enviado: {comando}")
        return True, arduino
    except Exception as e:
        print(f"⚠️ Erro ao enviar comando: {e}")
        try:
            arduino.close()
        except:
            pass
        if tentar_reconectar:
            return None, conectar_arduino(args.porta)
        return None, None

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
    arduino = conectar_arduino(args.porta)
    ultima_tentativa_conexao = time.time()
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
                            
                            engine.say(resposta)
                            engine.runAndWait()
                            
                            # Tentar reconectar periodicamente
                            agora = time.time()
                            if (not verificar_conexao_arduino(arduino) and 
                                (agora - ultima_tentativa_conexao > RECONNECT_INTERVAL)):
                                print("⏳ Tentando reconexão periódica...")
                                arduino = conectar_arduino(args.porta)
                                ultima_tentativa_conexao = agora
                            
                            # Enviar comandos para Arduino
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                sucesso, arduino = enviar_comando_arduino(arduino, acao)
                                if sucesso:
                                    time.sleep(0.1)
                            
                            if "desligar" in fala.lower():
                                break
                                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Erro temporário: {e}")
                time.sleep(1)
                
    finally:
        print("\n🧹 Encerrando...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if verificar_conexao_arduino(arduino):
            arduino.close()
        print("✅ Sistema encerrado.")

if __name__ == "__main__":
    main()
