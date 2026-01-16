
import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (248, 200, 220)
RED = (178, 34, 34)

RECT_FRAME_WIDTH = 3
RECT_HEIGHT = 50
RECT_WIDTH = 50

class Grid:

    def __init__(self, pos_x: int = 0, pos_y: int = 0, colour:tuple = WHITE
                 , is_object: bool = False, is_poisoned:bool = False, is_blowable = True) -> None:
        self._pos_x = pos_x
        self._pos_y = pos_y
        self._colour = colour
        self._is_object = is_object
        self._is_poisoned = is_poisoned
        self._is_blowable = is_blowable
        self._image = None  # הוספת משתנה לתמונה

    def set_image(self, image):
        self._image = image

    def get_pos_x(self) -> int:
        return self._pos_x

    def get_pos_y(self) -> int:
        return self._pos_y

    def get_colour(self) -> tuple:
        return self._colour

    def set_is_object(self, is_object: bool) -> None:
        self._is_object = is_object
        return None

    def get_is_object(self) -> bool:
        return self._is_object

    def set_is_blowable(self, is_blowable: bool) -> None:
        self._is_blowable = is_blowable
        return None

    def get_is_blowable(self) -> bool:
        return self._is_blowable

    def set_explosion(self) -> None:
        self._colour = RED
        self.__set_is_poisoned(True)
        if self._is_blowable:
            self._is_object = False
            self._image = None  # התיקון: מוחק את התמונה מהזיכרון של הריבוע
        return None

    def end_of_explosion(self) -> None:
        self._colour = WHITE
        self.__set_is_poisoned(False)
        return None

    def __set_is_poisoned(self, value: bool) -> None:
        self._is_poisoned = value
        return None

    def get_is_poisoned(self) -> bool:
        return self._is_poisoned

    def square_drawing(self) -> None:
        screen = pygame.display.get_surface()
        # ציור הרקע של הריבוע
        pygame.draw.rect(screen, BLACK, (self._pos_x, self._pos_y, RECT_WIDTH, RECT_HEIGHT), width=RECT_FRAME_WIDTH)
        pygame.draw.rect(screen, self._colour, (
            self._pos_x + RECT_FRAME_WIDTH, self._pos_y + RECT_FRAME_WIDTH,
            RECT_WIDTH - (2 * RECT_FRAME_WIDTH),
            RECT_HEIGHT - (2 * RECT_FRAME_WIDTH)))

        # אם יש תמונה (מכשול/קיר), נצייר אותה
        if self._image and self._is_object:
            screen.blit(self._image, (self._pos_x + 5, self._pos_y + 2))

    def __str__(self):
        return f"({self._pos_x}, {self._pos_y}, {self._is_object})"
