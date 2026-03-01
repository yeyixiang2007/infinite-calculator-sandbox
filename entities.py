import random

class Entity:
    def __init__(self, x, y, symbol, color=None):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.color = color # Placeholder for future color support

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 'P') # Player is 'P'
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.xp = 0
        self.stamina = 100
        self.max_stamina = 100
        self.level = 1
        self.xp_next = 100
        self.attack_damage = 20
        self.attack_range = 2
        self.inventory = []

    def move(self, dx, dy, world):
        new_x = self.x + dx
        new_y = self.y + dy

        if not world.is_blocked(new_x, new_y):
            self.x = new_x
            self.y = new_y

            # Interact with the tile
            tile = world.get_tile(new_x, new_y)
            if tile.isdigit():
                val = int(tile)
                self.score += val
                self.xp += val * 10 # Base XP from numbers
                world.set_tile(new_x, new_y, '.') # Collect the number
                return f"Collected {val}!"
            elif tile in ['+', '-', '*', '/', '^', '%']:
                # Operator logic
                if tile == '+':
                    self.health = min(self.max_health, self.health + 10)
                    world.set_tile(new_x, new_y, '.')
                    return "Health +10!"
                elif tile == '-':
                    self.health -= 10
                    world.set_tile(new_x, new_y, '.')
                    return "Health -10!"
                elif tile == '*':
                    gain = min(self.score, 50) # Cap gain at 50
                    self.score += gain
                    world.set_tile(new_x, new_y, '.')
                    return f"Score +{gain} (Doubled, Capped)!"
                elif tile == '/':
                    self.score //= 2
                    world.set_tile(new_x, new_y, '.')
                    return "Score Halved!"
                elif tile == '^':
                    gain = min(self.score ** 2 - self.score, 50) # Cap gain at 50
                    self.score += gain
                    world.set_tile(new_x, new_y, '.')
                    return f"Score +{gain} (Squared, Capped)!"
                elif tile == '%':
                    self.score = self.score % 10
                    world.set_tile(new_x, new_y, '.')
                    return "Score Modulo 10!"
            elif tile in ['~', '{', '}']:
                # Strategic Score Manipulation
                score_str = str(abs(self.score))
                if tile == '~':
                    self.score = int(score_str[::-1])
                    world.set_tile(new_x, new_y, '.')
                    return "SCORE REVERSED!"
                elif tile == '{':
                    self.score = int("".join(sorted(score_str)))
                    world.set_tile(new_x, new_y, '.')
                    return "SCORE SORTED (ASC)!"
                elif tile == '}':
                    self.score = int("".join(sorted(score_str, reverse=True)))
                    world.set_tile(new_x, new_y, '.')
                    return "SCORE SORTED (DESC)!"
            elif tile == 'E':
                return "WIN"
        return ""

    def update(self, dt=0.05):
        # Regenerate stamina (12 points per second - slower)
        if self.stamina < self.max_stamina:
            self.stamina += 12 * dt
            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

        # Level up check (using XP)
        if self.xp >= self.xp_next:
            self.level += 1
            # Progressive scaling for more mid-late consistency
            self.xp_next += int(100 * (self.level ** 1.5))
            return True # Signal level up
        return False

class Enemy(Entity):
    def __init__(self, x, y, symbol, damage, hp=20):
        super().__init__(x, y, symbol)
        self.damage = damage
        self.hp = hp
        self.max_hp = hp
        self.move_timer = 0
        self.move_delay = 15 # Further slowed down (approx 0.75s)

    def update(self, player, world):
        self.move_timer += 1
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.move(player, world)
            # Collision check only happens when moving
            if self.x == player.x and self.y == player.y:
                return True
        return False

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0

    def move(self, player, world):
        pass # To be implemented by subclasses

class Chaser(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 'X', 10, hp=30) # 'X' has more HP
        self.move_delay = 18 # Slower but persistent

    def move(self, player, world):
        dx = 0
        dy = 0
        if self.x < player.x: dx = 1
        elif self.x > player.x: dx = -1

        if self.y < player.y: dy = 1
        elif self.y > player.y: dy = -1

        # Check for obstacles properly
        # Don't move diagonally if it means clipping through a corner
        can_move_x = dx != 0 and not world.is_blocked(self.x + dx, self.y)
        can_move_y = dy != 0 and not world.is_blocked(self.x, self.y + dy)

        if dx != 0 and dy != 0:
            # Diagonal move: only if both axis are free
            if can_move_x and can_move_y and not world.is_blocked(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy
            elif can_move_x:
                self.x += dx
            elif can_move_y:
                self.y += dy
        elif can_move_x:
            self.x += dx
        elif can_move_y:
            self.y += dy

class RandomWalker(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, '?', 5, hp=15) # '?' is weaker
        self.move_delay = 25 # Very slow

    def move(self, player, world):
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(moves)
        for dx, dy in moves:
            if not world.is_blocked(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy
                break

class Glitch(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 'G', 15, hp=40)
        self.move_delay = 14

    def move(self, player, world):
        if random.random() < 0.2:
             # Teleport randomly
             dx = random.randint(-3, 3)
             dy = random.randint(-3, 3)
             if not world.is_blocked(self.x + dx, self.y + dy):
                 self.x += dx
                 self.y += dy
        else:
             # Move towards player aggressively
            dx = 0
            dy = 0
            if self.x < player.x: dx = 1
            elif self.x > player.x: dx = -1
            if self.y < player.y: dy = 1
            elif self.y > player.y: dy = -1

            if not world.is_blocked(self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy

class Virus(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 'V', 5, hp=10)
        self.move_delay = 10 # Fast but not overwhelming

    def move(self, player, world):
        # Very simple direct movement, ignores diagonal blocks sometimes (glitchy)
        dx = 0
        dy = 0
        if self.x < player.x: dx = 1
        elif self.x > player.x: dx = -1
        if self.y < player.y: dy = 1
        elif self.y > player.y: dy = -1

        if not world.is_blocked(self.x + dx, self.y + dy):
             self.x += dx
             self.y += dy

class Projectile(Entity):
    def __init__(self, x, y, dx, dy, symbol, damage):
        super().__init__(x, y, symbol)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.life = 20 # Range/Duration

    def update(self, world):
        self.life -= 1
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        if world.is_blocked(new_x, new_y):
            return True # Hit wall

        self.x = new_x
        self.y = new_y
        return self.life <= 0

class Boss(Enemy):
    def __init__(self, x, y, symbol_matrix, damage, hp):
        # symbol_matrix is a list of strings, e.g. ["/-\", "|@|", "\-/"]
        self.width = len(symbol_matrix[0])
        self.height = len(symbol_matrix)
        super().__init__(x, y, symbol_matrix[0][0], damage, hp) # Symbol placeholder
        self.symbol_matrix = symbol_matrix
        self.move_delay = 30 # Bosses are slow
        self.attack_timer = 0
        self.attack_cooldown = 40

    def get_occupied_cells(self):
        cells = []
        for dy in range(self.height):
            for dx in range(self.width):
                cells.append((self.x + dx, self.y + dy))
        return cells

    def update(self, player, world, engine):
        # Custom update to handle multi-tile movement and attacking
        self.move_timer += 1
        self.attack_timer += 1

        # Movement
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.move(player, world)

        # Attack
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            self.attack(player, engine)

        # Collision with player (body slam)
        player_pos = (player.x, player.y)
        if player_pos in self.get_occupied_cells():
            return True
        return False

    def move(self, player, world):
        # Simple movement: try to move towards player but check all occupied cells
        dx = 0
        dy = 0
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        if center_x < player.x: dx = 1
        elif center_x > player.x: dx = -1

        if center_y < player.y: dy = 1
        elif center_y > player.y: dy = -1

        # Check if new position is valid for ALL cells
        if self.can_move_to(self.x + dx, self.y + dy, world):
            self.x += dx
            self.y += dy
        elif self.can_move_to(self.x + dx, self.y, world):
            self.x += dx
        elif self.can_move_to(self.x, self.y + dy, world):
            self.y += dy

    def can_move_to(self, tx, ty, world):
        for r in range(self.height):
            for c in range(self.width):
                if world.is_blocked(tx + c, ty + r):
                    return False
        return True

    def attack(self, player, engine):
        pass

class MathLord(Boss):
    def __init__(self, x, y):
        matrix = [
            "[MATH]",
            "/LORD\\"
        ]
        super().__init__(x, y, matrix, 25, 300) # High HP, High Damage
        self.attack_cooldown = 50

    def attack(self, player, engine):
        # Fire projectiles in 8 directions
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        dirs = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
        for dx, dy in dirs:
            proj = Projectile(center_x, center_y, dx, dy, '*', 15)
            engine.projectiles.append(proj)

        engine.message = "MATH LORD UNLEASHES CHAOS!"
