
# 🤖 Robô com Comando de Voz

Sistema interativo com reconhecimento de voz offline, integração com Arduino e interface 3D futurista em ambiente web.

---

## 📌 Visão Geral

Este projeto une **hardware e software** para criar um robô interativo capaz de:

- 🎙️ **Entender comandos de voz (offline)**
- 🧠 **Responder com fala sintetizada**
- 🔌 **Controlar motores via Arduino**
- 🌐 **Exibir interface web com visual holográfico e olhos animados**

---

## 🗂️ Estrutura do Projeto

```
├── index.html               # Interface web com efeitos 3D
├── main.py                 # Sistema principal: STT, TTS e controle serial
├── respostas.json          # Banco de diálogos e ações
├── CodigoPrincipalMotores.ino # Código para Arduino (controle de motores)
└── vosk-model-small-pt/    # Modelo de reconhecimento de voz (Vosk)
```

### 📁 Descrição dos Arquivos

| Arquivo                        | Função Principal                                       |
|-------------------------------|--------------------------------------------------------|
| `index.html`                  | Interface visual 3D e efeitos holográficos             |
| `main.py`                     | Captura voz, executa ações, responde em voz           |
| `respostas.json`              | Define palavras-chave, respostas e ações              |
| `CodigoPrincipalMotores.ino` | Código Arduino para receber comandos serial e agir     |
| `vosk-model-small-pt/`        | Modelo Vosk para reconhecimento offline em português   |

---

## 🚀 Como Começar

### 📋 Pré-requisitos

- Python 3.7+
- Microfone funcional
- Navegador moderno (para `index.html`)
- (Opcional) Arduino Uno/Mega com motores e sensores

### 💻 Instalação

```bash
# 1. Baixar e extrair o modelo de voz em português
wget https://alphacephei.com/vosk/models/vosk-model-small-pt.zip
unzip vosk-model-small-pt.zip -d ./vosk-model-small-pt

# 2. Instalar dependências
pip install vosk pyaudio pyttsx3 pyserial
```

---

## 🧠 Como Funciona

1. Você fala algo próximo ao microfone.
2. O Python interpreta sua fala com o modelo Vosk.
3. O texto é comparado com `respostas.json`.
4. O sistema:
   - Fala uma resposta
   - Envia comandos para o Arduino (se necessário)
   - Atualiza status ou efeitos na interface

---

## 🗣️ Exemplo de Comando de Voz

```json
{
  "palavras_chave": ["voce", "brilhante", "tempo"],
  "resposta": "Posso me mexer… e falar?!",
  "acoes": ["mover_frente", "mover_tras"]
}
```

---

## 🧭 Comandos e Ações Suportadas

| Ação             | Descrição                         |
|------------------|-----------------------------------|
| `abrir_porta`    | Aciona o servo motor              |
| `girar`          | Rotação em 360°                   |
| `andar_3s`       | Move por 3 segundos               |
| `passos_frente`  | Movimento à frente (curto)        |
| `ajustar_porta`  | Faz calibração ou ajuste fino     |
| `girar_esquerda` | Rotação para a esquerda           |
| `girar_direita`  | Rotação para a direita            |
| `fechar_porta`   | Desativa servo ou fecha motor     |

---

## 🌐 Interface Web Futurista

A interface em `index.html` oferece:

- ✨ **Olhos animados com pupilas dinâmicas**
- 🌌 **Sistema de partículas flutuantes**
- 💡 **Efeitos de luz holográfica e HUD futurista**
- 🎯 **Perspectiva 3D e distorção visual**

```css
/* Exemplo de efeito visual */
.robot-visor {
  box-shadow: 0 0 200px rgba(0, 198, 251, 0.8);
  background: linear-gradient(135deg, rgba(0, 198, 251, 0.2), rgba(0, 91, 234, 0.2));
  animation: hologram-pulse 3s infinite alternate;
}
```

---

## 🛠️ Solução de Problemas

### ❌ Modelo Vosk não encontrado

> **Causa:** Pasta incorreta ou ausente  
> **Solução:**  
> - Verifique se o caminho está correto: `./vosk-model-small-pt/model`  
> - Use o mesmo nome de pasta que o código espera

### 🎙️ Microfone não detectado

> **Solução:** Liste os dispositivos de entrada:

```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))
```

Altere no `main.py`:

```python
input_device_index=None  # Altere para o índice do microfone desejado
```

---

## 📣 Comando Especial

- **"desligar"**  
  Encerra o sistema imediatamente com segurança.

---

## 👤 Autor

**Desenvolvedor:** Kayky de Paula  
📧 [kaykyrdepaula@gmail.com](mailto:kaykyrdepaula@gmail.com)  
🔗 [Repositório no GitHub](https://github.com/kayky-ctrl/chatbotVersaoFinal/)  
🐞 [Reportar Problemas / Issues](https://github.com/kayky-ctrl/chatbotVersaoFinal/issues)

---

## 🌐 Contato e Redes

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/kayky-de-paula-3053a5326/)  
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=flat&logo=instagram)](https://www.instagram.com/ntkayky/)

---

## 📄 Licença

Este projeto está sob a Licença MIT. Consulte o arquivo `LICENSE` para mais informações.
