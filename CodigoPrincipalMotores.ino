#include <Servo.h>

// Definindo os pinos dos motores
const int ena = 2;
const int dir = 3;
const int pul = 4;

const int ena2 = 5;
const int dir2 = 6;
const int pul2 = 7;

// Definindo o pino do servo
const int servoPin = 22;

// Criando objeto do servo
Servo myServo;

void setup() {
  // Configurando os pinos dos motores como saída
  pinMode(ena, OUTPUT);
  pinMode(dir, OUTPUT);
  pinMode(pul, OUTPUT);
  
  pinMode(ena2, OUTPUT);
  pinMode(dir2, OUTPUT);
  pinMode(pul2, OUTPUT);

  pinMode(servoPin, INPUT);
  digitalWrite(servoPin, LOW);
  // Configurando o servo
  delay(100);
  myServo.attach(servoPin);
  delay(100);
  myServo.write(-60); // Inicia com a porta fechada
  delay(500);
  
  // Iniciando com os motores desabilitados (verificar se LOW ou HIGH habilita no seu driver)
  digitalWrite(ena, LOW);  
  digitalWrite(ena2, LOW);
  
  // Iniciando comunicação serial
  Serial.begin(9600);
  Serial.println("Sistema iniciado - Motores parados");
}

void loop() {


  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    Serial.print("Comando recebido: ");
    Serial.println(comando);
    
    if (comando == "mover_frente") {
      moverFrente(2000);
    } 
    else if (comando == "mover_tras") {
      moverTras(2000);
    } 
    else if (comando == "girar_direita") {
      girarDireita(1000);
    }
    else if (comando == "girar_esquerda") {
      girarEsquerda(1000);
    }
    else if (comando == "abrir_porta") {
      abrirPorta();
    } 
    else if (comando == "fechar_porta") {
      fecharPorta();
    }
    else if (comando == "andar_3s") {
      moverFrente(3000);
    }
  }
}

void moverFrente(unsigned long tempo) {
  Serial.println("Movendo para frente");
  
  // Habilitar os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configurar direção para frente
  digitalWrite(dir, LOW);
  digitalWrite(dir2, HIGH);
  
  // Gerar pulsos por 'tempo' milissegundos
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(900); // Aumentado para 1ms
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(900);
  }
  
  // Desabilitar os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

void moverTras(unsigned long tempo) {
  Serial.println("Movendo para trás");
  
  // Habilitar os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configurar direção para trás
  digitalWrite(dir, HIGH);
  digitalWrite(dir2, LOW);
  
  // Gerar pulsos por 'tempo' milissegundos
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(900);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(900);
  }
  
  // Desabilitar os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

void girarDireita(unsigned long tempo) {
  Serial.println("Girando para direita");
  
  // Habilitar os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configurar direções opostas para girar
  digitalWrite(dir, HIGH);   // Motor 1 para frente
  digitalWrite(dir2, LOW);   // Motor 2 para trás
  
  // Gerar pulsos por 'tempo' milissegundos
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilitar os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

void girarEsquerda(unsigned long tempo) {
  Serial.println("Girando para esquerda");
  
  // Habilitar os motores
  digitalWrite(ena, HIGH);
  digitalWrite(ena2, HIGH);
  
  // Configurar direções opostas para girar
  digitalWrite(dir, LOW);   // Motor 1 para trás
  digitalWrite(dir2, HIGH);   // Motor 2 para frente
  
  // Gerar pulsos por 'tempo' milissegundos
  unsigned long inicio = millis();
  while(millis() - inicio < tempo) {
    digitalWrite(pul, HIGH);
    digitalWrite(pul2, HIGH);
    delayMicroseconds(1000);
    digitalWrite(pul, LOW);
    digitalWrite(pul2, LOW);
    delayMicroseconds(1000);
  }
  
  // Desabilitar os motores
  digitalWrite(ena, LOW);
  digitalWrite(ena2, LOW);
}

void abrirPorta() {
  Serial.println("Abrindo porta");
  for(int pos = 0; pos <= 90; pos += 1) { // Movimento suave
    myServo.write(pos);
    delay(15);
  }
}

void fecharPorta() {
  Serial.println("Fechando porta");
  for(int pos = 90; pos >= 0; pos -= 1) { // Movimento suave
    myServo.write(pos);
    delay(15);
  }
}



