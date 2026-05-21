import threading
import json

class BroadcastReceiver(threading.Thread):
    def __init__(self, udp_socket):
        super().__init__(daemon=True)
        self.udp_socket = udp_socket
        self.running = True
        self.estado_atual = None 

    def receive_object(self):
        data, addr = self.udp_socket.recvfrom(65535)
        obj = json.loads(data.decode('utf-8'))
        return obj, addr

    def run(self):
        print("Receiver de broadcasts UDP ativo...")
        
        while self.running: 
            try:
                estado, addr = self.receive_object()
                self.estado_atual = estado  # Atualiza o estado lido
                
                print("--- ESTADO DO JOGO ---")
                print(f"Score Global: {estado.get('score', 0)}")
                print(f"Mensagem: {estado.get('msg', '')}")
                
                # Mostrar as mãos
                print(f"Cartas do Adversário: {estado.get('opp_visible', [])}")
                minha_mao = estado.get('my_hand', [])
                print(f"A Tua Mão: {minha_mao} (Soma: {sum(minha_mao)})")
                
                # Avisos de turno
                if estado.get('game_over'):
                    print(">>>  Game Over <<<")
                elif estado.get('round_over'):
                    print(">>> Ronda acabou. A aguardar o servidor... <<<")
                elif estado.get('is_my_turn'):
                    print(">>> É A TUA VEZ! <<<")
                elif estado.get('my_stand'):
                    print(">>> Stand. Á espera... <<<")
                else:
                    print(">>> Á espera a jogada do adversário... <<<")
                #na vez de cada jogador mostra pequena mensagem de aviso
                if estado.get('is_my_turn') and not estado.get('game_over') and not estado.get('round_over'):
                    print("\nEscolhe a tua ação: Hit ou Stand: ", end="", flush=True)

            except Exception as e:
                if self.running:
                    print(f"Receiver UDP desconectado: {e}")
                self.running = False