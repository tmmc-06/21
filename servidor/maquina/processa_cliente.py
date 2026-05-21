import json
import threading
import servidor

class ProcessaCliente(threading.Thread):
    def __init__(self, connection, address, motor, lista_clientes, emissor, player_id):
        super().__init__()
        self.connection = connection
        self.address = address
        self.motor = motor
        self.lista_clientes = lista_clientes
        self.emissor = emissor
        self.player_id = player_id
        self.udp_port = None


    # ---------------------- interaction with sockets ------------------------------
    def receive_int(self,connection, n_bytes: int) -> int:
        """
        :param n_bytes: The number of bytes to read from the current connection
        :return: The next integer read from the current connection
        """
        data = connection.recv(n_bytes)
        return int.from_bytes(data, byteorder='big', signed=True)

    def send_int(self,connection, value: int, n_bytes: int) -> None:
        """
        :param value: The integer value to be sent to the current connection
        :param n_bytes: The number of bytes to send
        """
        connection.send(value.to_bytes(n_bytes, byteorder="big", signed=True))

    def receive_str(self,connection, n_bytes: int) -> str:
        """
        :param n_bytes: The number of bytes to read from the current connection
        :return: The next string read from the current connection
        """
        data = connection.recv(n_bytes)
        return data.decode()

    def send_str(self,connection, value: str) -> None:
        """
        :param value: The string value to send to the current connection
        """
        connection.connection.send(value.encode())

    # Implement a method that sends and object and returns an object.
    def send_object(self,connection, obj):
        """1º: envia tamanho, 2º: envia dados."""
        data = json.dumps(obj).encode('utf-8')
        size = len(data)
        self.send_int(connection, size, servidor.INT_SIZE)         # Envio do tamanho
        connection.send(data)              		     # Envio do objeto

    def receive_object(self,connection):
        """1º: lê tamanho, 2º: lê dados."""
        size = self.receive_int(connection, servidor.INT_SIZE)  	# Recebe o tamanho
        data = connection.recv(size)       			# Recebe o objeto
        return json.loads(data.decode('utf-8'))
    #-------------------
    def run(self):
        print(f"[{self.address}] Thread iniciada (Jogador {self.player_id + 1})")
        
        # Envia o estado inicial mal o jogador se conecta
        self.emissor.notificar_jogadores()
        
        last_request = False
        while not last_request:
            try:
                request_type = self.receive_str(self.connection, servidor.COMMAND_SIZE)
                
                if request_type == servidor.UDP_PORT:
                    self.udp_port = self.receive_int(self.connection, servidor.INT_SIZE)
                    self.lista_clientes.adicionar(self.address, self.connection, self.udp_port)
                    # Força nova notificação agora que sabemos o porto UDP
                    self.emissor.notificar_jogadores()

                elif request_type == servidor.HIT_OP:
                    print(f"[{self.address}] Pediu HIT")
                    result = self.motor.play_action(self.player_id, "hit")
                    self.processar_resultado_ronda(result)
                    
                elif request_type == servidor.STD_OP:
                    print(f"[{self.address}] Pediu STAND")
                    result = self.motor.play_action(self.player_id, "stand")
                    self.processar_resultado_ronda(result)

                elif request_type == servidor.END_OP:
                    last_request = True
                    self.lista_clientes.remover(self.address)
                    self.connection.close()
                    
            except Exception as e:
                print(f"[{self.address}] Erro ou desconexão: {e}")
                self.lista_clientes.remover(self.address)
                break

    def processar_resultado_ronda(self, result):
        #Notifica os jogadores da jogada atual
        self.emissor.notificar_jogadores()
        
        if result["round_finished"]:
            import time
            time.sleep(1)
            self.motor.reset_round()
            self.emissor.notificar_jogadores()