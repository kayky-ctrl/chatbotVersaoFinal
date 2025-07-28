// Definindo os pinos para o sensor ultrassônico
const int trigPin = 2;
const int echoPin = 3;

// Definindo os pinos para a ponte H
const int enA = 9;   // Pino PWM para controle de velocidade
const int in1 = 5;
const int in2 = 6;

// Distância de parada em cm
const int distanciaParada = 20;

void setup() {
  // Inicializando os pinos do sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  // Inicializando os pinos da ponte H
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  
  // Iniciando comunicação serial para debug
  Serial.begin(9600);
}

void loop() {
  // Medindo a distância
  float distancia = medirDistancia();
  
  Serial.print("Distancia: ");
  Serial.print(distancia);
  Serial.println(" cm");
  
  // Se a distância for maior que 50 cm, gira o motor
  if (distancia > distanciaParada) {
    girarMotor();
  } else {
    // Caso contrário, para o motor
    pararMotor();
    Serial.println("Objeto detectado a menos de 50 cm - Motor parado");
  }
  
  delay(100); // Pequeno delay entre as medições
}

float medirDistancia() {
  // Limpa o trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  
  // Define o trigPin no estado HIGH por 10 microsegundos
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Lê o echoPin, retorna o tempo de viagem da onda sonora em microssegundos
  long duration = pulseIn(echoPin, HIGH);
  
  // Calcula a distância (velocidade do som dividida por 2 - ida e volta)
  float distancia = duration * 0.034 / 2;
  
  return distancia;
}

void girarMotor() {
  // Define a direção de rotação (por exemplo, para frente)
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  
  // Define a velocidade máxima (255) ou ajuste conforme necessário
  analogWrite(enA, 255);
  
  Serial.println("Motor girando...");
}

void pararMotor() {
  // Desliga o motor
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  analogWrite(enA, 0);
}
