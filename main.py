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

# Configuração de argumentos de linha de comando
parser = argparse.ArgumentParser()
parser.add_argument('--porta', type=str, help='COM9')
args = parser.parse_args()

# 1. Carrega o modelo de voz offline
try:
    model = Model("vosk-model-small-pt")
    recognizer = KaldiRecognizer(model, 16000)
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo de voz. Verifique se a pasta 'vosk-model-small-pt' existe.\nErro: {e}")
    sys.exit(1)

# 2. Inicializa o sintetizador de voz offline
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Velocidade da fala

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================

def conectar_arduino(porta_manual=None):
    """Tenta conectar ao Arduino de forma não-bloqueante"""
    try:
        if porta_manual:
            # Tenta conectar na porta manual especificada
            try:
                arduino = serial.Serial(porta_manual, 9600, timeout=1)
                time.sleep(2)  # Tempo para inicialização
                print(f"✅ Arduino conectado na porta manual {porta_manual}")
                return arduino
            except Exception as e:
                print(f"⚠️ Falha ao conectar na porta manual {porta_manual}. Tentando autodetecção...")
        
        # Lista portas COM onde o Arduino pode estar (autodetecção)
        portas_possiveis = [
            p.device for p in list_ports.comports() 
            if 'Arduino' in p.description or 'USB Serial Device' in p.description
        ]
        
        if portas_possiveis:
            arduino = serial.Serial(portas_possiveis[0], 9600, timeout=1)
            time.sleep(2)  # Tempo para inicialização
            print(f"✅ Arduino conectado na porta autodetecção {portas_possiveis[0]}")
            return arduino
        
        print("⚠️ Arduino não encontrado. Continuando sem controle de movimentos...")
        return None
            
    except Exception as e:
        print(f"⚠️ Falha ao conectar ao Arduino. Continuando sem controle de movimentos...\nErro: {e}")
        return None

def enviar_comando_se_possivel(arduino, comando, ultima_tentativa_conexao=0):
    """Envia comandos apenas se o Arduino estiver conectado"""
    agora = time.time()
    
    # Tenta reconectar a cada 30 segundos se não estiver conectado
    if (not arduino or not arduino.is_open) and (agora - ultima_tentativa_conexao > 30):
        print("⏳ Tentando reconectar ao Arduino...")
        novo_arduino = conectar_arduino(args.porta)
        ultima_tentativa_conexao = agora
        if novo_arduino:
            arduino = novo_arduino
    
    if arduino and arduino.is_open:
        try:
            arduino.write(f"{comando}\n".encode())
            print(f"➡️ Enviado para Arduino: {comando}")
        except Exception as e:
            print(f"⚠️ Falha ao enviar comando para Arduino. Erro: {e}")
            try:
                arduino.close()
            except:
                pass
            arduino = None
    
    return arduino, ultima_tentativa_conexao

def carregar_dialogos():
    """Carrega o arquivo de diálogos"""
    try:
        with open("respostas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível carregar os diálogos.\nErro: {e}")
        sys.exit(1)

def encontrar_resposta(fala, dialogos):
    """Encontra a resposta apropriada baseada nas palavras-chave"""
    fala = fala.lower()
    for dialogo in dialogos:
        if any(palavra.lower() in fala for palavra in dialogo.get("palavras_chave", [])):
            return dialogo
    return None

# ==============================================
# LOOP PRINCIPAL
# ==============================================

def main():
    # 1. Conecta ao Arduino (se disponível)
    arduino = conectar_arduino(args.porta)
    ultima_tentativa_conexao = 0
    
    # 2. Carrega diálogos
    dialogos = carregar_dialogos()
    
    # 3. Configura o microfone
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192
    )
    
    print("\n🎭 SISTEMA PRONTO PARA O TEATRO 🎭")
    print("Diga 'desligar' para encerrar.\n")
    
    try:
        while True:
            try:
                # 4. Captura áudio
                data = stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'text' in result and result['text']:
                        fala = result['text']
                        print(f"👂 Você disse: {fala}")
                        
                        # 5. Encontra a resposta
                        dialogo = encontrar_resposta(fala, dialogos)
                        if dialogo:
                            resposta = dialogo.get("resposta", "Não entendi o que você disse...")
                            print(f"🤖 Resposta: {resposta}")
                            
                            # 6. Fala a resposta (SEMPRE executa, mesmo sem Arduino)
                            engine.say(resposta)
                            engine.runAndWait()
                            
                            # 7. Envia ações para Arduino (se estiver conectado)
                            acoes = dialogo.get("acoes", [])
                            if isinstance(acoes, str):
                                acoes = [acoes]
                                
                            for acao in acoes:
                                arduino, ultima_tentativa_conexao = enviar_comando_se_possivel(
                                    arduino, 
                                    acao,
                                    ultima_tentativa_conexao
                                )
                                time.sleep(0.1)  # Pequena pausa entre comandos
                            
                            # 8. Verifica comando de desligamento
                            if "desligar" in fala.lower():
                                engine.say("Desativando sistema")
                                engine.runAndWait()
                                break
                                
            except KeyboardInterrupt:
                print("\n👋 Encerrando pelo usuário...")
                break
            except Exception as e:
                print(f"⚠️ Erro temporário: {e}")
                time.sleep(1)  # Prevenção contra loops rápidos de erro
                
    finally:
        # 9. Encerra recursos
        print("\n🧹 Limpando recursos...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if arduino and arduino.is_open:
            arduino.close()
        print("✅ Sistema encerrado com segurança.")

if __name__ == "__main__":
    main()
