
class Hit:
    def __init__(self, dados):
        self.dados = dados

    def executar(self, player_id):
        with self.dados.lock:
            # Só faz hit se o jogador não tiver feito stand e houver cartas
            if not self.dados.stands[player_id]:
                if len(self.dados.deck) > 0:
                    carta = self.dados.deck.pop()
                    self.dados.hands[player_id].append(carta)
                    self.dados.msg = f"Jogador {player_id+1} fez hit e tirou a carta {carta}."
                else:
                    self.dados.msg = f"Jogador {player_id+1} fez hit, mas o baralho está vazio."