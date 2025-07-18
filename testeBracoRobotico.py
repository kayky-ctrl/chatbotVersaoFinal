from pyuarm import UArm
import time

# Conecta ao uArm
robot = UArm()
robot.connect()
print("Conectado com sucesso!")

# Movimentos básicos
robot.set_position(x=150, y=0, z=50)  # Posição inicial
time.sleep(2)

# Movimento de pegar objeto
robot.set_position(x=200, y=0, z=30)  # Ir para posição do objeto
robot.set_pump(True)                  # Ligar a ventosa
time.sleep(1)
robot.set_position(z=100)             # Levantar o objeto
time.sleep(1)

# Movimento de soltar
robot.set_position(x=0, y=200, z=100) # Mover para posição de soltar
robot.set_pump(False)                 # Desligar a ventosa

# Finalizar
robot.disconnect()