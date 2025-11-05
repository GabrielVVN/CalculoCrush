import pygame
import random
import os
import math

# --- Constantes de Jogo ---
GRID_ROWS = 8
GRID_COLS = 8
BLOCK_SIZE = 80
UI_HEIGHT = 150 # AUMENTADO de 100 para 150
GAME_WIDTH = GRID_COLS * BLOCK_SIZE # 640
GAME_HEIGHT = (GRID_ROWS * BLOCK_SIZE) + UI_HEIGHT # 640 + 150 = 790

# --- NOVO: Constantes da Janela ---
# Adiciona "padding" (preenchimento) ao redor da área de jogo
PADDING_X = 100
PADDING_Y = 50
WINDOW_WIDTH = GAME_WIDTH + (PADDING_X * 2)   # 640 + 200 = 840
WINDOW_HEIGHT = GAME_HEIGHT + (PADDING_Y * 2) # 790 + 100 = 890

# --- NOVO: Offsets (Deslocamento) ---
# Onde o canto superior esquerdo do JOGO começa dentro da JANELA
GAME_AREA_X_OFFSET = PADDING_X
GAME_AREA_Y_OFFSET = PADDING_Y

FPS = 60 

# --- Paleta de Cores Moderna ---
WHITE = (230, 230, 230)
GRAY_UI = (30, 30, 30)
BG_COLOR = (20, 20, 20)
GRID_BG = (40, 40, 40)
WINDOW_BG_COLOR = (15, 15, 15) # Fundo escuro da janela

COLOR_1_3 = (60, 100, 160)
COLOR_4_6 = (60, 160, 100)
COLOR_7_9 = (180, 140, 50)
COLOR_PRODUCT = (140, 70, 160)

RED_ERROR = (220, 20, 60)
GOLD_WIN = (255, 215, 0)
GREEN_MATCH = (0, 255, 0)
BLUE_HINT = (0, 100, 255)

# --- Constantes de UI (Re-posicionadas) ---
# Posições relativas ao JOGO (0,0), não à JANELA
HINT_BUTTON_RECT = pygame.Rect(GAME_WIDTH // 2 - 60, 90, 120, 40) # (y=90)

# Constantes de Animação
ANIM_SWAP_SPEED = 300
ANIM_FALL_SPEED = 500

# Configurações do Nível 1
STARTING_MOVES = 20
TARGET_SCORE = 300

# Lista de números fáceis
EASY_NUMBERS_LIST = (
    [1, 2, 3] * 15 + [4, 5] * 7 + [6, 7, 8, 9] * 4 +
    [4, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 36] * 2
)
random.shuffle(EASY_NUMBERS_LIST)

# --- Inicialização do Pygame ---
pygame.init()
pygame.font.init()
# --- ATUALIZADO: Usa o tamanho da JANELA ---
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("CalculoCrush")
clock = pygame.time.Clock()

# --- NOVO: Surface do Jogo ---
# Criamos uma "tela" separada para o jogo.
# Vamos desenhar o jogo nela, e depois desenhar ela na janela principal.
game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

# --- Carregamento de Fonte Customizada ---
ASSETS_PATH = "assets"
FONT_PATH = os.path.join(ASSETS_PATH, "font.ttf")

try:
    number_font = pygame.font.Font(FONT_PATH, 40)
    ui_font = pygame.font.Font(FONT_PATH, 30)
    game_over_font = pygame.font.Font(FONT_PATH, 60)
    button_font = pygame.font.Font(FONT_PATH, 25)
    # NOVO: Fonte do Título e "Enfeites"
    title_font = pygame.font.Font(FONT_PATH, 50)
    small_font = pygame.font.Font(FONT_PATH, 16)
except FileNotFoundError:
    print(f"Erro: Fonte '{FONT_PATH}' não encontrada. Usando fonte padrão.")
    # Fallback...
    number_font = pygame.font.SysFont(None, 50)
    ui_font = pygame.font.SysFont(None, 40)
    game_over_font = pygame.font.SysFont(None, 70)
    button_font = pygame.font.SysFont(None, 30)
    title_font = pygame.font.SysFont(None, 60)
    small_font = pygame.font.SysFont(None, 20)

# --- Funções de Lógica ---
def create_board(rows, cols):
    board = []
    for row in range(rows):
        board.append([])
        for col in range(cols):
            board[row].append(random.choice(EASY_NUMBERS_LIST))
    return board

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

def get_clicked_pos(pos):
    """
    ATUALIZADO: Converte (x, y) da JANELA para (linha, coluna) da grade.
    """
    x, y = pos
    
    # 1. Subtrai o offset para ter a coordenada relativa ao JOGO
    x -= GAME_AREA_X_OFFSET
    y -= GAME_AREA_Y_OFFSET

    # 2. Verifica se o clique foi dentro da área do JOGO
    if x < 0 or y < 0 or x >= GAME_WIDTH or y >= GAME_HEIGHT:
        return None # Clicou fora da área do jogo (nos enfeites)

    # 3. Subtrai o offset da UI (agora relativo ao jogo)
    y_adjusted = y - UI_HEIGHT
    if y_adjusted < 0: 
        return None # Clicou na UI (mas dentro do game_surface)

    # 4. Calcula a grade
    row = y_adjusted // BLOCK_SIZE
    col = x // BLOCK_SIZE
    if row >= GRID_ROWS or col >= GRID_COLS or row < 0 or col < 0:
        return None
    return (row, col)

def drop_pieces(board):
    moves = []
    for c in range(GRID_COLS):
        drop_to_row = GRID_ROWS - 1
        for r in range(GRID_ROWS - 1, -1, -1):
            if board[r][c] > 0:
                number = board[r][c]
                if r != drop_to_row:
                    moves.append((number, (r, c), (drop_to_row, c)))
                    board[drop_to_row][c] = number
                    board[r][c] = 0
                drop_to_row -= 1
    return moves

def refill_board(board):
    new_pieces = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if board[r][c] == 0:
                number = random.choice(EASY_NUMBERS_LIST)
                board[r][c] = number
                new_pieces.append((number, (r, c)))
    return new_pieces

def is_swap_valid(board, pos1, pos2):
    swap_pieces(board, pos1, pos2)
    matches = find_matches(board)
    swap_pieces(board, pos1, pos2)
    return len(matches) > 0

# --- CORREÇÃO AQUI: Função LERP Adicionada ---
def lerp(a, b, t):
    """Interpolação Linear: de 'a' para 'b' em 't' (0.0 a 1.0)"""
    return a + (b - a) * t
# --- FIM DA CORREÇÃO ---

# --- Funções de Desenho ---

def get_piece_color(number):
    if number == 0: return GRID_BG
    elif number < 4: return COLOR_1_3
    elif number < 7: return COLOR_4_6
    elif number < 10: return COLOR_7_9
    else: return COLOR_PRODUCT

def draw_piece(surface, number, x, y, size=BLOCK_SIZE, border_color=None):
    """Desenha uma peça na SURFACE especificada."""
    piece_rect = pygame.Rect(x, y, size, size)
    color = get_piece_color(number)
    pygame.draw.rect(surface, color, piece_rect, border_radius=10)
    
    text_surface = number_font.render(str(number), True, WHITE)
    text_rect = text_surface.get_rect(center=piece_rect.center)
    surface.blit(text_surface, text_rect)
    
    if border_color:
        pygame.draw.rect(surface, border_color, piece_rect, 5, border_radius=10)

def draw_board_static(surface, board, highlight_set=set(), hint_to_show=None, 
                      hide_pieces=set()):
    """Desenha o tabuleiro estático na SURFACE."""
    # Desenha o fundo da grade (agora relativo ao game_surface)
    grid_rect = pygame.Rect(0, UI_HEIGHT, GAME_WIDTH, GAME_HEIGHT - UI_HEIGHT)
    pygame.draw.rect(surface, BG_COLOR, grid_rect)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # Coordenadas relativas ao game_surface
            x = col * BLOCK_SIZE
            y = (row * BLOCK_SIZE) + UI_HEIGHT
            
            if (row, col) in hide_pieces:
                pygame.draw.rect(surface, GRID_BG, (x, y, BLOCK_SIZE, BLOCK_SIZE), border_radius=10)
                continue
            
            number = board[row][col]
            if number > 0:
                border_color = None
                if (row, col) in highlight_set:
                    border_color = GREEN_MATCH
                elif (row, col) == hint_to_show:
                    border_color = BLUE_HINT
                
                draw_piece(surface, number, x, y, border_color=border_color)

def draw_ui(surface, score, moves_left, target_score):
    """ATUALIZADO: Desenha a UI (com Título) na SURFACE."""
    ui_rect = pygame.Rect(0, 0, GAME_WIDTH, UI_HEIGHT)
    pygame.draw.rect(surface, GRAY_UI, ui_rect)
    
    # 1. Título
    title_surf = title_font.render("CalculoCrush", True, WHITE)
    title_rect = title_surf.get_rect(center=(GAME_WIDTH // 2, 45))
    surface.blit(title_surf, title_rect)
    
    # 2. Score (agora mais baixo)
    score_text = f"Pontos: {score} / {target_score}"
    score_surf = ui_font.render(score_text, True, WHITE)
    score_rect = score_surf.get_rect(midleft=(25, 105)) # y=105
    surface.blit(score_surf, score_rect)
    
    # 3. Movimentos (agora mais baixo)
    moves_text = f"Movimentos: {moves_left}"
    moves_surf = ui_font.render(moves_text, True, WHITE)
    moves_rect = moves_surf.get_rect(midright=(GAME_WIDTH - 25, 105)) # y=105
    surface.blit(moves_surf, moves_rect)
    
    # 4. Botão de Dica (centralizado)
    pygame.draw.rect(surface, BLUE_HINT, HINT_BUTTON_RECT, border_radius=10)
    hint_text_surf = button_font.render("Dica", True, WHITE)
    hint_text_rect = hint_text_surf.get_rect(center=HINT_BUTTON_RECT.center)
    surface.blit(hint_text_surf, hint_text_rect)

def draw_game_over(surface, won):
    """Desenha o game over na SURFACE."""
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    surface.blit(overlay, (0, 0))
    
    text = "Você Venceu!" if won else "Fim de Jogo"
    color = GOLD_WIN if won else RED_ERROR
    text_surf = game_over_font.render(text, True, color)
    # Centraliza na ÁREA DE JOGO
    text_rect = text_surf.get_rect(center=(GAME_WIDTH // 2, GAME_HEIGHT // 2))
    surface.blit(text_surf, text_rect)

# --- NOVO: Função para desenhar os "Enfeites" ---
def draw_window_decorations(screen):
    """Desenha o fundo da JANELA e os enfeites."""
    screen.fill(WINDOW_BG_COLOR)
    
    # Desenha um "frame" elegante ao redor da área de jogo
    frame_rect = pygame.Rect(
        GAME_AREA_X_OFFSET - 4, 
        GAME_AREA_Y_OFFSET - 4, 
        GAME_WIDTH + 8, 
        GAME_HEIGHT + 8
    )
    pygame.draw.rect(screen, GRAY_UI, frame_rect, 4, border_radius=10)
    
    # Adiciona texto de "crédito" nos enfeites
    credit_text = small_font.render("CalculoCrush | 2025", True, GRAY_UI)
    credit_rect = credit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - PADDING_Y // 2))
    screen.blit(credit_text, credit_rect)

def update_game_surface(surface, board, score, moves, game_over, won=False, 
                       hint_to_show=None, highlight_set=set(), hide_pieces=set()):
    """
    ATUALIZADO: Função centralizada para redesenhar tudo na GAME_SURFACE.
    """
    surface.fill(BG_COLOR) # Preenche o fundo do jogo
    draw_board_static(surface, board, highlight_set, hint_to_show, hide_pieces)
    draw_ui(surface, score, moves, TARGET_SCORE)
    if game_over:
        draw_game_over(surface, won)

# --- Funções de Animação ---

def animate_swap(surface, board, pos1, pos2, is_valid, score_data):
    """Anima a troca na GAME_SURFACE."""
    r1, c1 = pos1
    r2, c2 = pos2
    n1, n2 = board[r1][c1], board[r2][c2]
    
    # Coordenadas relativas ao game_surface
    x1, y1 = c1 * BLOCK_SIZE, (r1 * BLOCK_SIZE) + UI_HEIGHT
    x2, y2 = c2 * BLOCK_SIZE, (r2 * BLOCK_SIZE) + UI_HEIGHT
    
    start_time = pygame.time.get_ticks()
    
    animating = True
    while animating:
        elapsed = pygame.time.get_ticks() - start_time
        t = min(1.0, elapsed / ANIM_SWAP_SPEED)
        
        # Redesenha o jogo estático (no game_surface)
        update_game_surface(surface, board, **score_data, hide_pieces={pos1, pos2})
        
        current_x1 = lerp(x1, x2, t)
        current_y1 = lerp(y1, y2, t)
        current_x2 = lerp(x2, x1, t)
        current_y2 = lerp(y2, y1, t)
        
        # Desenha as peças animadas (no game_surface)
        draw_piece(surface, n1, current_x1, current_y1)
        draw_piece(surface, n2, current_x2, current_y2)
        
        # --- ATUALIZAÇÃO IMPORTANTE ---
        # Blit o game_surface na tela principal
        screen.blit(surface, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET))
        pygame.display.flip() # Atualiza a tela inteira
        
        if t >= 1.0: animating = False
        clock.tick(FPS)

    if not is_valid:
        start_time = pygame.time.get_ticks()
        animating = True
        while animating:
            elapsed = pygame.time.get_ticks() - start_time
            t = min(1.0, elapsed / ANIM_SWAP_SPEED)
            
            update_game_surface(surface, board, **score_data, hide_pieces={pos1, pos2})
            
            current_x1 = lerp(x2, x1, t)
            current_y1 = lerp(y2, y1, t)
            current_x2 = lerp(x1, x2, t)
            current_y2 = lerp(y1, y2, t)
            
            draw_piece(surface, n1, current_x1, current_y1)
            draw_piece(surface, n2, current_x2, current_y2)
            
            screen.blit(surface, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET))
            pygame.display.flip()
            
            if t >= 1.0: animating = False
            clock.tick(FPS)

def animate_fall_and_refill(surface, board_before_drop, falling_moves, 
                            new_pieces, score_data):
    """Anima a queda na GAME_SURFACE."""
    start_time = pygame.time.get_ticks()
    
    animating = True
    while animating:
        elapsed = pygame.time.get_ticks() - start_time
        t = min(1.0, elapsed / ANIM_FALL_SPEED)
        
        # Desenha o tabuleiro estático (antes da queda)
        update_game_surface(surface, board_before_drop, **score_data)
        
        # Anima peças caindo
        for number, (r_from, c_from), (r_to, c_to) in falling_moves:
            x = c_from * BLOCK_SIZE
            y_from = (r_from * BLOCK_SIZE) + UI_HEIGHT
            y_to = (r_to * BLOCK_SIZE) + UI_HEIGHT
            current_y = lerp(y_from, y_to, t)
            draw_piece(surface, number, x, current_y)
            
        # Anima novas peças entrando
        for number, (r, c) in new_pieces:
            x = c * BLOCK_SIZE
            y_to = (r * BLOCK_SIZE) + UI_HEIGHT
            y_from = y_to - (GRID_ROWS * BLOCK_SIZE)
            current_y = lerp(y_from, y_to, t)
            draw_piece(surface, number, x, current_y)

        screen.blit(surface, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET))
        pygame.display.flip()
        
        if t >= 1.0: animating = False
        clock.tick(FPS)

def run_combo_loop(surface, board, score, moves_left):
    """Executa o combo, desenhando na GAME_SURFACE."""
    total_score_gain = 0
    matches = find_matches(board)
    
    score_data = {
        "score": score, "moves": moves_left, "game_over": False, 
        "won": False, "hint_to_show": None
    }
    
    while matches:
        # Flash Verde
        update_game_surface(surface, board, **score_data, highlight_set=matches)
        screen.blit(surface, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET))
        pygame.display.flip()
        pygame.time.wait(300)

        score_gain = remove_pieces(board, matches)
        total_score_gain += score_gain
        score_data["score"] += score_gain
        
        board_before_drop = [row.copy() for row in board]
        falling_moves = drop_pieces(board)
        new_pieces = refill_board(board)
        
        # Anima a queda (que também atualiza a tela)
        animate_fall_and_refill(surface, board_before_drop, falling_moves, 
                                new_pieces, score_data)
        
        matches = find_matches(board)
        
    return total_score_gain

# --- Loop Principal (ATUALIZADO) ---

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
    game_state = "IDLE" 

    while running:
        clock.tick(FPS)
        
        score_data = {
            "score": score, "moves": moves_left, "game_over": game_over, 
            "won": won, "hint_to_show": hint_to_show
        }
        
        # --- 1. Processamento de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
            
            if game_over or game_state != "IDLE": continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_grid_pos = get_clicked_pos(event.pos)
                
                # --- ATUALIZADO: Verifica o clique no botão de Dica ---
                # Ajusta as coordenadas do mouse para checar contra o HINT_RECT
                adj_x = event.pos[0] - GAME_AREA_X_OFFSET
                adj_y = event.pos[1] - GAME_AREA_Y_OFFSET
                
                if clicked_grid_pos:
                    selected_piece = clicked_grid_pos
                    is_dragging = True
                    drag_pos = event.pos
                elif HINT_BUTTON_RECT.collidepoint((adj_x, adj_y)):
                    hint_move = find_hint(board)
                    if hint_move:
                        hint_to_show = hint_move[0] 
            
            if event.type == pygame.MOUSEBUTTONUP:
                if is_dragging and selected_piece:
                    release_grid_pos = get_clicked_pos(event.pos)
                    
                    if release_grid_pos and release_grid_pos != selected_piece:
                        is_adjacent = abs(selected_piece[0] - release_grid_pos[0]) + \
                                      abs(selected_piece[1] - release_grid_pos[1]) == 1
                        
                        if is_adjacent:
                            game_state = "ANIMATING"
                            is_valid = is_swap_valid(board, selected_piece, release_grid_pos)
                            
                            # ATUALIZADO: Passa a 'game_surface' para a animação
                            animate_swap(game_surface, board, selected_piece, 
                                         release_grid_pos, is_valid, score_data)
                            
                            if is_valid:
                                swap_pieces(board, selected_piece, release_grid_pos)
                                moves_left -= 1
                                trigger_combo_loop = True
                                hint_to_show = None 
                            game_state = "IDLE"
                                
                is_dragging = False
                selected_piece = None
            
            if event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    drag_pos = event.pos

        # --- 2. Lógica do Jogo (Loop de Combo) ---
        if trigger_combo_loop and game_state == "IDLE":
            game_state = "ANIMATING"
            # ATUALIZADO: Passa a 'game_surface'
            score_gain = run_combo_loop(game_surface, board, score, moves_left)
            score += score_gain
            
            if moves_left <= 0:
                game_over = True
                won = (score >= TARGET_SCORE)
            
            trigger_combo_loop = False
            game_state = "IDLE"
        
        # --- 3. Desenho (Renderização) ---
        
        # Só redesenha a tela estática se estiver IDLE
        if game_state == "IDLE":
            # 1. Desenha os "enfeites" da janela
            draw_window_decorations(screen)
            
            # 2. Desenha o jogo estático na surface
            update_game_surface(game_surface, board, **score_data)
            
            # 3. Blit a surface do jogo na tela principal
            screen.blit(game_surface, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET))
            
            # 4. Desenha a peça sendo arrastada (na tela principal)
            if is_dragging and selected_piece:
                r, c = selected_piece
                number = board[r][c]
                # Desenha na posição do mouse
                draw_piece(screen, number, drag_pos[0] - BLOCK_SIZE // 2, 
                           drag_pos[1] - BLOCK_SIZE // 2, border_color=RED_ERROR)

            # 5. Atualiza a tela
            pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()