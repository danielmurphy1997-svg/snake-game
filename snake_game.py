import pygame
import random
import sys
from enum import Enum

# --- Constants ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE   # 30 cells wide
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE  # 20 cells tall
FPS_BASE = 8

# --- Colors ---
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   200, 0)
DARK_GREEN = (0,   140, 0)
RED        = (220, 50,  50)
YELLOW     = (255, 220, 0)
CYAN       = (0,   220, 220)
PURPLE     = (180, 0,   220)
ORANGE     = (255, 140, 0)
BLUE       = (50,  100, 255)
PINK       = (255, 100, 180)
GRAY       = (120, 120, 120)
DARK_GRAY  = (30,  30,  30)


class Direction(Enum):
    UP    = (0, -1)
    DOWN  = (0,  1)
    LEFT  = (-1, 0)
    RIGHT = (1,  0)


OPPOSITES = {
    Direction.UP:    Direction.DOWN,
    Direction.DOWN:  Direction.UP,
    Direction.LEFT:  Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


class PowerUpType(Enum):
    INVINCIBILITY = "Ghost"
    MAGNET        = "Magnet"
    SHRINK        = "Shrink"
    TIME_SLOW     = "Slow"
    FIREBALL      = "Fire"
    TELEPORT      = "Portal"


POWERUP_COLORS = {
    PowerUpType.INVINCIBILITY: CYAN,
    PowerUpType.MAGNET:        PURPLE,
    PowerUpType.SHRINK:        ORANGE,
    PowerUpType.TIME_SLOW:     BLUE,
    PowerUpType.FIREBALL:      RED,
    PowerUpType.TELEPORT:      PINK,
}

# Duration in game-frames (0 = instant / one-shot)
POWERUP_DURATION = {
    PowerUpType.INVINCIBILITY: 300,
    PowerUpType.MAGNET:        250,
    PowerUpType.SHRINK:        0,
    PowerUpType.TIME_SLOW:     200,
    PowerUpType.FIREBALL:      400,
    PowerUpType.TELEPORT:      500,
}


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        sx, sy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.body = [(sx, sy), (sx - 1, sy), (sx - 2, sy)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = 0

    def change_direction(self, new_dir: Direction):
        if new_dir != OPPOSITES[self.direction]:
            self.next_direction = new_dir

    def move(self):
        self.direction = self.next_direction
        dx, dy = self.direction.value
        hx, hy = self.body[0]
        self.body.insert(0, (hx + dx, hy + dy))
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, amount: int = 1):
        self.grow_pending += amount

    def shrink(self, amount: int = 3):
        target = max(3, len(self.body) - amount)
        self.body = self.body[:target]

    def wrap_walls(self):
        x, y = self.body[0]
        self.body[0] = (x % GRID_WIDTH, y % GRID_HEIGHT)

    @property
    def head(self):
        return self.body[0]

    def wall_collision(self) -> bool:
        x, y = self.head
        return x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT

    def self_collision(self) -> bool:
        return self.head in self.body[1:]

    def draw(self, surface: pygame.Surface, ghost: bool = False):
        r = GRID_SIZE // 2 - 1  # circle radius per segment

        def seg_center(sx, sy):
            return (sx * GRID_SIZE + GRID_SIZE // 2, sy * GRID_SIZE + GRID_SIZE // 2)

        for i, (x, y) in enumerate(self.body):
            cx, cy = seg_center(x, y)
            color = (CYAN if i == 0 else (0, 160, 160)) if ghost else (GREEN if i == 0 else DARK_GREEN)

            if ghost:
                tile = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(tile, (*color, 140), (r, r), r)
                surface.blit(tile, (cx - r, cy - r))
            else:
                # Fill the connector rect between this segment and the next
                if i + 1 < len(self.body):
                    nx, ny = self.body[i + 1]
                    ncx, ncy = seg_center(nx, ny)
                    # Rectangle spanning from this centre to next centre, width = diameter
                    rx = min(cx, ncx) - (r if cy == ncy else 0)
                    ry = min(cy, ncy) - (r if cx == ncx else 0)
                    rw = abs(ncx - cx) + (r * 2 if cy == ncy else 0)
                    rh = abs(ncy - cy) + (r * 2 if cx == ncx else 0)
                    pygame.draw.rect(surface, DARK_GREEN, (rx, ry, rw, rh))
                pygame.draw.circle(surface, color, (cx, cy), r)

        # Eye on head
        if self.body:
            hx, hy = self.body[0]
            cx, cy = seg_center(hx, hy)
            edx, edy = self.direction.value
            pygame.draw.circle(surface, BLACK, (cx + edx * 4, cy + edy * 4), 2)


# ---------------------------------------------------------------------------
# Food
# ---------------------------------------------------------------------------
class Food:
    def __init__(self, occupied):
        self.position = (0, 0)
        self.spawn(occupied)

    def spawn(self, occupied):
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in occupied:
                self.position = pos
                return

    def draw(self, surface: pygame.Surface):
        x, y = self.position
        rect = pygame.Rect(x * GRID_SIZE + 2, y * GRID_SIZE + 2, GRID_SIZE - 4, GRID_SIZE - 4)
        pygame.draw.ellipse(surface, RED, rect)
        pygame.draw.circle(surface, WHITE, (x * GRID_SIZE + 6, y * GRID_SIZE + 5), 2)


# ---------------------------------------------------------------------------
# PowerUp pickup
# ---------------------------------------------------------------------------
class PowerUp:
    def __init__(self, occupied):
        self.type = random.choice(list(PowerUpType))
        self.color = POWERUP_COLORS[self.type]
        self.position = (0, 0)
        self._spawn(occupied)
        self.lifetime = 280

    def _spawn(self, occupied):
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in occupied:
                self.position = pos
                return

    def draw(self, surface: pygame.Surface, frame: int):
        x, y = self.position
        pulse = int(2 * abs(pygame.math.Vector2(1, 0).rotate(frame * 6).x))
        size = GRID_SIZE - 2 + pulse
        off = (GRID_SIZE - size) // 2
        rect = pygame.Rect(x * GRID_SIZE + off, y * GRID_SIZE + off, size, size)
        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        lbl = pygame.font.SysFont("consolas", 9, bold=True).render(self.type.value[0], True, BLACK)
        surface.blit(lbl, (x * GRID_SIZE + 5, y * GRID_SIZE + 5))


# ---------------------------------------------------------------------------
# Fireball projectile
# ---------------------------------------------------------------------------
class Fireball:
    def __init__(self, pos, direction: Direction):
        self.pos = list(pos)
        self.direction = direction
        self.active = True

    def move(self):
        dx, dy = self.direction.value
        self.pos[0] += dx
        self.pos[1] += dy
        if not (0 <= self.pos[0] < GRID_WIDTH and 0 <= self.pos[1] < GRID_HEIGHT):
            self.active = False

    def grid_pos(self):
        return (int(self.pos[0]), int(self.pos[1]))

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        x, y = self.grid_pos()
        cx = x * GRID_SIZE + GRID_SIZE // 2
        cy = y * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, ORANGE, (cx, cy), GRID_SIZE // 2 - 1)
        pygame.draw.circle(surface, YELLOW, (cx, cy), GRID_SIZE // 4)


# ---------------------------------------------------------------------------
# Portal pair (for Teleport power-up)
# ---------------------------------------------------------------------------
class Portal:
    def __init__(self, occupied):
        self.positions = []
        self._spawn(occupied)

    def _spawn(self, occupied):
        tries = 0
        while len(self.positions) < 2 and tries < 200:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in occupied and pos not in self.positions:
                self.positions.append(pos)
            tries += 1

    def exit_of(self, entry):
        if entry == self.positions[0]:
            return self.positions[1]
        if entry == self.positions[1]:
            return self.positions[0]
        return None

    def draw(self, surface: pygame.Surface, frame: int):
        colors = [PINK, (200, 50, 255)]
        font = pygame.font.SysFont("consolas", 9, bold=True)
        for i, (x, y) in enumerate(self.positions):
            cx = x * GRID_SIZE + GRID_SIZE // 2
            cy = y * GRID_SIZE + GRID_SIZE // 2
            r = GRID_SIZE // 2 + int(2 * abs(pygame.math.Vector2(1, 0).rotate(frame * 8 + i * 90).x))
            pygame.draw.circle(surface, colors[i], (cx, cy), r, 3)
            lbl = font.render(str(i + 1), True, colors[i])
            surface.blit(lbl, (x * GRID_SIZE + 6, y * GRID_SIZE + 5))


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake  |  Arrow keys to move  |  P to pause")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 13)
        self._reset()

    # ------------------------------------------------------------------
    def _reset(self):
        self.snake    = Snake()
        self.food     = Food(set())
        self.score    = 0
        self.frame    = 0
        self.powerup  = None
        self.powerup_timer = random.randint(120, 220)
        self.active_effects: dict[PowerUpType, int] = {}  # type -> frames_left
        self.fireballs: list[Fireball] = []
        self.portals: Portal | None = None
        self.game_over = False
        self.paused    = False

    # ------------------------------------------------------------------
    def _occupied(self) -> set:
        occ = set(self.snake.body)
        occ.add(self.food.position)
        if self.powerup:
            occ.add(self.powerup.position)
        if self.portals:
            occ.update(self.portals.positions)
        return occ

    def _fps(self) -> int:
        speed = FPS_BASE + self.score // 5
        if PowerUpType.TIME_SLOW in self.active_effects:
            speed = max(3, speed // 2)
        return min(speed, 25)

    # ------------------------------------------------------------------
    def _apply_powerup(self, pu: PowerUp):
        pt = pu.type
        if pt == PowerUpType.SHRINK:
            self.snake.shrink(3)          # instant — no duration stored
        elif pt == PowerUpType.TELEPORT:
            self.portals = Portal(self._occupied())
            self.active_effects[pt] = POWERUP_DURATION[pt]
        else:
            self.active_effects[pt] = POWERUP_DURATION[pt]

    # ------------------------------------------------------------------
    def _update(self):
        if self.game_over or self.paused:
            return

        self.frame += 1

        # Count down active effects
        for pt in list(self.active_effects):
            self.active_effects[pt] -= 1
            if self.active_effects[pt] <= 0:
                del self.active_effects[pt]
                if pt == PowerUpType.TELEPORT:
                    self.portals = None

        # Magnet: nudge food one cell toward snake head each frame
        if PowerUpType.MAGNET in self.active_effects:
            fx, fy = self.food.position
            hx, hy = self.snake.head
            ndx = 0 if fx == hx else (1 if hx > fx else -1)
            ndy = 0 if fy == hy else (1 if hy > fy else -1)
            candidate = (fx + ndx, fy + ndy)
            if candidate not in self.snake.body:
                self.food.position = candidate

        # Move snake
        self.snake.move()

        # Collision resolution
        if PowerUpType.INVINCIBILITY in self.active_effects:
            self.snake.wrap_walls()
        else:
            if self.snake.wall_collision() or self.snake.self_collision():
                self.game_over = True
                return

        # Portal teleport
        if self.portals:
            exit_pos = self.portals.exit_of(self.snake.head)
            if exit_pos:
                self.snake.body[0] = exit_pos

        # Eat food
        if self.snake.head == self.food.position:
            self.snake.grow(1)
            self.score += 1
            self.food.spawn(self._occupied())

        # Collect power-up
        if self.powerup and self.snake.head == self.powerup.position:
            self._apply_powerup(self.powerup)
            self.powerup = None

        # Power-up natural expiry
        if self.powerup:
            self.powerup.lifetime -= 1
            if self.powerup.lifetime <= 0:
                self.powerup = None

        # Spawn next power-up
        if self.powerup is None:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.powerup = PowerUp(self._occupied())
                self.powerup_timer = random.randint(150, 300)

        # Move fireballs and check tail hits
        for fb in self.fireballs[:]:
            fb.move()
            if not fb.active:
                self.fireballs.remove(fb)
                continue
            gp = fb.grid_pos()
            if gp in self.snake.body[2:]:
                idx = self.snake.body.index(gp)
                self.snake.body = self.snake.body[:idx]  # sever tail at impact
                fb.active = False
                self.fireballs.remove(fb)

    # ------------------------------------------------------------------
    def _shoot(self):
        if PowerUpType.FIREBALL in self.active_effects:
            self.fireballs.append(Fireball(self.snake.head, self.snake.direction))

    # ------------------------------------------------------------------
    def _draw_hud(self):
        # Score (top-left)
        self.screen.blit(
            self.font_med.render(f"Score: {self.score}", True, WHITE), (10, 8)
        )
        # Active power-up timers (top-right, stacked left)
        rx = WINDOW_WIDTH - 10
        for pt, frames in self.active_effects.items():
            txt = self.font_small.render(f"{pt.value} {frames // 8 + 1}s", True, POWERUP_COLORS[pt])
            rx -= txt.get_width() + 8
            self.screen.blit(txt, (rx, 10))
        # Speed (bottom-left)
        self.screen.blit(
            self.font_small.render(f"Speed: {self._fps()}", True, GRAY), (10, WINDOW_HEIGHT - 20)
        )
        # Fireball hint (bottom-centre)
        if PowerUpType.FIREBALL in self.active_effects:
            hint = self.font_small.render("SPACE: shoot fireball", True, ORANGE)
            self.screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 20))
        # Pause hint
        pause_hint = self.font_small.render("P: pause", True, GRAY)
        self.screen.blit(pause_hint, (WINDOW_WIDTH - pause_hint.get_width() - 10, WINDOW_HEIGHT - 20))

    def _draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        for surf, y_off in [
            (self.font_large.render("GAME OVER", True, RED),   -55),
            (self.font_med.render(f"Final Score: {self.score}", True, WHITE), 0),
            (self.font_med.render("R  —  Restart",  True, GREEN), 45),
            (self.font_med.render("Q  —  Quit",     True, GRAY),  75),
        ]:
            self.screen.blit(surf, surf.get_rect(center=(cx, cy + y_off)))

    def _draw_paused(self):
        lbl = self.font_large.render("PAUSED", True, YELLOW)
        self.screen.blit(lbl, lbl.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

    # ------------------------------------------------------------------
    def _draw(self):
        self.screen.fill(DARK_GRAY)

        # Subtle grid
        for gx in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (42, 42, 42), (gx, 0), (gx, WINDOW_HEIGHT))
        for gy in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, (42, 42, 42), (0, gy), (WINDOW_WIDTH, gy))

        self.food.draw(self.screen)

        if self.powerup:
            self.powerup.draw(self.screen, self.frame)

        if self.portals:
            self.portals.draw(self.screen, self.frame)

        for fb in self.fireballs:
            fb.draw(self.screen)

        self.snake.draw(self.screen, ghost=PowerUpType.INVINCIBILITY in self.active_effects)

        self._draw_hud()

        if self.game_over:
            self._draw_game_over()
        elif self.paused:
            self._draw_paused()

        pygame.display.flip()

    # ------------------------------------------------------------------
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self._reset()
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            pygame.quit()
                            sys.exit()
                    else:
                        match event.key:
                            case pygame.K_UP:    self.snake.change_direction(Direction.UP)
                            case pygame.K_DOWN:  self.snake.change_direction(Direction.DOWN)
                            case pygame.K_LEFT:  self.snake.change_direction(Direction.LEFT)
                            case pygame.K_RIGHT: self.snake.change_direction(Direction.RIGHT)
                            case pygame.K_p:     self.paused = not self.paused
                            case pygame.K_SPACE: self._shoot()

            self._update()
            self._draw()
            self.clock.tick(self._fps())


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    game = Game()
    game.run()
