import socket
import json
import time
import sys
import pygame
import cliente
from cliente.interface.broadcast_receiver import BroadcastReceiver

# Configurações Visuais e Cores
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30

# Cores (RGB)
BG_COLOR = (34, 112, 63)       # Verde mesa de Casino/Feltro
TEXT_COLOR = (255, 255, 255)    # Branco
CARD_COLOR = (245, 245, 240)    # Off-white para as cartas
CARD_BORDER = (0, 0, 0)         # Preto
BUTTON_COLOR = (41, 128, 185)   # Azul
BUTTON_HOVER = (52, 152, 219)   # Azul claro
BUTTON_TEXT = (255, 255, 255)
MSG_BG_COLOR = (20, 70, 40)     # Verde escuro para caixa de status

class InterfaceGrafica:
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

        # Inicialização do Pygame
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("21")
        self.clock = pygame.time.Clock()
        
        # Fontes do sistema
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 18)
        self.font_cards = pygame.font.SysFont("Arial", 22, bold=True)

        # Definição dos Retângulos dos Botões (X, Y, Largura, Altura)
        self.btn_hit_rect = pygame.Rect(200, 500, 150, 45)
        self.btn_stand_rect = pygame.Rect(450, 500, 150, 45)

    # ----- enviar e receber ----- #
    def send_str(self, connect, value: str) -> None:
        value = value.ljust(cliente.COMMAND_SIZE)
        connect.send(value.encode())

    def send_int(self, connect: socket.socket, value: int, n_bytes: int) -> None:
        connect.send(value.to_bytes(n_bytes, byteorder="big", signed=True))

    # ----- Funções Auxiliares de Desenho (Rendering) ----- #
    def draw_text(self, text, font, color, x, y, center=False):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)

    def draw_button(self, rect, text, is_hovered):
        color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=8)
        self.draw_text(text, self.font_body, BUTTON_TEXT, rect.centerx, rect.centery, center=True)

    def draw_card(self, valor, x, y, ocultada=False):
        rect = pygame.Rect(x, y, 70, 100)
        if ocultada:
            # Desenha as costas da carta (Vermelha com borda)
            pygame.draw.rect(self.screen, (192, 57, 43), rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=3, border_radius=6)
            self.draw_text("?", self.font_cards, (255, 255, 255), rect.centerx, rect.centery, center=True)
        else:
            # Desenha a frente da carta
            pygame.draw.rect(self.screen, CARD_COLOR, rect, border_radius=6)
            pygame.draw.rect(self.screen, CARD_BORDER, rect, width=2, border_radius=6)
            self.draw_text(str(valor), self.font_cards, (0, 0, 0), rect.centerx, rect.centery, center=True)

    # ----- Ciclo Principal do Jogo ----- #
    def execute(self):
        running = True
        
        while running:
            # Buscar o estado do jogo capturado pelo Receiver UDP thread-safe
            estado = self.broadcast.estado_atual
            
            # Captura de posição do Rato para efeitos de Hover nos botões
            mouse_pos = pygame.mouse.get_pos()
            hover_hit = self.btn_hit_rect.collidepoint(mouse_pos)
            hover_stand = self.btn_stand_rect.collidepoint(mouse_pos)

            # --- Tratamento de Eventos (Inputs) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Envia sinal de stop ao servidor antes de fechar a janela
                    try:
                        self.send_str(self.connection, cliente.END_OP)
                    except:
                        pass
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Apenas permite ações se houver estado válido, se for o turno do jogador e se o jogo não tiver terminado
                    if estado and estado.get('is_my_turn') and not estado.get('game_over') and not estado.get('round_over'):
                        if hover_hit:
                            print("[GUI] Clique em HIT")
                            self.send_str(self.connection, cliente.HIT_OP)
                        elif hover_stand:
                            print("[GUI] Clique em STAND")
                            self.send_str(self.connection, cliente.STD_OP)

            # --- Desenho do Ecrã (Rendering) ---
            self.screen.fill(BG_COLOR)

            # Título principal e Score Global
            self.draw_text("21", self.font_title, (241, 196, 15), SCREEN_WIDTH // 2, 30, center=True)
            
            score_global = estado.get('score', 0) if estado else 0
            self.draw_text(f"Score Global: {score_global}", self.font_body, TEXT_COLOR, SCREEN_WIDTH // 2, 75, center=True)

            if estado:
                # 1. Desenhar a Mão do Adversário (Cartas Visíveis)
                self.draw_text("Mão do Adversário:", self.font_body, TEXT_COLOR, 50, 120)
                opp_cards = estado.get('opp_visible', [])
                
                # Se o oponente não deu stand ou jogo não acabou, assume-se que há uma carta oculta (regra clássica)
                # O teu motor envia apenas a lista das visíveis (ex: [8])
                self.draw_card("?", 50, 150, ocultada=True)
                for i, card in enumerate(opp_cards):
                    self.draw_card(card, 130 + (i * 80), 150)

                # 2. Desenhar a Minha Mão
                my_hand = estado.get('my_hand', [])
                self.draw_text(f"A Tua Mão (Total: {sum(my_hand)}):", self.font_body, TEXT_COLOR, 50, 280)
                for i, card in enumerate(my_hand):
                    self.draw_card(card, 50 + (i * 80), 310)

                # 3. Caixa de Mensagem / Logs do Servidor
                msg_box = pygame.Rect(50, 430, 700, 45)
                pygame.draw.rect(self.screen, MSG_BG_COLOR, msg_box, border_radius=5)
                self.draw_text(estado.get('msg', ''), self.font_body, (230, 230, 230), msg_box.centerx, msg_box.centery, center=True)

                # 4. Estado de Turno e Desenho de Botões
                if estado.get('game_over'):
                    self.draw_text(">>> GAME OVER! Partida Terminada <<<", self.font_title, (231, 76, 60), SCREEN_WIDTH // 2, 520, center=True)
                elif estado.get('round_over'):
                    self.draw_text("Ronda acabou. A aguardar resposta do servidor...", self.font_body, (241, 196, 15), SCREEN_WIDTH // 2, 520, center=True)
                elif estado.get('is_my_turn'):
                    # Desenha os botões interativos apenas quando for a vez do cliente
                    self.draw_button(self.btn_hit_rect, "HIT (Pedir)", hover_hit)
                    self.draw_button(self.btn_stand_rect, "STAND (Passar)", hover_stand)
                elif estado.get('my_stand'):
                    self.draw_text("Fizeste STAND. A aguardar jogadas do oponente...", self.font_body, TEXT_COLOR, SCREEN_WIDTH // 2, 520, center=True)
                else:
                    self.draw_text("A aguardar a jogada do adversário...", self.font_body, TEXT_COLOR, SCREEN_WIDTH // 2, 520, center=True)
            else:
                # Caso o estado inicial ainda não tenha chegado via UDP
                self.draw_text("A aguardar ligação estável e estado do jogo...", self.font_body, TEXT_COLOR, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)

            pygame.display.flip()
            self.clock.tick(FPS)

        # Encerramento limpo fora do ciclo principal
        print("A encerrar ligação gráfica...")
        self.broadcast.running = False
        self.connection.close()
        self.udp_socket.close()
        pygame.quit()
        sys.exit(0)
