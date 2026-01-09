import pygame
import time
import Grid

SLEEP_TIME = 1.5
RECT_FRAME_WIDTH = 3
RECT_HEIGHT = 50
RECT_WIDTH = 50
BLACK = (0, 0, 0)


class Bomb:

    _cached_icon = None

    def __init__(self, column: int = 0, row: int = 0, grid_list: list = None, active_bombs_list: list = None) -> None:
        self._row = row
        self._column = column

        if Bomb._cached_icon is None:
            try:
                Bomb._cached_icon = pygame.image.load("bomb.png")
            except:
                # יצירת משטח זמני אם הקובץ חסר כדי למנוע קריסה
                Bomb._cached_icon = pygame.Surface((40, 40))

        self._icon = Bomb._cached_icon
        self._power = 1
        self._grid_list = grid_list
        self._active_bombs_list = active_bombs_list
        self._screen = pygame.display.get_surface()
        self._running = True


    def get_icon(self):
        return self._icon

    def get_column(self) -> int:
        return self._column

    def get_row(self) -> int:
        return self._row

    def stop(self):
        """Signals the bomb to stop immediately."""
        self._running = False

    def explosion_list(self) -> list:
        explode = [(self._column, self._row)]
        hit_a_wall = [False for _ in range(4)]
        for i in range(1, self._power + 2):

            if self._column > 0 and self._column >= i and not hit_a_wall[0]:
                if not self._grid_list[self._column - i][self._row].get_is_blowable():
                    hit_a_wall[0] = True
                else:
                    explode.append((self._column - i, self._row))
                    if self._grid_list[self._column - i][self._row].get_is_object():
                        hit_a_wall[0] = True

            if self._column + i < 13 and not hit_a_wall[1]:
                if not self._grid_list[self._column + i][self._row].get_is_blowable():
                    hit_a_wall[1] = True
                else:
                    explode.append((self._column + i, self._row))
                    if self._grid_list[self._column + i][self._row].get_is_object():
                        hit_a_wall[1] = True

            if self._row > 0 and self._row >= i and not hit_a_wall[2]:
                if not self._grid_list[self._column][self._row - i].get_is_blowable():
                    hit_a_wall[2] = True
                else:
                    explode.append((self._column, self._row - i))
                    if self._grid_list[self._column][self._row - i].get_is_object():
                        hit_a_wall[2] = True

            if self._row + i < 15 and not hit_a_wall[3]:
                if not self._grid_list[self._column][self._row + i].get_is_blowable():
                    hit_a_wall[3] = True
                else:
                    explode.append((self._column, self._row + i))
                    if self._grid_list[self._column][self._row + i].get_is_object():
                        hit_a_wall[3] = True
        return explode

    def __explosion(self, explode: list) -> None:
        for col, row in explode:
            sqr = self._grid_list[col][row]
            sqr.set_explosion()
            self.__square_drawing(sqr)
        return None

    def __end_of_explosion(self, explode: list) -> None:
        for col, row in explode:
            sqr = self._grid_list[col][row]
            sqr.end_of_explosion()
            self.__square_drawing(sqr)
        return None

    def __square_drawing(self, square: Grid.Grid) -> None:
        if not self._running: return
        try:
            screen = pygame.display.get_surface()
            if screen is None: return

            pygame.draw.rect(screen, BLACK, (square.get_pos_x(), square.get_pos_y(), RECT_WIDTH, RECT_HEIGHT),
                             width=RECT_FRAME_WIDTH)
            pygame.draw.rect(screen, square.get_colour(), (
                square.get_pos_x() + RECT_FRAME_WIDTH, square.get_pos_y() + RECT_FRAME_WIDTH,
                RECT_WIDTH - (2 * RECT_FRAME_WIDTH),
                RECT_HEIGHT - (2 * RECT_FRAME_WIDTH)))
        except:
            # If drawing fails (e.g. video system closed), just stop the thread
            self.stop()

    def blow_up(self):
        sqr = self._grid_list[self._column][self._row]
        sqr.set_image(None) # וודא שאין תמונת מכשול ישנה על המשבצת של הפצצה
        sqr.set_is_object(True)
        time.sleep(SLEEP_TIME)
        explode = self.explosion_list()
        self.__explosion(explode)
        if self in self._active_bombs_list:
            self._active_bombs_list.remove(self)
        time.sleep(SLEEP_TIME - 1)
        self.__end_of_explosion(explode)


        return None
