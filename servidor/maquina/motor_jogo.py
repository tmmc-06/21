from servidor.maquina.dados import Dados
from servidor.acoes.hit import Hit
from servidor.acoes.stand import Stand

class MotorJogo:
    def __init__(self):
        self.dados = Dados()
        self.operacoes = {
            "hit": Hit(self.dados),
            "stand": Stand(self.dados)
        }
        self.reset_round()

    def reset_round(self):
        self.dados.reset_ronda()

    def get_state_for_player(self, player_id):
        opp_id = 1 if player_id == 0 else 0
        
        with self.dados.lock:
            opp_visible = self.dados.hands[opp_id][1:]
            return {
                "score": self.dados.score,
                "game_over": self.dados.game_over,
                "my_hand": self.dados.hands[player_id],
                "opp_visible": opp_visible,
                "my_stand": self.dados.stands[player_id],
                "opp_stand": self.dados.stands[opp_id],
                "round_over": self.dados.round_over,
                "is_my_turn": self.dados.current_turn == player_id,
                "msg": self.dados.msg
            }

    def play_action(self, player_id, action):
        with self.dados.lock:
            if self.dados.round_over or player_id != self.dados.current_turn:
                return {"accepted": False, "logs": [], "round_finished": False}

        logs = []
        
        if action in self.operacoes:
            self.operacoes[action].executar(player_id)
            with self.dados.lock:
                logs.append(self.dados.msg)
        else:
            self.dados.alterar_msg(f"Ação ignorada do Jogador {player_id+1}: {action}.")
            with self.dados.lock:
                logs.append(self.dados.msg)

        # Verifica se alguém ganhou a ronda após a jogada
        round_finished = self.check_round_end()

        # Passa o turno para o adversário, se a ronda não acabou e o adversário não fez stand
        with self.dados.lock:
            if not self.dados.round_over:
                opp_id = 1 if player_id == 0 else 0
                if not self.dados.stands[opp_id]:
                    self.dados.current_turn = opp_id

        return {
            "accepted": True,
            "logs": logs,
            "round_finished": round_finished,
        }

    def check_round_end(self):
        if self.dados.stands[0] and self.dados.stands[1]:
            score_p1 = sum(self.dados.hands[0])
            score_p2 = sum(self.dados.hands[1])
            winner = "Empate"

            p1_bust = score_p1 > 21
            p2_bust = score_p2 > 21
            
            novo_score = self.dados.score

            if p1_bust and p2_bust:
                if score_p1 < score_p2:
                    novo_score += 1
                elif score_p2 < score_p1:
                    novo_score -= 1
                if score_p1 < score_p2:
                    winner = "Jogador 1"
                elif score_p2 < score_p1: 
                    winner = "Jogador 2"
            elif p1_bust:
                novo_score -= 1
                winner = "Jogador 2"
            elif p2_bust:
                novo_score += 1
                winner = "Jogador 1"
            else:
                if score_p1 > score_p2:
                    novo_score += 1
                elif score_p2 > score_p1: 
                    novo_score -= 1

                if score_p1 > score_p2:
                    winner = "Jogador 1"
                elif score_p2 > score_p1:
                    winner = "Jogador 2"

            game_over = False

            if novo_score >= 7:
                msg = f"JOGO TERMINADO! Jogador 1 venceu! Score Global:{novo_score}"
                game_over = True
            elif novo_score <= -7:
                msg = f"JOGO TERMINADO! Jogador 2 venceu! Score Global:{novo_score}"
                game_over = True
            else:
                msg = (
                f"Ronda terminou! P1:{score_p1} | P2:{score_p2} "
                f"Vencedor: {winner}. Score global: {novo_score}"
                )
            
            self.dados.terminar_ronda(winner, novo_score, msg, game_over)

          
            if game_over:
                return False
            
            return True

        return False