import pygame
import Player
import Grid
import keyboard
import sys
from functools import *
import random
import threading
import socket

pygame.init()

# define the RGB value
# for white, black, pink
# colour respectively.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (248, 200, 220)
DARK_PINK = (169, 92, 104)
RED = (178, 34, 34)

COORDINATES = (0, 0)
RECT_FRAME_WIDTH = 3
RECT_HEIGHT = 50
RECT_WIDTH = 50

# assigning values to X and Y variable. Screen size
X = 1000
Y = 650

COLUMN = 13
ROW = 15

OBSTACLE = ['apple.png', 'books.png', 'pencil.png']
WALLS_LOCATION = [(0, 0), (0, 1), (0, 4), (0, 5), (0, 9), (0, 10), (0, 13), (0, 14), (1, 0), (1, 5), (1, 7)
    , (1, 9), (1, 14), (2, 5), (2, 7), (2, 9), (3, 5), (3, 9), (4, 3), (4, 4), (4, 5), (4, 9), (4, 10), (4, 11)
    , (5, 0), (5, 14), (6, 0), (6, 1), (6, 2), (6, 3), (6, 7), (6, 11), (6, 12), (6, 13), (6, 14), (7, 0), (7, 14)
    , (8, 3), (8, 4), (8, 5), (8, 9), (8, 10), (8, 11), (9, 5), (9, 9), (10, 5), (10, 7), (10, 9), (11, 0), (11, 5)
    , (11, 7), (11, 9), (11, 14), (12, 0), (12, 1), (12, 4), (12, 5), (12, 9), (12, 10), (12, 13), (12, 14)]
CLEAR_SPOTS = [
    (2, 1), (1, 2), (2, 3), (3, 2), (2, 2), (2, 11), (1, 12), (2, 13), (3, 12), (2, 12),
    (10, 1), (9, 2), (10, 3), (11, 2), (10, 2), (10, 11), (9, 12), (10, 13), (11, 12), (10, 12),
    (11, 2), (2, 9), (12, 10), (12, 9)
]

MAX_MSG = 1024
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5555


def creating_window() -> None:
    # creating the pygame window
    # create the display surface object
    # of specific dimension..e(X,Y).
    surface = pygame.display.set_mode((X, Y))
    surface.fill(BLACK)
    pygame.display.set_caption("פוצץ אותה!")
    return None


def creating_grid_list() -> list:
    lst = []
    x, y = COORDINATES
    temp = x
    for i in range(COLUMN):
        lst1 = []
        for j in range(ROW):
            grid = Grid.Grid(x, y)
            lst1.append(grid)
            x += 50
        x = temp
        y += 50
        lst.append(lst1)
    return lst


def create_location_square_list(lst: list, source: list) -> list:
    result = []
    for location in source:
        c, r = location
        result.append(lst[c][r])
    return result


def object_list(lst: list, walls: list) -> list:
    no_obj = create_location_square_list(lst, CLEAR_SPOTS)
    return [y for x in lst for y in x if y not in no_obj and y not in walls]


def loading_obstacle_images() -> list:
    return [pygame.image.load(obj) for obj in OBSTACLE]


def obstacles_on_screen(lst: list) -> None:
    possible_obstacles = loading_obstacle_images()
    wall_img = pygame.image.load('wall1.png')
    walls = create_location_square_list(lst, WALLS_LOCATION)

    for sqr in walls:
        sqr.set_is_object(True)
        sqr.set_is_blowable(False)
        sqr.set_image(wall_img)

    possible_obj_locations = object_list(lst, walls)
    num_to_sample = min(114, len(possible_obj_locations))
    obj_list = random.sample(possible_obj_locations, k=num_to_sample)

    for sqr in obj_list:
        sqr.set_is_object(True)
        sqr.set_image(random.choice(possible_obstacles))


def creating_grid(lst: list) -> None:
    # creating the grid of the game, made of rectangles
    for square in lst:
        for grd in square:
            grd.square_drawing()
    return None


def object_on_screen(object, lst: list) -> None:
    screen = pygame.display.get_surface()
    square = lst[object.get_column()][object.get_row()]
    screen.blit(object.get_icon(), (square.get_pos_x() + 5, square.get_pos_y() + 1))
    return


def managing_bots(lst: list, human_player) -> list[Player.Bot]:
    # bots_data = (עמודה/אנכי, שורה/אופקי, אייקון)
    bots_data = [(2, 12, 'blueBot.png'), (10, 2, 'greenBot.png'), (10, 12, 'orangeBot.png')]
    bots = []
    for col_idx, row_idx, icon in bots_data:
        bots.append(Player.Bot(column=col_idx, row=row_idx, icon=icon, grid_list=lst, other_players=[human_player]))
    return bots


def starting_bot_algorithm(lst: list) -> None:
    for b in lst:
        bot_thread = threading.Thread(target=b.bot_algorithm, daemon=True)
        bot_thread.start()


def update_are_bots_alive(bots: list) -> None:
    for bot in bots:
        bot.was_poisoned()
    return None


def bot_bomb_list(bots: list) -> list:
    lst = []
    for b in bots:
        active_bombs = b.get_active_bombs()
        lst.extend(active_bombs)
    return lst


def drawing_bots(lst: list, bot_lst: list) -> None:
    for bot in bot_lst:
        if bot.is_alive():
            object_on_screen(bot, lst)


def server_socket():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_sock.bind((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print(f"Error binding to {SERVER_IP}:{SERVER_PORT}: {e}")
        return
    server_sock.setblocking(False)
    return server_sock


def multiplayer_game(lst: list) -> None:
    screen = pygame.display.get_surface()
    server = server_socket()


def check_game_over(p1, bot_lst) -> tuple[bool, str]:
    """בדוק אם המשחק נגמר"""
    if not p1.is_alive():
        return True, "Game Over - You Lost!"

    alive_bots = sum(1 for bot in bot_lst if bot.is_alive())
    if alive_bots == 0:
        return True, "You Win! Press ESC to exit"

    return False, ""


def display_game_over_message(message: str) -> None:
    """הצג הודעת סוף משחק"""
    screen = pygame.display.get_surface()
    font = pygame.font.Font(None, 60)
    text = font.render(message, True, RED)
    text_rect = text.get_rect(center=(X // 2, Y // 2))

    # רקע שחור מאחורי הטקסט
    background_rect = text_rect.inflate(40, 40)
    pygame.draw.rect(screen, BLACK, background_rect)
    pygame.draw.rect(screen, WHITE, background_rect, 3)

    screen.blit(text, text_rect)


def solo_game_loop(lst: list) -> None:
    p1 = Player.Player(grid_list=lst)
    moving = partial(on_key_event, p=p1, lst=lst)
    keyboard.hook(moving)

    bot_lst = managing_bots(lst, p1)

    # הוסף את הבוטים לרשימת השחקנים האחרים של כל בוט
    for bot in bot_lst:
        bot._other_players = [p1] + [b for b in bot_lst if b != bot]

    # התחל את הבוטים רק אחרי שהכל מוכן
    starting_bot_algorithm(bot_lst)

    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    running = True
    game_over = False
    game_over_message = ""
    game_over_time = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # בדוק אם המשחק נגמר
        if not game_over:
            game_over, game_over_message = check_game_over(p1, bot_lst)
            if game_over:
                game_over_time = pygame.time.get_ticks()
                print(game_over_message)

        screen.fill(BLACK)
        pygame.draw.rect(screen, PINK, (752, 0, 250, 650))

        # צייר כל הגריד
        for col in lst:
            for sqr in col:
                sqr.square_drawing()

        # עדכן וצייר שחקן
        if p1.is_alive():
            p1.was_poisoned()
            object_on_screen(p1, lst)

        # עדכן וצייר בוטים
        update_are_bots_alive(bot_lst)
        drawing_bots(lst, bot_lst)

        # צייר פצצות
        all_active_bombs = bot_bomb_list(bot_lst)
        all_active_bombs.extend(p1.get_active_bombs())
        for bomb in all_active_bombs:
            object_on_screen(bomb, lst)

        # הצג הודעת game over
        if game_over:
            display_game_over_message(game_over_message)

        pygame.display.flip()
        clock.tick(60)

    # ניקוי
    for b in bot_lst:
        b.stop()
    keyboard.unhook_all()
    return None


def screen_loop() -> None:
    # game_mode = input("If you want to play solo press: 1\nIf you want to play multiplayer press: 2")
    game_mode = "1"

    creating_window()
    screen = pygame.display.get_surface()
    lst = creating_grid_list()
    creating_grid(lst)
    pygame.draw.rect(screen, PINK, (752, 0, 250, 650))
    obstacles_on_screen(lst)

    if game_mode == "1":
        solo_game_loop(lst)
    elif game_mode == "2":
        multiplayer_game(lst)

    # ניקוי אחרי סיום
    keyboard.unhook_all()
    pygame.quit()
    sys.exit()


def on_key_event(event, p: Player.Player, lst: list) -> None:
    if not p.is_alive():
        return
    if event.event_type == keyboard.KEY_DOWN:
        lst[p.get_column()][p.get_row()].square_drawing()
        if event.name == 'up':
            p.up()
        elif event.name == 'down':
            p.down()
        elif event.name == 'left':
            p.left()
        elif event.name == 'right':
            p.right()
        elif event.name == 'space':
            p.space()
        elif event.name == 'esc':
            print("See you again later")
            keyboard.unhook_all()
            pygame.quit()
            sys.exit()


def main():
    screen_loop()


if __name__ == "__main__":
    main()  