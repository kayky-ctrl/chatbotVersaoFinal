#include <Servo.h>  // Biblioteca para controlar o servo motor

// Definição dos pinos para os motores de passo
const int ena = 2, dir = 3, pul = 4;     // Motor 1: enable, direction, pulse
const int ena2 = 5, dir2 = 6, pul2 = 7;  // Motor 2: enable, direction, pulse
const int servoPin = 22;                 // Pino para o servo motor da porta

Servo myServo;  // Objeto para controlar o servo motor

void setup() {
  // Configuração dos pinos dos motores como saída
  pinMode(ena, OUTPUT);
  pinMode(dir, OUTPUT);
  pinMode(pul, OUTPUT);
  pinMode(ena2, OUTPUT);
  pinMode(dir2, OUTPUT);
  pinMode(pul2, OUTPUT);

  // Configuração inicial do pino do servo
  pinMode(servoPin, INPUT);
  digitalWrite(servoPin, LOW);

  // Inicialização do servo motor
  delay(100);                // Pequena pausa para estabilização
  myServo.attach(servoPin);  // Associa o servo ao pino
  delay(100);
  myServo.write(-60);  // Posição inicial (porta fechada)
  delay(500);          // Tempo para o servo atingir a posição

  // Desativa os motores inicialmente
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);

  // Inicia comunicação serial com computador
  Serial.begin(9600);
  Serial.println("Sistema iniciado - Motores parados");
}

void loop() {
  // Verifica se há comandos recebidos via serial
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');  // Lê o comando completo
    comando.trim();                                 // Remove espaços extras

    // Exibe o comando recebido no monitor serial
    Serial.print("Comando recebido: ");
    Serial.println(comando);

    // Executa a função correspondente ao comando
    if (comando == "mover_frente") {
      moverFrente(2000);  // Move para frente por 2 segundos
    } else if (comando == "mover_tras") {
      moverTras(2000);  // Move para trás por 2 segundos
    } else if (comando == "girar_direita") {
      girarDireita(1000);  // Gira para direita por 1 segundo
    } else if (comando == "girar_esquerda") {
      girarEsquerda(1000);  // Gira para esquerda por 1 segundo
    } else if (comando == "abrir_porta") {
      abrirPorta();  // Abre a porta (servo motor)
    } else if (comando == "fechar_porta") {
      fecharPorta();  // Fecha a porta (servo motor)
    } else if (comando == "andar_3s") {
      moverFrente(3000);  // Move para frente por 3 segundos
    } else if (comando == "passos_frente") {
      pequenosPassos(50, 1);  // 50 passos para frente
    } else if (comando == "passos_tras") {
      pequenosPassos(50, -1);  // 50 passos para trás
    }
  }
}

// Função para mover para frente
void moverFrente(unsigned long tempo) {
  Serial.println("Movendo para frente");

  // Ativa os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);

  // Define direção (depende da ligação dos motores)
  digitalWrite(dir, LOW);
  digitalWrite(dir2, HIGH);

  // Gera pulsos para movimentação
  unsigned long inicio = millis();
  while (millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(900);  // Controla velocidade
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(900);
  }

  // Desativa os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Função para mover para trás (similar à moverFrente)
void moverTras(unsigned long tempo) {
  Serial.println("Movendo para trás");
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  digitalWrite(dir, HIGH);  // Direção invertida
  digitalWrite(dir2, LOW);

  unsigned long inicio = millis();
  while (millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(900);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(900);
  }

  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Função para girar para direita
void girarDireita(unsigned long tempo) {
  Serial.println("Girando para direita");
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  // Motores em direções opostas para girar
  digitalWrite(dir, HIGH);
  digitalWrite(dir2, LOW);

  unsigned long inicio = millis();
  while (millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }

  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Função para girar para esquerda (similar à girarDireita)
void girarEsquerda(unsigned long tempo) {
  Serial.println("Girando para esquerda");
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  // Motores em direções opostas
  digitalWrite(dir, LOW);
  digitalWrite(dir2, HIGH);

  unsigned long inicio = millis();
  while (millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }

  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Função para abrir a porta (servo motor)
void abrirPorta() {
  Serial.println("Abrindo porta");
  // Movimento gradual de 0 a 90 graus
  for (int pos = 0; pos <= 90; pos += 1) {
    myServo.write(pos);
    delay(15);  // Controla velocidade do movimento
  }
}

// Função para fechar a porta (servo motor)
void fecharPorta() {
  Serial.println("Fechando porta");
  // Movimento gradual de 90 a 0 graus
  for (int pos = 90; pos >= 0; pos -= 1) {
    myServo.write(pos);
    delay(15);
  }
}
