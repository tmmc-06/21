import socket
import json
import time
import sys
import cliente
from cliente.interface.broadcast_receiver import BroadcastReceiver

class Interface:
    def __init__(self):
        # Ligação TCP para pedidos/respostas do jogo
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((cliente.SERVER_ADDRESS, cliente.PORT))

        # Socket UDP dedicado para receber broadcasts
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('', 0)) # porta livre atribuída pelo SO
        self.udp_port = self.udp_socket.getsockname()[1]

        # Informa o servidor de que a seguir será enviado o porto UDP
        self.send_str(self.connection, cliente.UDP_PORT)
        self.send_int(self.connection, self.udp_port, cliente.INT_SIZE)
        print(f"Cliente ligado por TCP; à escuta de broadcasts UDP na porta {self.udp_port}")

        # Iniciar recepção de udp no lado do cliente
        self.broadcast = BroadcastReceiver(self.udp_socket)
        self.broadcast.start()

    # ----- enviar e receber ----- #
    def send_str(self, connect, value: str) -> None:
        value = value.ljust(cliente.COMMAND_SIZE)
        connect.send(value.encode())

    def send_int(self, connect: socket.socket, value: int, n_bytes: int) -> None:
        connect.send(value.to_bytes(n_bytes, byteorder="big", signed=True))

    def execute(self):
        print("\nA aguardar pelo início do jogo...")
        
        try:
            while self.broadcast.running:
                # Vamos ler o estado que está a ser atualizado em background pelo Receiver
                estado = self.broadcast.estado_atual
                
                # Se o estado já chegou, se é a nossa vez, e a ronda/jogo não acabaram
                if estado and estado.get('is_my_turn') and not estado.get('round_over') and not estado.get('game_over'):
                    
                    # O Receiver já imprimiu "A tua jogada (hit/stand): ", por isso esperamos o input
                    acao = input("").strip().lower()
                    
                    if acao == "hit":
                        self.send_str(self.connection, cliente.HIT_OP)
                        time.sleep(0.5) # Pequena pausa para o servidor processar e enviar novo estado
                    elif acao == "stand":
                        self.send_str(self.connection, cliente.STD_OP)
                        time.sleep(0.5)
                    elif acao == "fim" or acao == "sair":
                        self.send_str(self.connection, cliente.END_OP)
                        self.broadcast.running = False
                        break
                    elif acao == "":
                        pass #se tocar no enter sem querer nao dá erro
                    else:
                        print("Comando inválido. Usa 'hit', 'stand' ou 'fim'.")
                
                # Se o jogo acabou, sai do loop ao fim de uns segundos para o jogador ver o resultado
                elif estado and estado.get('game_over'):
                    time.sleep(3)
                    self.broadcast.running = False
                    break
                else:
                    time.sleep(0.2)
                    
        except Exception as e:
            print(f"Erro na interface: {e}")
        finally:
            print("A encerrar ligação...")
            self.connection.close()
            self.udp_socket.close()
            sys.exit(0)