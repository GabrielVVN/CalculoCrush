import pygame
import random
import os
import math # Usado para animações

# --- Constantes ---
GRID_ROWS = 8
GRID_COLS = 8
BLOCK_SIZE = 80
UI_HEIGHT = 100
WIDTH = GRID_COLS * BLOCK_SIZE
HEIGHT = (GRID_ROWS * BLOCK_SIZE) + UI_HEIGHT
FPS = 60 # Aumentado para animações mais suaves

# --- NOVA PALETA DE CORES (Moderna / Dark Mode) ---
WHITE = (230, 230, 230)
BLACK = (10, 10, 10)
GRAY_UI = (30, 30, 30) # Fundo da UI
BG_COLOR = (20, 20, 20)  # Fundo do tabuleiro
GRID_BG = (40, 40, 40)   # Cor do espaço vazio da grade

# Cores dos Blocos (Baseado no número)
COLOR_1_3 = (60, 100, 160)   # Azul
COLOR_4_6 = (60, 160, 100)   # Verde
COLOR_7_9 = (180, 140, 50)  # Laranja
COLOR_PRODUCT = (140, 70, 160) # Roxo (para produtos >= 10)

# Cores de Destaque
RED_ERROR = (220, 20, 60)
GOLD_WIN = (255, 215, 0)
GREEN_MATCH = (0, 255, 0)
BLUE_HINT = (0, 100, 255)

HINT_BUTTON_RECT = pygame.Rect(WIDTH // 2 - 60, UI_HEIGHT // 2 - 20, 120, 40)

# --- Constantes de Animação ---
ANIM_SWAP_SPEED = 300 # 300ms (0.3s) para trocar
ANIM_FALL_SPEED = 500 # 0.5s para cair

# Configurações do Nível 1
STARTING_MOVES = 20
TARGET_SCORE = 3000

# Lista de números fáceis
EASY_NUMBERS_LIST = (
    [1, 2, 3] * 15 + [4, 5] * 7 + [6, 7, 8, 9] * 4 +
    [4, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 36] * 2
)
random.shuffle(EASY_NUMBERS_LIST)

# --- Inicialização do Pygame ---
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CalculoCrush")
clock = pygame.time.Clock()

# --- Carregamento de Fonte Customizada ---
ASSETS_PATH = "assets"
FONT_PATH = os.path.join(ASSETS_PATH, "font.ttf")

try:
    number_font = pygame.font.Font(FONT_PATH, 40)
    ui_font = pygame.font.Font(FONT_PATH, 30)
    game_over_font = pygame.font.Font(FONT_PATH, 60)
    button_font = pygame.font.Font(FONT_PATH, 25)
except FileNotFoundError:
    print(f"Erro: Fonte '{FONT_PATH}' não encontrada. Usando fonte padrão.")
    number_font = pygame.font.SysFont(None, 50)
    ui_font = pygame.font.SysFont(None, 40)
    game_over_font = pygame.font.SysFont(None, 70)
    button_font = pygame.font.SysFont(None, 30)

# --- Funções de Lógica (A maioria sem alteração) ---

def create_board(rows, cols):
    board = []
    for row in range(rows):
        board.append([])
        for col in range(cols):
            board[row].append(random.choice(EASY_NUMBERS_LIST))
    return board

def get_clicked_pos(pos):
    x, y = pos
    y_adjusted = y - UI_HEIGHT
    if y_adjusted < 0: return None
    row = y_adjusted // BLOCK_SIZE
    col = x // BLOCK_SIZE
    if row >= GRID_ROWS or col >= GRID_COLS or row < 0 or col < 0:
        return None
    return (row, col)

def swap_pieces(board, pos1, pos2):
    r1, c1 = pos1
    r2, c2 = pos2
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]

def find_matches(board):
    matches = set()
    # Horizontal
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS - 2):
            a = board[r][c]; b = board[r][c+1]; c_val = board[r][c+2]
            if a > 0 and b > 0 and a * b == c_val:
                matches.update([(r, c), (r, c+1), (r, c+2)])
    # Vertical
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS - 2):
            a = board[r][c]; b = board[r+1][c]; c_val = board[r+2][c]
            if a > 0 and b > 0 and a * b == c_val:
                matches.update([(r, c), (r+1, c), (r+2, c)])
    return matches

def find_hint(board):
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # Direita
            if c < GRID_COLS - 1:
                pos1 = (r, c); pos2 = (r, c + 1)
                swap_pieces(board, pos1, pos2)
                matches = find_matches(board)
                swap_pieces(board, pos1, pos2)
                if matches: return (pos1, pos2)
            # Baixo
            if r < GRID_ROWS - 1:
                pos1 = (r, c); pos2 = (r + 1, c)
                swap_pieces(board, pos1, pos2)
                matches = find_matches(board)
                swap_pieces(board, pos1, pos2)
                if matches: return (pos1, pos2)
    return None

def remove_pieces(board, matches):
    score_gain = 0
    for r, c in matches:
        number = board[r][c]
        if number > 0:
            score_gain += number 
            board[r][c] = 0
    return score_gain

def drop_pieces(board):
    """
    Modificado para retornar uma LISTA de movimentos de queda.
    moves = [ (número, (r_origem, c_origem), (r_destino, c_destino)), ... ]
    """
    moves = []
    for c in range(GRID_COLS):
        drop_to_row = GRID_ROWS - 1
        for r in range(GRID_ROWS - 1, -1, -1):
            if board[r][c] > 0:
                number = board[r][c]
                if r != drop_to_row:
                    # Registra o movimento
                    moves.append((number, (r, c), (drop_to_row, c)))
                    # Executa a lógica
                    board[drop_to_row][c] = number
                    board[r][c] = 0
                drop_to_row -= 1
    return moves

def refill_board(board):
    """
    Modificado para retornar uma LISTA de novas peças.
    new_pieces = [ (número, (r, c)), ... ]
    """
    new_pieces = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if board[r][c] == 0:
                number = random.choice(EASY_NUMBERS_LIST)
                board[r][c] = number
                new_pieces.append((number, (r, c)))
    return new_pieces

def is_swap_valid(board, pos1, pos2):
    """NOVA função que APENAS verifica, não anima."""
    swap_pieces(board, pos1, pos2)
    matches = find_matches(board)
    swap_pieces(board, pos1, pos2) # Desfaz
    return len(matches) > 0

# --- NOVAS FUNÇÕES de Animação e Desenho ---

def lerp(a, b, t):
    """Interpolação Linear: de 'a' para 'b' em 't' (0.0 a 1.0)"""
    return a + (b - a) * t

def get_piece_color(number):
    """Retorna a cor correta para o número."""
    if number == 0:
        return GRID_BG
    elif number < 4:
        return COLOR_1_3
    elif number < 7:
        return COLOR_4_6
    elif number < 10:
        return COLOR_7_9
    else:
        return COLOR_PRODUCT

def draw_piece(screen, number, x, y, size=BLOCK_SIZE, border_color=None):
    """Desenha uma peça individual (arredondada e colorida)."""
    piece_rect = pygame.Rect(x, y, size, size)
    
    # Desenha o fundo da peça
    color = get_piece_color(number)
    pygame.draw.rect(screen, color, piece_rect, border_radius=10)
    
    # Desenha o número (agora em BRANCO)
    text_surface = number_font.render(str(number), True, WHITE)
    text_rect = text_surface.get_rect(center=piece_rect.center)
    screen.blit(text_surface, text_rect)
    
    # Desenha a borda de destaque (se houver)
    if border_color:
        pygame.draw.rect(screen, border_color, piece_rect, 5, border_radius=10)

def draw_board_static(screen, board, highlight_set=set(), hint_to_show=None, 
                      hide_pieces=set()):
    """
    Desenha o tabuleiro estático.
    'hide_pieces' é um set de (r, c) para não desenhar (serão animados).
    """
    # Desenha o fundo da grade
    grid_rect = pygame.Rect(0, UI_HEIGHT, WIDTH, HEIGHT - UI_HEIGHT)
    pygame.draw.rect(screen, BG_COLOR, grid_rect)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if (row, col) in hide_pieces:
                # Desenha o buraco
                x = col * BLOCK_SIZE
                y = (row * BLOCK_SIZE) + UI_HEIGHT
                pygame.draw.rect(screen, GRID_BG, (x, y, BLOCK_SIZE, BLOCK_SIZE), border_radius=10)
                continue
            
            number = board[row][col]
            if number > 0:
                x = col * BLOCK_SIZE
                y = (row * BLOCK_SIZE) + UI_HEIGHT
                
                border_color = None
                if (row, col) in highlight_set:
                    border_color = GREEN_MATCH
                elif (row, col) == hint_to_show:
                    border_color = BLUE_HINT
                
                draw_piece(screen, number, x, y, border_color=border_color)

def draw_ui(screen, score, moves_left, target_score):
    """Desenha a UI (com a nova cor e fonte)."""
    ui_rect = pygame.Rect(0, 0, WIDTH, UI_HEIGHT)
    pygame.draw.rect(screen, GRAY_UI, ui_rect)
    
    score_text = f"Pontos: {score} / {target_score}"
    moves_text = f"Movimentos: {moves_left}"
    
    score_surf = ui_font.render(score_text, True, WHITE)
    moves_surf = ui_font.render(moves_text, True, WHITE)
    
    score_rect = score_surf.get_rect(midleft = (15, UI_HEIGHT // 2))
    moves_rect = moves_surf.get_rect(midright = (WIDTH - 15, UI_HEIGHT // 2))
    
    screen.blit(score_surf, score_rect)
    screen.blit(moves_surf, moves_rect)
    
    pygame.draw.rect(screen, BLUE_HINT, HINT_BUTTON_RECT, border_radius=10)
    hint_text_surf = button_font.render("Dica (?)", True, WHITE)
    hint_text_rect = hint_text_surf.get_rect(center=HINT_BUTTON_RECT.center)
    screen.blit(hint_text_surf, hint_text_rect)

def draw_game_over(screen, won):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    screen.blit(overlay, (0, 0))
    
    text = "Você Venceu!" if won else "Fim de Jogo"
    color = GOLD_WIN if won else RED_ERROR
    text_surf = game_over_font.render(text, True, color)
    text_rect = text_surf.get_rect(center = (WIDTH // 2, HEIGHT // 2))
    screen.blit(text_surf, text_rect)

def update_screen_full(board, score, moves, game_over, won=False, 
                       hint_to_show=None, highlight_set=set(), hide_pieces=set()):
    """Função centralizada para redesenhar tudo estático."""
    screen.fill(BG_COLOR)
    draw_board_static(screen, board, highlight_set, hint_to_show, hide_pieces)
    draw_ui(screen, score, moves, TARGET_SCORE)
    if game_over:
        draw_game_over(screen, won)

def animate_swap(screen, board, pos1, pos2, is_valid, score_data):
    """
    NOVA FUNÇÃO: Anima a troca (e a volta, se for inválida).
    Esta função "pausa" o jogo e roda seu próprio loop.
    """
    r1, c1 = pos1
    r2, c2 = pos2
    n1, n2 = board[r1][c1], board[r2][c2]
    
    x1, y1 = c1 * BLOCK_SIZE, (r1 * BLOCK_SIZE) + UI_HEIGHT
    x2, y2 = c2 * BLOCK_SIZE, (r2 * BLOCK_SIZE) + UI_HEIGHT
    
    start_time = pygame.time.get_ticks()
    
    # Loop de Animação de Troca
    animating = True
    while animating:
        elapsed = pygame.time.get_ticks() - start_time
        t = min(1.0, elapsed / ANIM_SWAP_SPEED) # t vai de 0.0 a 1.0
        
        # Redesenha tudo, mas escondendo as duas peças
        update_screen_full(board, **score_data, hide_pieces={pos1, pos2})
        
        # Calcula a posição atual das duas peças
        current_x1 = lerp(x1, x2, t)
        current_y1 = lerp(y1, y2, t)
        current_x2 = lerp(x2, x1, t)
        current_y2 = lerp(y2, y1, t)
        
        # Desenha as duas peças em suas posições animadas
        draw_piece(screen, n1, current_x1, current_y1)
        draw_piece(screen, n2, current_x2, current_y2)
        
        pygame.display.flip()
        
        if t >= 1.0:
            animating = False
        
        clock.tick(FPS)

    # Animação de volta (se for inválida)
    if not is_valid:
        start_time = pygame.time.get_ticks()
        animating = True
        while animating:
            elapsed = pygame.time.get_ticks() - start_time
            t = min(1.0, elapsed / ANIM_SWAP_SPEED) # t vai de 0.0 a 1.0
            
            # Redesenha tudo, escondendo as duas peças
            update_screen_full(board, **score_data, hide_pieces={pos1, pos2})
            
            # Anima de volta (invertendo início e fim)
            current_x1 = lerp(x2, x1, t)
            current_y1 = lerp(y2, y1, t)
            current_x2 = lerp(x1, x2, t)
            current_y2 = lerp(y1, y2, t)
            
            draw_piece(screen, n1, current_x1, current_y1)
            draw_piece(screen, n2, current_x2, current_y2)
            
            pygame.display.flip()
            
            if t >= 1.0:
                animating = False
            
            clock.tick(FPS)

def animate_fall_and_refill(screen, board_before_drop, falling_moves, 
                            new_pieces, score_data):
    """Anima as peças caindo E as novas peças entrando."""
    start_time = pygame.time.get_ticks()
    
    animating = True
    while animating:
        elapsed = pygame.time.get_ticks() - start_time
        t = min(1.0, elapsed / ANIM_FALL_SPEED) # t vai de 0.0 a 1.0
        
        # Desenha o tabuleiro estático (o estado *antes* da queda)
        update_screen_full(board_before_drop, **score_data)
        
        # Anima as peças caindo
        for number, (r_from, c_from), (r_to, c_to) in falling_moves:
            x = c_from * BLOCK_SIZE
            y_from = (r_from * BLOCK_SIZE) + UI_HEIGHT
            y_to = (r_to * BLOCK_SIZE) + UI_HEIGHT
            
            current_y = lerp(y_from, y_to, t)
            draw_piece(screen, number, x, current_y)
            
        # Anima as novas peças entrando (de cima)
        for number, (r, c) in new_pieces:
            x = c * BLOCK_SIZE
            y_to = (r * BLOCK_SIZE) + UI_HEIGHT
            y_from = y_to - (GRID_ROWS * BLOCK_SIZE) # Começa BEM de cima
            
            current_y = lerp(y_from, y_to, t)
            draw_piece(screen, number, x, current_y)

        pygame.display.flip()
        
        if t >= 1.0:
            animating = False
        
        clock.tick(FPS)


def run_combo_loop(board, score, moves_left):
    """Executa o ciclo de combo, agora com animações."""
    total_score_gain = 0
    matches = find_matches(board)
    
    # Prepara os dados da UI para as funções de animação
    score_data = {
        "score": score, 
        "moves": moves_left, 
        "game_over": False, 
        "won": False, 
        "hint_to_show": None
    }
    
    while matches:
        # Animação de "Flash Verde"
        update_screen_full(board, **score_data, highlight_set=matches)
        pygame.display.flip()
        pygame.time.wait(300) # Pausa rápida para o flash

        score_gain = remove_pieces(board, matches)
        total_score_gain += score_gain
        score_data["score"] += score_gain # Atualiza o score para as próximas animações
        
        # Salva o estado atual (com os buracos)
        board_before_drop = [row.copy() for row in board]
        
        # Calcula as quedas e os preenchimentos
        falling_moves = drop_pieces(board)
        new_pieces = refill_board(board)
        
        # Anima TUDO de uma vez
        animate_fall_and_refill(screen, board_before_drop, falling_moves, 
                                new_pieces, score_data)
        
        # Verifica se as novas peças criaram combos
        matches = find_matches(board)
        
    return total_score_gain

# --- Loop Principal ---

def main():
    running = True
    board = create_board(GRID_ROWS, GRID_COLS)
    
    score = 0
    moves_left = STARTING_MOVES
    game_over = False
    won = False
    
    selected_piece = None 
    is_dragging = False   
    drag_pos = (0, 0)
    hint_to_show = None
    trigger_combo_loop = False 
    
    # Flag para impedir cliques durante uma animação
    game_state = "IDLE" # "IDLE" ou "ANIMATING"

    while running:
        clock.tick(FPS)
        
        # Pacote de dados da UI para as funções de animação
        score_data = {
            "score": score, 
            "moves": moves_left, 
            "game_over": game_over, 
            "won": won, 
            "hint_to_show": hint_to_show
        }
        
        # --- 1. Processamento de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # NÃO processa eventos de mouse se o jogo não estiver IDLE
            if game_over or game_state != "IDLE":
                continue

            # --- Lógica de Clique e Arraste ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_grid_pos = get_clicked_pos(event.pos)
                
                if clicked_grid_pos:
                    selected_piece = clicked_grid_pos
                    is_dragging = True
                    drag_pos = event.pos
                elif HINT_BUTTON_RECT.collidepoint(event.pos):
                    hint_move = find_hint(board)
                    if hint_move:
                        hint_to_show = hint_move[0] 
            
            if event.type == pygame.MOUSEBUTTONUP:
                if is_dragging and selected_piece:
                    release_grid_pos = get_clicked_pos(event.pos)
                    
                    if release_grid_pos and release_grid_pos != selected_piece:
                        r1, c1 = selected_piece
                        r2, c2 = release_grid_pos
                        is_adjacent = abs(r1 - r2) + abs(c1 - c2) == 1
                        
                        if is_adjacent:
                            game_state = "ANIMATING" # Trava o input
                            
                            is_valid = is_swap_valid(board, selected_piece, release_grid_pos)
                            
                            # Roda a animação de troca (e de volta se inválida)
                            animate_swap(screen, board, selected_piece, 
                                         release_grid_pos, is_valid, score_data)
                            
                            if is_valid:
                                swap_pieces(board, selected_piece, release_grid_pos) # Atualiza o dado
                                moves_left -= 1
                                trigger_combo_loop = True
                                hint_to_show = None 
                            
                            game_state = "IDLE" # Libera o input
                                
                is_dragging = False
                selected_piece = None
            
            if event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    drag_pos = event.pos

        # --- 2. Lógica do Jogo (Loop de Combo) ---
        if trigger_combo_loop and game_state == "IDLE":
            game_state = "ANIMATING" # Trava o input
            
            score_gain = run_combo_loop(board, score, moves_left)
            score += score_gain
            
            if moves_left <= 0:
                game_over = True
                won = (score >= TARGET_SCORE)
            
            trigger_combo_loop = False
            game_state = "IDLE" # Libera o input
        
        # --- 3. Desenho (Renderização) ---
        update_screen_full(board, **score_data)
        
        # Desenha a peça sendo arrastada (se estiver)
        if is_dragging and selected_piece:
            r, c = selected_piece
            number = board[r][c]
            draw_piece(screen, number, drag_pos[0] - BLOCK_SIZE // 2, 
                       drag_pos[1] - BLOCK_SIZE // 2, border_color=RED_ERROR)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()