### 1. Funcionamento do Jogo
Toda a inteligência e validação das regras do Blackjack ocorrem exclusivamente no lado do **Servidor**, mantendo os clientes como interfaces puramente visuais e recetivas:

* **Baralho e Distribuição:** Ao iniciar cada ronda, o servidor gera uma sequência numérica de 1 a 11, baralha os dados usando `random.shuffle()` e distribui automaticamente duas cartas a cada jogador.

* **Controlo de Turnos:** O estado de exclusividade do turno é gerido pela variável `current_turn`. O cliente apenas ganha permissão para interagir quando o servidor valida que é a sua vez.

* **Comandos de Execução:** As ações são processadas através do padrão de desenho de comandos (classes `Hit` e `Stand`):

  * **Hit:** Remove um elemento com `deck.pop()` e anexa-o à lista de mãos do jogador respetivo.

  * **Stand:** Altera o booleano do jogador em `stands` para `True`, informando o motor de jogo de que este jogador concluiu a sua participação na ronda atual.

### 2. Protocolo de Mensagens
O projeto resolve o desafio clássico de balanceamento entre fiabilidade e baixa latência através de uma arquitetura de sockets híbrida:
* **Fluxo TCP (Ações Críticas do Cliente ➔ Servidor):**

  * Utilizado para garantir que nenhum comando de jogo se perde. Como o TCP assegura a entrega ordenada e fiável, todas as mensagens de ação utilizam este canal.

  * Baseia-se num protocolo de tamanho fixo definido por `COMMAND_SIZE = 9`. Operações como clicar em HIT enviam a string `"hit      "`, preenchida com espaços em branco (*padding*) para totalizar exatamente 9 bytes.

  * Aquando do estabelecimento da ligação TCP, o cliente envia uma mensagem inicial contendo o porto UDP livre alocado pelo seu sistema operativo (`udp_port `), permitindo que o servidor saiba para onde direcionar os fluxos rápidos.

* **Fluxo UDP (Atualização de Estado Servidor ➔ Clientes):**

  * Utilizado para realizar *broadcast* rápido e assíncrono do estado do jogo através da classe `BroadcastEmissor`.

  * O servidor empacota as variáveis estruturadas num objeto serializado em formato **JSON** e envia-o via pacotes UDP Datagram para os endereços mapeados na `ListaClientes`.

  * Do lado do cliente, a thread `BroadcastReceiver` corre continuamente em segundo plano, efetuando a desserialização (`json.loads`) e injetando as variáveis em tempo real na interface gráfica (`interface_grafica.py` ou `interface.py`).

### 3. Gestão e Sincronização de Dados
Por se tratar de um ambiente multithreading distribuído onde múltiplos utilizadores interagem em simultâneo, a integridade dos dados foi salvaguardada na classe `Dados` (`dados.py`):

* **Exclusão Mútua (Locks):** A classe possui um trinco de exclusão mútua (`self.lock = threading.Lock()`). Sempre que uma thread do servidor executa uma alteração de estado crítico (gerar nova ronda, atualizar pontuação global ou registar um *stand*), a operação é protegida num bloco `with self.lock:`. Isto previne condições de corrida (*race conditions*).

* **Ocultação Condicional (Mecanismo Anti-Cheat):** O servidor reconstrói o objeto de estado dinamicamente para cada utilizador antes de o enviar por UDP. O ficheiro JSON final contém as cartas privadas do próprio (`my_hand`), mas filtra e esconde a carta oculta do oponente (`opp_visible`), cumprindo as regras oficiais do Blackjack e evitando que os clientes tenham acesso a informação privilegiada na memória local.

* **Dicionários Estruturados e Mapeamentos (`Dict`):** Na gestão de conexões (`lista_clientes.py`), utiliza-se o dicionário `self._clientes`. Este mapeia uma chave única do tipo **Tuplo** `Tuple[str, int]` (composta pelo IP e Porto TCP de origem do cliente) para um segundo dicionário interno que encapsula o objeto socket de ligação (`connection`), o porto UDP (`udp_port`) e o tuplo de destino UDP (`udp_address`). Esta modelagem confere uma complexidade algorítmica de busca, inserção e remoção extremamente eficiente de ordem constante $O(1)$.

* **Listas Dinâmicas / Vetores (`List`):** O baralho de cartas (`self.deck`) é implementado como uma lista linear de inteiros (valores de 1 a 11). A escolha desta estrutura deve-se à compatibilidade direta com a função `random.shuffle()` para baralhar, e à capacidade de efetuar operações eficientes de remoção no topo através do método dinâmico `pop()`.

* **Listas Bidimensionais / Matrizes (`List[List]`):** As mãos dos jogadores (`self.hands`) são modeladas como uma lista encadeada que armazena outras duas sublistas dinâmicas `[[], []]`. Cada índice principal (0 e 1) representa um jogador na partida, onde a respetiva sublista armazena e expande os inteiros das cartas acumuladas a cada jogada de *hit*.

* **Vetores de Controlo Booleano (`List[bool]`):** O estado de paragem dos utilizadores é controlado por uma lista indexada de valores booleanos (`self.stands`), permitindo verificar instantaneamente se o jogador na posição correspondente já declarou *stand*.

* **Sincronização por Exclusão Mútua (`threading.Lock`):** Como os dados acima são partilhados e manipulados de forma concorrente por múltiplas threads de clientes, a classe `Dados` utiliza um trinco mecânico (`self.lock`). Todas as escritas e leituras críticas — tais como retirar cartas com `pop()`, reiniciar a ronda com `reset_ronda()` ou atualizar os scores globais — são obrigatoriamente encapsuladas dentro de blocos atómicos com `with self.lock:`, eliminando por completo o risco de condições de corrida (*race conditions*).

* **Ocultação Condicional (Mecanismo Anti-Cheat):** Antes de realizar o envio do estado via pacotes UDP, o servidor filtra os dados estruturados através do método `get_state_for_player`. O payload JSON final descodificado pelo cliente contém as cartas privadas do próprio utilizador (`my_hand`), mas a estrutura limpa e omite a carta oculta do oponente (`opp_visible`), prevenindo leituras indevidas de memória local por parte do cliente.
