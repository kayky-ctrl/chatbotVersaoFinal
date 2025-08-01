#include <Servo.h>

// =============================================
// DEFINIÇÃO DE PINOS
// =============================================

// Pinos do primeiro motor
const int ena = 2;   // Pino de habilitação do motor 1
const int dir = 3;    // Pino de direção do motor 1
const int pul = 4;    // Pino de pulso do motor 1

// Pinos do segundo motor
const int ena2 = 5;   // Pino de habilitação do motor 2
const int dir2 = 6;   // Pino de direção do motor 2
const int pul2 = 7;   // Pino de pulso do motor 2

// Pino do servo motor
const int servoPin = 22;  // Pino de controle do servo

// =============================================
// OBJETOS
// =============================================

Servo myServo;  // Objeto para controle do servo motor

// =============================================
// CONFIGURAÇÃO INICIAL
// =============================================

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
  delay(100);
  myServo.attach(servoPin);
  delay(100);
  myServo.write(-60);  // Posição inicial com a porta fechada
  delay(500);
  
  // Desabilita os motores inicialmente
  digitalWrite(ena, LOW);  
  digitalWrite(ena2, LOW);
  
  // Inicia a comunicação serial
  Serial.begin(9600);
  Serial.println("Sistema iniciado - Motores parados");
}

// =============================================
// LOOP PRINCIPAL
// =============================================

void loop() {
  // Verifica se há comandos disponíveis na serial
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    // Exibe o comando recebido
    Serial.print("Comando recebido: ");
    Serial.println(comando);
    
    // Executa o comando correspondente
    if (comando == "mover_frente") {
      moverFrente(3000);
    } 
    else if (comando == "mover_tras") {
      moverTras(3000);
    } 
    else if (comando == "girar_direita") {
      girarDireita(6000);
    }
    else if (comando == "girar_esquerda") {
      girarEsquerda(3000);
    }
    else if (comando == "abrir_porta") {
      abrirPorta();
    } 
    else if (comando == "fechar_porta") {
      fecharPorta();
    }
    else if (comando == "andar_3s") {
      moverFrente(8000);
    }
  }
}

// =============================================
// FUNÇÕES DE MOVIMENTAÇÃO
// =============================================

// Move o robô para frente pelo tempo especificado
void moverFrente(unsigned long tempo) {
  Serial.println("Movendo para frente");
  
  // Habilita os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configura a direção para frente
  digitalWrite(dir, HIGH);
  digitalWrite(dir2, LOW);
  
  // Gera pulsos pelo tempo especificado
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilita os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Move o robô para trás pelo tempo especificado
void moverTras(unsigned long tempo) {
  Serial.println("Movendo para trás");
  
  // Habilita os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configura a direção para trás
  digitalWrite(dir, LOW);
  digitalWrite(dir2, HIGH);
  
  // Gera pulsos pelo tempo especificado
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilita os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Gira o robô para direita pelo tempo especificado
void girarDireita(unsigned long tempo) {
  Serial.println("Girando para direita");
  
  // Habilita os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configura direções opostas para girar
  digitalWrite(dir, LOW);   // Motor 1 para frente
  digitalWrite(dir2, LOW);  // Motor 2 para trás
  
  // Gera pulsos pelo tempo especificado
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilita os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// Gira o robô para esquerda pelo tempo especificado
void girarEsquerda(unsigned long tempo) {
  Serial.println("Girando para esquerda");
  
  // Habilita os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configura direções opostas para girar
  digitalWrite(dir, HIGH);   // Motor 1 para trás
  digitalWrite(dir2, HIGH);  // Motor 2 para frente
  
  // Gera pulsos pelo tempo especificado
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilita os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

// =============================================
// FUNÇÕES DO SERVO MOTOR (PORTA)
// =============================================

// Abre a porta gradualmente
void abrirPorta() {
  Serial.println("Abrindo porta");
  for(int pos = 0; pos <= 100; pos += 1) {
    myServo.write(pos);
    delay(15);
  }
}

// Fecha a porta gradualmente
void fecharPorta() {
  Serial.println("Fechando porta");
  for(int pos = 90; pos >= 0; pos -= 1) {
    myServo.write(pos);
    delay(15);
  }
}
