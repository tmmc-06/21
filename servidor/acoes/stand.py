
class Stand:
    def __init__(self, dados):
        self.dados = dados

    def executar(self, player_id):
        with self.dados.lock:
            self.dados.stands[player_id] = True
            self.dados.msg = f"Jogador {player_id+1} fez stand."