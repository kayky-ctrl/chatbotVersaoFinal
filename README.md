# 🤖 Robô - Sistema de Interação por Voz

## 📌 Visão Geral
Sistema de robô com reconhecimento de voz e interface 3D futurista, integrando:
- Processamento de linguagem natural offline
- Controle de hardware via Arduino
- Visualização web avançada com efeitos holográficos

## 🚀 Começando

### 📋 Pré-requisitos
#### Navegadores Suportados
- Google Chrome 90+
- Mozilla Firefox 88+
- Microsoft Edge 90+

#### Hardware (Opcional)
- Arduino Uno/Mega
- Microfone USB de qualidade

### 🔧 Instalação
```bash
# Baixar modelo de linguagem Vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-pt.zip
unzip vosk-model-small-pt.zip -d ./vosk-model-small-pt

# Instalar dependências Python
pip install vosk pyaudio pyttsx3 pyserial
```

## 🗂 Estrutura do Projeto
```
├── index.html # Interface visual (HTML/CSS/JS)
├── main.py # Sistema de reconhecimento de voz
└── respostas.json # Banco de diálogos e ações
```

**Descrição dos arquivos**:
- `index.html`: Interface principal com todos os efeitos visuais
- `main.py`: Script Python para processamento de voz e controle
- `respostas.json`: Configuração das interações e respostas do robô

## 🎮 Funcionalidades

### 🗣️ Comandos de Voz
```json
{
  "palavras_chave": ["voce", "brilhante", "tempo"],
  "resposta": "Posso me mexer... e falar?!",
  "acoes": ["mover_frente", "mover_tras"]
}
```

### 🕹️ Ações Suportadas

| Comando       | Descrição               |
|---------------|-------------------------|
| `abrir_porta` | Ativa servo motor       |
| `girar`       | Rotação 360°            |
| `andar_3s`    | Movimento temporizado   |

## 🌐 Interface Web

### ✨ Recursos Visuais

- **Efeitos Holográficos 3D** - Renderização avançada com perspectiva e profundidade
- **Sistema de Partículas Dinâmico** - Elementos flutuantes com física realista
- **Animações de Olho Robótico** - Movimentos pupilares e efeitos de iluminação

```css
/* Exemplo de efeito visual principal */
.robot-visor {
  box-shadow: 0 0 200px rgba(0, 198, 251, 0.8);
  background: linear-gradient(135deg, 
              rgba(0, 198, 251, 0.2), 
              rgba(0, 91, 234, 0.2));
  animation: hologram-pulse 3s infinite alternate;
}
```

## ⚠️ Solução de Problemas

### 🔍 Erros Comuns

#### 1. Modelo Vosk não encontrado
- **Solução:**  
  Verifique se:
  - A pasta `vosk-model-small-pt` está na raiz do projeto
  - O nome da pasta está exatamente como especificado
  - O arquivo `model` está presente dentro da pasta

#### 2. Problemas de Áudio
```python
# Em main.py, ajuste o dispositivo de entrada:
input_device_index=None  # Troque por índice numérico se necessário

# Para listar dispositivos disponíveis:
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))
```
## ✉️ Contato

**Desenvolvedor:** Kayky-ctrl

**Email:** [kaykyrdepaula@gmail.com](mailto:kaykyrdepaula@gmail.com)  

**Repositório:** [github.com/kayky-ctrl/chatbotVersaoFinal/](https://github.com/kayky-ctrl/chatbotVersaoFinal/)  

**Issues:** [Reportar Problema](https://github.com/kayky-ctrl/chatbotVersaoFinal/issues)  

📌 **Mantenha contato:**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/kayky-de-paula-3053a5326/)
[![Instagram](https://img.shields.io/badge/Instagram-1DA1F2?style=flat&logo=instagram)](https://www.instagram.com/ntkayky/)
