import threading
import random

class Dados:
    def __init__(self):
        self.lock = threading.Lock()
        self.score = 0
        self.game_over = False
        self.deck = []
        self.hands = [[], []]
        self.stands = [False, False]
        self.round_over = False
        self.current_turn = 0
        self.round_winner = None
        self.msg = ""

    def reset_ronda(self):
        with self.lock:
            self.deck = list(range(1, 12))
            random.shuffle(self.deck)
            self.hands = [[self.deck.pop(), self.deck.pop()], [self.deck.pop(), self.deck.pop()]]
            self.stands = [False, False]
            self.round_over = False
            self.current_turn = 0
            self.round_winner = None
            self.msg = "Nova ronda! Jogador 1 começa."

    def alterar_msg(self, mensagem):
        with self.lock:
            self.msg = mensagem


    def terminar_ronda(self, vencedor, novo_score, mensagem, terminou_jogo):
        with self.lock:
            self.round_winner = vencedor
            self.score = novo_score 
            self.msg = mensagem
            self.game_over = terminou_jogo
            self.round_over = True