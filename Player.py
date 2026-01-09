import pygame
import threading
import random
import time
from collections import deque

# קבועים לניהול קצב המשחק
TIME_SLEEP = 0.3


class Player:
    def __init__(self, row: int = 2, column: int = 2, icon: str = "pinkBot.png", grid_list: list = None):
        self._row = row
        self._column = column
        self._icon = pygame.image.load(icon)
        self._is_alive = True
        self._grid_list = grid_list
        self._screen = pygame.display.get_surface()
        self._active_bombs = []
        self._max_bombs = 2

    def get_icon(self) -> pygame.surface.Surface:
        return self._icon

    def get_row(self) -> int:
        return self._row

    def get_column(self) -> int:
        return self._column

    def get_active_bombs(self) -> list:
        return self._active_bombs

    def is_alive(self) -> bool:
        return self._is_alive

    def right(self) -> None:
        if self._row < 14:
            if not self._grid_list[self._column][self._row + 1].get_is_object():
                self._row += 1

    def left(self) -> None:
        if self._row > 0:
            if not self._grid_list[self._column][self._row - 1].get_is_object():
                self._row -= 1

    def up(self) -> None:
        if self._column > 0:
            if not self._grid_list[self._column - 1][self._row].get_is_object():
                self._column -= 1

    def down(self) -> None:
        if self._column < 12:
            if not self._grid_list[self._column + 1][self._row].get_is_object():
                self._column += 1

    def space(self) -> None:
        # ייבוא מקומי כדי למנוע circular import
        import Bomb

        if len(self._active_bombs) >= self._max_bombs:
            return None
        bomb = Bomb.Bomb(self._column, self._row, grid_list=self._grid_list, active_bombs_list=self._active_bombs)
        self._active_bombs.append(bomb)
        t = threading.Thread(target=bomb.blow_up, daemon=True)
        t.start()

    def was_poisoned(self) -> None:
        if self._grid_list[self._column][self._row].get_is_poisoned():
            self._is_alive = False


class Bot(Player):
    def __init__(self, row: int, column: int, icon: str = "blueBot.png", grid_list: list = None,
                 other_players: list = None):
        super().__init__(row, column, icon, grid_list)
        self._running = True
        self._other_players = other_players if other_players else []
        self._max_bombs = 1
        self._last_bomb_time = 0

    def stop(self):
        self._running = False

    def _who_is_around(self, c: int, r: int) -> list:
        """מחזיר רשימת שכנים אפשריים"""
        lst = []
        if c > 0:
            lst.append((c - 1, r))
        if c < 12:
            lst.append((c + 1, r))
        if r > 0:
            lst.append((c, r - 1))
        if r < 14:
            lst.append((c, r + 1))
        return lst

    def get_danger_zones(self) -> set:
        """מזהה את כל האזורים המסוכנים במפה"""
        danger = set()

        # אזורי פיצוץ קיימים
        for c in range(len(self._grid_list)):
            for r in range(len(self._grid_list[0])):
                if self._grid_list[c][r].get_is_poisoned():
                    danger.add((c, r))

        # אזורי פצצות פעילות - שלי
        for b in self._active_bombs:
            danger.update(b.explosion_list())

        # אזורי פצצות פעילות - של שחקנים אחרים
        for p in self._other_players:
            if p.is_alive():
                for b in p.get_active_bombs():
                    danger.update(b.explosion_list())

        return danger

    def _get_potential_blast_zone(self, c: int, r: int) -> set:
        """מחזיר את אזור הפיצוץ הפוטנציאלי אם נניח פצצה במיקום (c, r)"""
        blast_zone = {(c, r)}

        # בדוק בכל 4 הכיוונים
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            for i in range(1, 3):  # טווח פצצה = 2
                nc, nr = c + (dc * i), r + (dr * i)
                if 0 <= nc < 13 and 0 <= nr < 15:
                    blast_zone.add((nc, nr))
                    # עצור אם פגשנו קיר
                    if self._grid_list[nc][nr].get_is_object() and not self._grid_list[nc][nr].get_is_blowable():
                        break
                    # עצור אם פגשנו מכשול שניתן לפוצץ
                    if self._grid_list[nc][nr].get_is_object():
                        break

        return blast_zone

    def _has_escape_route(self, bomb_pos: tuple) -> tuple[bool, tuple | None]:
        """
        בודק אם יש מסלול בריחה אם נניח פצצה ב-bomb_pos
        מחזיר: (יש מסלול בריחה?, המקום הבטוח הקרוב ביותר)
        """
        # חשב את אזור הסכנה העתידי (כולל הפצצה החדשה)
        future_danger = self.get_danger_zones()
        potential_blast = self._get_potential_blast_zone(bomb_pos[0], bomb_pos[1])
        future_danger.update(potential_blast)

        # BFS למציאת מקום בטוח
        queue = deque([bomb_pos])
        visited = {bomb_pos}
        parent = {bomb_pos: None}

        while queue:
            curr = queue.popleft()

            # מצאנו מקום בטוח מחוץ לאזור הפיצוץ!
            if curr not in future_danger:
                # בנה את המסלול
                path = []
                node = curr
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()

                # המקום הבטוח הראשון שנגיע אליו
                return True, path[-1] if len(path) > 1 else curr

            # המשך לחפש
            for neighbor in self._who_is_around(curr[0], curr[1]):
                if neighbor not in visited:
                    nc, nr = neighbor
                    sqr = self._grid_list[nc][nr]

                    # מותר לעבור דרך ריבועים ריקים או פיצוצים קיימים
                    if not sqr.get_is_object() or sqr.get_is_poisoned():
                        visited.add(neighbor)
                        parent[neighbor] = curr
                        queue.append(neighbor)

        return False, None

    def _is_safe_spot(self, pos: tuple) -> bool:
        """בודק אם מיקום בטוח"""
        c, r = pos
        sqr = self._grid_list[c][r]

        # לא בטוח אם יש שם אובייקט (חוץ מאם זה פיצוץ)
        if sqr.get_is_object() and not sqr.get_is_poisoned():
            return False

        # לא בטוח אם זה אזור סכנה
        danger = self.get_danger_zones()
        if pos in danger:
            return False

        return True

    def _find_safe_path(self, start: tuple) -> tuple | None:
        """מוצא את הצעד הבא למקום בטוח הכי קרוב"""
        queue = deque([start])
        visited = {start}
        parent = {start: None}
        danger = self.get_danger_zones()

        while queue:
            curr = queue.popleft()

            # אם מצאנו מקום בטוח - החזר את הצעד הראשון לשם
            if curr not in danger:
                path = []
                node = curr
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                return path[1] if len(path) > 1 else None

            # חפש שכנים
            for neighbor in self._who_is_around(curr[0], curr[1]):
                if neighbor not in visited:
                    nc, nr = neighbor
                    sqr = self._grid_list[nc][nr]

                    # מותר לעבור דרך ריבועים ריקים או פיצוצים
                    if not sqr.get_is_object() or sqr.get_is_poisoned():
                        visited.add(neighbor)
                        parent[neighbor] = curr
                        queue.append(neighbor)

        return None

    def _evaluate_position(self, c: int, r: int) -> int:
        """מעריך כמה טוב מיקום להנחת פצצה"""
        score = 0

        # בדוק בכל 4 הכיוונים
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            for i in range(1, 3):  # טווח הפצצה
                nc, nr = c + (dc * i), r + (dr * i)

                if 0 <= nc < 13 and 0 <= nr < 15:
                    target = self._grid_list[nc][nr]

                    # אם יש אובייקט שניתן לפוצץ
                    if target.get_is_object():
                        if target.get_is_blowable():
                            score += 15
                        break

                    # אם יש שחקן בקרבת מקום
                    for p in self._other_players:
                        if p.is_alive() and p.get_column() == nc and p.get_row() == nr:
                            score += 80

        return score

    def _find_target(self) -> tuple | None:
        """מוצא מטרה טובה להנחת פצצה - רק אם יש מסלול בריחה!"""
        best_target = None
        best_score = 0
        danger = self.get_danger_zones()

        # חפש במרחק של עד 6 צעדים
        for dc in range(-6, 7):
            for dr in range(-6, 7):
                c = self._column + dc
                r = self._row + dr

                # בדוק שהמיקום חוקי
                if not (0 <= c < 13 and 0 <= r < 15):
                    continue

                # בדוק שזה לא אזור סכנה נוכחי
                if (c, r) in danger:
                    continue

                # בדוק שזה מקום ריק
                sqr = self._grid_list[c][r]
                if sqr.get_is_object():
                    continue

                # חשב ציון למיקום הזה
                score = self._evaluate_position(c, r)

                # רק אם יש משהו שווה לפוצץ
                if score >= 15:
                    # הכי חשוב: בדוק שיש מסלול בריחה!
                    has_escape, _ = self._has_escape_route((c, r))
                    if has_escape:
                        # העדף מקומות קרובים יותר
                        distance = abs(dc) + abs(dr)
                        final_score = score - distance

                        if final_score > best_score:
                            best_score = final_score
                            best_target = (c, r)

        return best_target

    def _move_towards(self, target: tuple) -> bool:
        """מנסה לזוז לכיוון המטרה"""
        if not target:
            return False

        tc, tr = target
        curr_c, curr_r = self._column, self._row

        # חשב את המרחק בכל ציר
        dc = tc - curr_c
        dr = tr - curr_r

        # בחר את הכיוון עם המרחק הגדול יותר
        moves = []

        if abs(dc) >= abs(dr):
            # נע בציר האנכי קודם
            if dc < 0 and curr_c > 0:
                moves.append((curr_c - 1, curr_r))
            elif dc > 0 and curr_c < 12:
                moves.append((curr_c + 1, curr_r))

            # אחר כך בציר האופקי
            if dr < 0 and curr_r > 0:
                moves.append((curr_c, curr_r - 1))
            elif dr > 0 and curr_r < 14:
                moves.append((curr_c, curr_r + 1))
        else:
            # נע בציר האופקי קודם
            if dr < 0 and curr_r > 0:
                moves.append((curr_c, curr_r - 1))
            elif dr > 0 and curr_r < 14:
                moves.append((curr_c, curr_r + 1))

            # אחר כך בציר האנכי
            if dc < 0 and curr_c > 0:
                moves.append((curr_c - 1, curr_r))
            elif dc > 0 and curr_c < 12:
                moves.append((curr_c + 1, curr_r))

        # נסה כל מהלך
        for new_c, new_r in moves:
            if self._is_safe_spot((new_c, new_r)):
                self._column, self._row = new_c, new_r
                return True

        return False

    def bot_algorithm(self):
        """הלוגיקה הראשית של הבוט - חכמה יותר!"""

        while self._running:
            try:
                if not self._is_alive:
                    break

                time.sleep(TIME_SLEEP)

                curr_pos = (self._column, self._row)
                danger_zones = self.get_danger_zones()

                # 1. קדימות ראשונה: אם אנחנו באזור סכנה - ברח מיד!
                if curr_pos in danger_zones:
                    safe_move = self._find_safe_path(curr_pos)
                    if safe_move:
                        self._column, self._row = safe_move
                    else:
                        # אין מסלול ברור - נסה תנועה אקראית בכל זאת
                        neighbors = self._who_is_around(self._column, self._row)
                        for n in neighbors:
                            nc, nr = n
                            sqr = self._grid_list[nc][nr]
                            if not sqr.get_is_object() or sqr.get_is_poisoned():
                                self._column, self._row = n
                                break
                    continue

                # 2. בדוק אם כדאי להניח פצצה כאן (רק אם יש מסלול בריחה!)
                current_time = time.time()
                if (len(self._active_bombs) < self._max_bombs and
                        current_time - self._last_bomb_time > 2.5):

                    score = self._evaluate_position(self._column, self._row)

                    if score >= 15:  # יש משהו שווה לפוצץ
                        # בדוק שיש מסלול בריחה!
                        has_escape, escape_target = self._has_escape_route(curr_pos)

                        if has_escape:
                            self.space()
                            self._last_bomb_time = current_time

                            # ברח מיד אחרי הנחת הפצצה
                            time.sleep(0.05)
                            if escape_target:
                                # נע לכיוון המקום הבטוח
                                safe_move = self._find_safe_path(curr_pos)
                                if safe_move:
                                    self._column, self._row = safe_move
                            continue

                # 3. חפש מטרה ולך לשם
                target = self._find_target()
                if target:
                    moved = self._move_towards(target)
                    if not moved:
                        # לא הצלחנו לזוז למטרה - תנועה אקראית בטוחה
                        neighbors = self._who_is_around(self._column, self._row)
                        safe_neighbors = [n for n in neighbors if self._is_safe_spot(n)]
                        if safe_neighbors:
                            self._column, self._row = random.choice(safe_neighbors)
                else:
                    # אין מטרה ספציפית - סתם תסתובב
                    neighbors = self._who_is_around(self._column, self._row)
                    safe_neighbors = [n for n in neighbors if self._is_safe_spot(n)]
                    if safe_neighbors:
                        self._column, self._row = random.choice(safe_neighbors)

            except Exception as e:
                import traceback
                traceback.print_exc()
