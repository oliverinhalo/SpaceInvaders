import pygame
import random
import os

BLOCK = 8
DISPLAY_X, DISPLAY_Y = 1000, 750
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assests")
START_LIVES = 3

DEFENDER_PATTERN = (
    "0000001000000",
    "0000011100000",
    "0000011100000",
    "0111111111110",
    "1111111111111",
    "1111111111111",
    "1111111111111",
    "1111111111111",
)

INVADER_PATTERNS = (
    ("00100100", "00011000", "00111100", "01111110", "11011011", "11111111", "10100101", "00100100"),
    ("00011000", "00111100", "01111110", "11011011", "11111111", "00100100", "01011010", "10100101"),
    ("00011000", "00111100", "01111110", "11011011", "11111111", "00100100", "01011010", "10000001"),
)


def make_sprite(pattern, pixel_size, color):
    """Build a surface from a pattern of '0'/'1' strings."""
    image = pygame.Surface((len(pattern[0]) * pixel_size, len(pattern) * pixel_size), pygame.SRCALPHA)
    for row, pixels in enumerate(pattern):
        for column, pixel in enumerate(pixels):
            if pixel == "1":
                pygame.draw.rect(image, color, (column * pixel_size, row * pixel_size, pixel_size, pixel_size))
    return image


class Images:
    def __init__(self):
        self.defender = make_sprite(DEFENDER_PATTERN, 5, (80, 200, 255))
        self.life_icon = make_sprite(DEFENDER_PATTERN, 2, (80, 200, 255))
        self.bullet = self.load_bullet()
        self.background = self.load_background()
        self.invaders = [make_sprite(p, Invader.SPRITE_SIZE, (100, 255, 120)) for p in INVADER_PATTERNS]

    def load_bullet(self):
        image = pygame.image.load(os.path.join(ASSETS, "images", "bullet.png")).convert_alpha()
        return pygame.transform.scale(image, (BLOCK, BLOCK * 2))

    def load_background(self):
        image = pygame.image.load(os.path.join(ASSETS, "images", "space.png"))
        return pygame.transform.scale(image, (DISPLAY_X, DISPLAY_Y))

    def get_invader(self, variant):
        return self.invaders[variant % len(self.invaders)]


class Defender:
    def __init__(self, images):
        self.images = images
        self.image = images.defender
        self.rect = self.image.get_rect(centerx=DISPLAY_X // 2, bottom=DISPLAY_Y - BLOCK * 4)
        self.lives = START_LIVES
        self.score = 0

    def update(self, screen):
        screen.blit(self.image, self.rect)

    def move(self, direction):
        if direction == 'left':
            self.rect.x = max(0, self.rect.x - BLOCK * 2)
        elif direction == 'right':
            self.rect.x = min(DISPLAY_X - self.rect.width, self.rect.x + BLOCK * 2)

    def shoot(self):
        Bullet(1, self.rect.centerx, self.rect.top, self.images)

    def hit(self):
        self.lives -= 1
        # Clear enemy bullets so one volley can't take several lives
        Bullet.bullets = [b for b in Bullet.bullets if b.direction == 1]


class Invader:
    invaders = []
    SPRITE_SIZE = 6
    POINTS = (30, 20, 10)  # top rows are worth more
    direction = 1

    def __init__(self, x, y, images, variant=0):
        Invader.invaders.append(self)
        self.asset_images = images
        self.image = images.get_invader(variant)
        self.points = self.POINTS[min(variant, len(self.POINTS) - 1)]
        self.rect = self.image.get_rect(topleft=(x, y))

    def shoot(self):
        Bullet(-1, self.rect.centerx, self.rect.bottom, self.asset_images)

    @classmethod
    def update_all(cls, screen):
        shift_down = any(i.rect.right >= DISPLAY_X or i.rect.left <= 0 for i in cls.invaders)
        if shift_down:
            cls.direction *= -1

        for invader in cls.invaders:
            if shift_down:
                invader.rect.y += BLOCK
            invader.rect.x += 2 * cls.direction
            if random.random() < 0.0005:
                invader.shoot()
            screen.blit(invader.image, invader.rect)


class Barrier:
    barriers = []

    def __init__(self, index, max_barriers):
        Barrier.barriers.append(self)
        pos_x = (index / (max_barriers + 1)) * DISPLAY_X + 100
        self.rect = pygame.Rect(pos_x, DISPLAY_Y - 250, 100, 50)

    def update(self, screen):
        pygame.draw.rect(screen, (0, 255, 0), self.rect)


class Bullet:
    bullets = []

    def __init__(self, direction, centerx, edge_y, images):
        self.image = images.bullet
        self.rect = self.image.get_rect(centerx=centerx)
        self.direction = direction
        if direction == 1:
            self.rect.bottom = edge_y
        else:
            self.rect.top = edge_y
        Bullet.bullets.append(self)

    def remove(self):
        if self in Bullet.bullets:
            Bullet.bullets.remove(self)

    def update(self, screen):
        self.rect.y -= BLOCK * self.direction
        if self.rect.bottom < 0 or self.rect.top > DISPLAY_Y:
            self.remove()
            return

        if self.direction == 1:
            for invader in tuple(Invader.invaders):
                if self.rect.colliderect(invader.rect):
                    self.remove()
                    Invader.invaders.remove(invader)
                    defender.score += invader.points
                    return
        elif self.rect.colliderect(defender.rect):
            self.remove()
            defender.hit()
            return

        for barrier in Barrier.barriers:
            if self.rect.colliderect(barrier.rect):
                self.remove()
                return

        screen.blit(self.image, self.rect)


def draw_hud(screen, font):
    screen.blit(font.render(f"SCORE: {defender.score}", True, (255, 255, 255)), (16, 12))
    lives_text = font.render("LIVES:", True, (255, 255, 255))
    life_icon = images.life_icon
    lives_x = DISPLAY_X - 16 - lives_text.get_width() - START_LIVES * (life_icon.get_width() + 8)
    screen.blit(lives_text, (lives_x, 12))
    for i in range(defender.lives):
        screen.blit(life_icon, (lives_x + lives_text.get_width() + 8 + i * (life_icon.get_width() + 8), 12))


def draw_message(screen, font, text):
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=(DISPLAY_X // 2, DISPLAY_Y // 2)))


pygame.init()
screen = pygame.display.set_mode((DISPLAY_X, DISPLAY_Y))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 80)
running = True
game_over_text = None

images = Images()
defender = Defender(images)
BARRIERS_NUM = 5

for i in range(BARRIERS_NUM):
    Barrier(i, BARRIERS_NUM)

invader_columns, invader_rows = 10, 4
invader_spacing_x, invader_spacing_y = 72, 64
invader_start_x = (DISPLAY_X - ((invader_columns - 1) * invader_spacing_x + (8 * Invader.SPRITE_SIZE))) // 2

for row in range(invader_rows):
    for column in range(invader_columns):
        Invader(invader_start_x + column * invader_spacing_x, 48 + row * invader_spacing_y, images, row)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
            running = False
        elif event.type == pygame.KEYDOWN and not game_over_text:
            if event.key == pygame.K_LEFT:
                defender.move('left')
            elif event.key == pygame.K_RIGHT:
                defender.move('right')
            elif event.key == pygame.K_SPACE:
                defender.shoot()

    screen.blit(images.background, (0, 0))

    if not game_over_text:
        Invader.update_all(screen)
        for bullet in tuple(Bullet.bullets):
            bullet.update(screen)

        if defender.lives <= 0 or any(i.rect.bottom >= defender.rect.top for i in Invader.invaders):
            game_over_text = "GAME OVER"
        elif not Invader.invaders:
            game_over_text = "YOU WIN!"
    else:
        for invader in Invader.invaders:
            screen.blit(invader.image, invader.rect)

    defender.update(screen)
    for barrier in Barrier.barriers:
        barrier.update(screen)
    draw_hud(screen, font)

    if game_over_text:
        draw_message(screen, big_font, game_over_text)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
