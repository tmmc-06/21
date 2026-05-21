import socket
import servidor
from servidor.maquina.motor_jogo import MotorJogo
from servidor.maquina.lista_clientes import ListaClientes
from servidor.maquina.broadcast_emissor import BroadcastEmissor
from servidor.maquina.processa_cliente import ProcessaCliente 

class Maquina:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', servidor.PORT))
        self.lista_clientes = ListaClientes()
        self.motor = MotorJogo()
        self.emissor = BroadcastEmissor(self.lista_clientes, self.motor)

    def execute(self):
        self.s.listen(2)
        print(f"Servidor à espera de 2 jogadores na porta {servidor.PORT}...")
		#jogador 1 com id 0
        conn1, addr1 = self.s.accept()
        print(f"Jogador 1 conectou-se a partir de: {addr1}")
        t1 = ProcessaCliente(conn1, addr1, self.motor, self.lista_clientes, self.emissor, 0)
        
        #Jogador 2 com ID 1
        conn2, addr2 = self.s.accept()
        print(f"Jogador 2 conectou-se a partir de: {addr2}")
        t2 = ProcessaCliente(conn2, addr2, self.motor, self.lista_clientes, self.emissor, 1)
        
        print("Ambos os jogadores conectados. A iniciar jogo e a lançar threads...")
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        self.s.close()
        print("Servidor encerrado.")