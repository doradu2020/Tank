import pygame
import random
import math

# 初始化
pygame.init()

# 游戏窗口设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("坦克大战")
clock = pygame.time.Clock()

# 颜色
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# 坦克类
class Tank:
    def __init__(self, x, y, color, speed=3, is_player=False):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.is_player = is_player
        self.width = 40
        self.height = 40
        self.angle = 0  # 0 = 上, 90 = 右, 180 = 下, 270 = 左
        self.cooldown = 0

    def rotate(self, direction):
        self.angle = direction

    def move_forward(self):
        rad = math.radians(self.angle)
        self.x += math.sin(rad) * self.speed
        self.y -= math.cos(rad) * self.speed
        self.x = max(20, min(WIDTH - 20, self.x))
        self.y = max(20, min(HEIGHT - 20, self.y))

    def move_backward(self):
        rad = math.radians(self.angle)
        self.x -= math.sin(rad) * self.speed * 0.6
        self.y += math.cos(rad) * self.speed * 0.6
        self.x = max(20, min(WIDTH - 20, self.x))
        self.y = max(20, min(HEIGHT - 20, self.y))

    def draw(self):
        # 绘制坦克身体
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        rect = surface.get_rect(center=(self.x, self.y))
        pygame.draw.rect(surface, self.color, (rect.width//4, rect.height//4,
                                                  rect.width//2, rect.height//2))
        # 炮管
        pygame.draw.line(surface, self.color, (rect.centerx, rect.centery),
                         (rect.centerx + math.sin(math.radians(self.angle)) * 25,
                          rect.centery - math.cos(math.radians(self.angle)) * 25), 6)
        # 履带
        pygame.draw.rect(surface, GRAY, (0, 0, rect.width, 8))
        pygame.draw.rect(surface, GRAY, (0, rect.height - 8, rect.width, 8))

        rotated = pygame.transform.rotate(surface, self.angle)
        screen.blit(rotated, rotated.get_rect(center=(self.x, self.y)))

    def get_rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                          self.width, self.height)

    def fire(self):
        if self.cooldown <= 0:
            self.cooldown = 20
            rad = math.radians(self.angle)
            bullet_x = self.x + math.sin(rad) * 30
            bullet_y = self.y - math.cos(rad) * 30
            return Bullet(bullet_x, bullet_y, self.angle)
        return None

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

# 子弹类
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 8
        self.radius = 5

    def move(self):
        rad = math.radians(self.angle)
        self.x += math.sin(rad) * self.speed
        self.y -= math.cos(rad) * self.speed

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

    def is_off_screen(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

# 爆炸效果类
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 40
        self.alpha = 255

    def update(self):
        self.radius += 3
        self.alpha -= 20

    def draw(self):
        if self.alpha > 0:
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*RED, max(0, self.alpha)),
                             (self.radius, self.radius), self.radius)
            pygame.draw.circle(s, (*YELLOW, max(0, self.alpha//2)),
                             (self.radius, self.radius), self.radius//2)
            screen.blit(s, (self.x - self.radius, self.y - self.radius))

    def is_done(self):
        return self.alpha <= 0

# 敌方坦克AI
class EnemyTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, RED, speed=1.5, is_player=False)
        self.move_timer = 0
        self.fire_timer = 0
        self.current_direction = random.choice([0, 90, 180, 270])

    def update(self, player_tank):
        # 随机改变方向
        self.move_timer += 1
        if self.move_timer > 60:
            self.move_timer = 0
            if random.random() < 0.4:
                self.current_direction = random.choice([0, 90, 180, 270])

        # 面向玩家
        if random.random() < 0.02:
            dx = player_tank.x - self.x
            dy = player_tank.y - self.y
            self.current_direction = math.degrees(math.atan2(dx, -dy)) % 360

        self.angle = self.current_direction
        self.move_forward()

        # 随机开火
        self.fire_timer += 1
        if self.fire_timer > 90:
            self.fire_timer = 0
            if random.random() < 0.5:
                return self.fire()
        return None

# 砖墙类
class Brick:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20

    def draw(self):
        pygame.draw.rect(screen, (180, 100, 50),
                        (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (150, 80, 40),
                        (self.x + 2, self.y + 2, self.width - 4, self.height - 4))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# 游戏主类
class Game:
    def __init__(self):
        self.player = Tank(WIDTH // 2, HEIGHT - 60, GREEN, is_player=True)
        self.enemies = []
        self.bullets = []
        self.explosions = []
        self.bricks = []
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.enemies_to_spawn = 5
        self.spawn_timer = 0
        self.game_over = False
        self.paused = False
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)

        # 创建地图边界和障碍物
        self.create_map()

    def create_map(self):
        # 四周围墙
        for x in range(0, WIDTH, 40):
            self.bricks.append(Brick(x, 0))
            self.bricks.append(Brick(x, HEIGHT - 20))
        for y in range(0, HEIGHT, 40):
            self.bricks.append(Brick(0, y))
            self.bricks.append(Brick(WIDTH - 20, y))

        # 中间一些随机障碍
        for _ in range(15):
            x = random.randint(100, WIDTH - 120)
            y = random.randint(100, HEIGHT - 120)
            # 避免放在玩家出生点附近
            if abs(x - WIDTH // 2) > 100 or abs(y - (HEIGHT - 60)) > 100:
                self.bricks.append(Brick(x, y))

    def spawn_enemy(self):
        if len(self.enemies) < self.wave + 2:
            x = random.randint(60, WIDTH - 60)
            y = random.randint(60, 150)
            self.enemies.append(EnemyTank(x, y))
            self.enemies_to_spawn -= 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                if event.key == pygame.K_SPACE and not self.game_over and not self.paused:
                    bullet = self.player.fire()
                    if bullet:
                        self.bullets.append(bullet)
        return True

    def update(self):
        if self.game_over or self.paused:
            return

        keys = pygame.key.get_pressed()

        # 玩家移动和旋转
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.move_forward()
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player.move_backward()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.angle = (self.player.angle + 4) % 360
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.angle = (self.player.angle - 4) % 360
        if keys[pygame.K_SPACE]:
            bullet = self.player.fire()
            if bullet:
                self.bullets.append(bullet)

        # 更新敌人
        for enemy in self.enemies[:]:
            bullet = enemy.update(self.player)
            if bullet:
                self.bullets.append(bullet)

            # 敌人与玩家碰撞
            if enemy.get_rect().colliderect(self.player.get_rect()):
                self.lives -= 1
                self.explosions.append(Explosion(self.player.x, self.player.y))
                if self.lives <= 0:
                    self.game_over = True
                else:
                    self.player.x = WIDTH // 2
                    self.player.y = HEIGHT - 60

        # 生成敌人
        self.spawn_timer += 1
        if self.enemies_to_spawn > 0 and self.spawn_timer > 120:
            self.spawn_timer = 0
            self.spawn_enemy()

        # 波次检查
        if len(self.enemies) == 0 and self.enemies_to_spawn == 0:
            self.wave += 1
            self.enemies_to_spawn = self.wave + 4

        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.is_off_screen():
                self.bullets.remove(bullet)
                continue

            # 子弹击中敌人
            for enemy in self.enemies[:]:
                if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < 25:
                    self.explosions.append(Explosion(enemy.x, enemy.y))
                    self.enemies.remove(enemy)
                    self.score += 100
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

            # 子弹击中墙壁
            for brick in self.bricks[:]:
                if brick.get_rect().collidepoint(bullet.x, bullet.y):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # 更新爆炸效果
        for exp in self.explosions[:]:
            exp.update()
            if exp.is_done():
                self.explosions.remove(exp)

    def draw(self):
        screen.fill(BLACK)

        # 绘制砖墙
        for brick in self.bricks:
            brick.draw()

        # 绘制爆炸
        for exp in self.explosions:
            exp.draw()

        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw()

        # 绘制敌人
        for enemy in self.enemies:
            enemy.draw()

        # 绘制玩家
        if not self.game_over:
            self.player.draw()

        # UI
        score_text = self.font.render(f"得分: {self.score}", True, WHITE)
        lives_text = self.font.render(f"生命: {self.lives}", True, WHITE)
        wave_text = self.font.render(f"波次: {self.wave}", True, WHITE)
        screen.blit(score_text, (10, 30))
        screen.blit(lives_text, (10, 60))
        screen.blit(wave_text, (10, 90))

        # 控制提示
        controls = self.font.render("WASD/方向键移动 空格开火 ESC暂停", True, GRAY)
        screen.blit(controls, (WIDTH - controls.get_width() - 10, HEIGHT - 30))

        if self.paused:
            pause_text = self.big_font.render("暂停", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2,
                                    HEIGHT//2 - pause_text.get_height()//2))
            hint = self.font.render("按ESC继续", True, GRAY)
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 40))

        if self.game_over:
            game_over_text = self.big_font.render("游戏结束", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2,
                                         HEIGHT//2 - 60))
            final_score = self.font.render(f"最终得分: {self.score}", True, WHITE)
            screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2,
                                       HEIGHT//2))
            restart = self.font.render("按R重新开始", True, GRAY)
            screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 40))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
