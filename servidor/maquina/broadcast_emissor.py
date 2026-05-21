# broadcast_emissor.py
import socket
import json

class BroadcastEmissor:
    def __init__(self, lista_clientes, motor):
        self.lista_clientes = lista_clientes
        self.motor = motor
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_object_udp(self, udp_address, obj):
        data = json.dumps(obj).encode('utf-8')
        self.udp_socket.sendto(data, udp_address)

    def notificar_jogadores(self):
        """Notifica cada jogador do seu estado específico do jogo."""
        destinos = self.lista_clientes.obter_destinos_udp()
        clientes_ativos = list(destinos.keys())
        
        for player_id, address in enumerate(clientes_ativos):
            if player_id > 1: 
                break  # O jogo é só para 2 jogadores
                
            estado = self.motor.get_state_for_player(player_id)
            udp_address = destinos[address]
            
            try:
                self.send_object_udp(udp_address, estado)
            except Exception as e:
                print(f"Erro ao notificar {address}: {e}")