import os
import sys
import time
import input_handler as input_h
import random
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.table import Table
from world import World
from entities import Player, Chaser, RandomWalker, Glitch, Virus, Boss, MathLord, Projectile

class Effect:
    def __init__(self, x, y, symbol, style, duration=10):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.style = style
        self.duration = duration

class GameEngine:
    def __init__(self):
        self.console = Console()
        self.viewport_width = 40
        self.viewport_height = 20
        self.running = True
        self.state = "MENU" # MENU, GAME, GAME_OVER, HELP, PAUSED, DIFFICULTY_SELECT, MODE_SELECT, LEVEL_UP
        self.difficulty = "NORMAL" # EASY, NORMAL, HARD
        self.game_mode = "CHALLENGE" # CHALLENGE, ENDLESS
        self.timer = 0 # For challenge mode
        self.level_up_options = []

        self.world = World()
        self.player = Player(0, 0)
        self.effects = [] # Temporary visual effects

        # Difficulty multipliers
        self.diff_mods = {
            "EASY": {"hp": 0.7, "speed": 1.5, "damage": 0.7, "spawn": 8},
            "NORMAL": {"hp": 1.0, "speed": 1.0, "damage": 1.0, "spawn": 12},
            "HARD": {"hp": 1.5, "speed": 0.7, "damage": 1.5, "spawn": 18}
        }

        # Ensure player doesn't spawn on a wall
        while self.world.is_blocked(self.player.x, self.player.y):
             self.player.x += 1

        self.world.add_entity(self.player)
        self.enemies = []
        self.projectiles = []
        self.message = "Welcome to Infinite Calculator Sandbox!"
        self.exit_spawned = False
        self.exit_coords = None
        self.exit_reset_timer = 0.0 # Timer for portal repositioning
        self.invincible_timer = 0.0

    def add_effect(self, x, y, symbol, style, duration=5):
        self.effects.append(Effect(x, y, symbol, style, duration))

    def spawn_enemy_near_player(self, enemy_class):
        mod = self.diff_mods[self.difficulty]
        while True:
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-10, 10)
            x = self.player.x + offset_x
            y = self.player.y + offset_y

            if not self.world.is_blocked(x, y) and (abs(x - self.player.x) > 8 or abs(y - self.player.y) > 8):
                enemy = enemy_class(x, y)
                # Apply difficulty
                enemy.hp = int(enemy.hp * mod["hp"])
                enemy.max_hp = enemy.hp
                enemy.damage = int(enemy.damage * mod["damage"])
                enemy.move_delay = max(2, int(enemy.move_delay * mod["speed"]))

                self.enemies.append(enemy)
                self.world.add_entity(enemy)
                break

    def handle_input(self):
        if input_h.kbhit():
            key = input_h.getch()
            try:
                # Handle arrow keys (prefix 0x00 or 0xE0)
                if key in [b'\x00', b'\xe0']:
                    key = input_h.getch() # Read the second byte
                    if key == b'H': key = 'w'
                    elif key == b'P': key = 's'
                    elif key == b'K': key = 'a'
                    elif key == b'M': key = 'd'
                else:
                    key = key.decode('utf-8').lower()
            except UnicodeDecodeError:
                return

            if self.state == "MENU":
                if key == '1': self.state = "DIFFICULTY_SELECT"
                elif key == '2': self.state = "HELP"
                elif key == '3' or key == 'q': self.running = False

            elif self.state == "DIFFICULTY_SELECT":
                if key == '1':
                    self.difficulty = "EASY"
                    self.state = "MODE_SELECT"
                elif key == '2':
                    self.difficulty = "NORMAL"
                    self.state = "MODE_SELECT"
                elif key == '3':
                    self.difficulty = "HARD"
                    self.state = "MODE_SELECT"
                elif key == 'b' or key == 'q': self.state = "MENU"

            elif self.state == "MODE_SELECT":
                if key == '1':
                    self.game_mode = "CHALLENGE"
                    self.start_game()
                elif key == '2':
                    self.game_mode = "ENDLESS"
                    self.start_game()
                elif key == 'b' or key == 'q': self.state = "DIFFICULTY_SELECT"

            elif self.state == "HELP":
                if key == 'b' or key == 'q': self.state = "MENU"

            elif self.state == "GAME":
                result = ""
                if key == 'q':
                    self.state = "MENU"
                elif key == 'p':
                    self.state = "PAUSED"
                elif key == 'e': # Special AC skill
                    self.perform_ac_skill()
                elif key == ' ': # Spacebar to attack
                    self.perform_attack()
                elif key == 'w':
                    result = self.player.move(0, -1, self.world)
                elif key == 's':
                    result = self.player.move(0, 1, self.world)
                elif key == 'a':
                    result = self.player.move(-1, 0, self.world)
                elif key == 'd':
                    result = self.player.move(1, 0, self.world)

                if result == "WIN":
                    self.message = "YOU ESCAPED THE MATRIX!"
                    self.state = "GAME_OVER"
                elif result:
                    self.message = result

            elif self.state == "PAUSED":
                if key == 'p':
                    self.state = "GAME"
                elif key == 'q':
                    self.state = "MENU"

            elif self.state == "LEVEL_UP":
                if key in ['1', '2', '3', '4']:
                    choice = self.level_up_options[int(key)-1]
                    if choice == "MAX_HP":
                        self.player.max_health += 20
                    elif choice == "MAX_STAMINA":
                        self.player.max_stamina += 20
                        self.player.stamina += 20
                    elif choice == "DAMAGE":
                        self.player.attack_damage += 10
                    elif choice == "RANGE":
                        self.player.attack_range += 1

                    self.state = "GAME"
                    self.message = f"Upgraded {choice}!"

            elif self.state == "GAME_OVER":
                if key == 'r':
                    self.__init__() # Reset game
                    self.state = "GAME"
                    self.invincible_timer = 3.0
                elif key == 'q':
                    self.state = "MENU"

    def start_game(self):
        # Full reset of game state but keep difficulty/mode
        self.world = World()
        self.player = Player(0, 0)
        while self.world.is_blocked(self.player.x, self.player.y):
             self.player.x += 1
        self.world.add_entity(self.player)
        self.enemies = []
        self.projectiles = []
        self.effects = []
        self.exit_spawned = False
        self.exit_coords = None
        self.exit_reset_timer = 0.0
        self.invincible_timer = 3.0
        self.timer = 180 if self.game_mode == "CHALLENGE" else 0
        self.state = "GAME"
        self.message = f"Starting {self.game_mode} Mode ({self.difficulty})"

        # Initial spawns
        for _ in range(5):
            self.spawn_enemy_near_player(random.choice([Chaser, RandomWalker]))

    def perform_attack(self):
        # Attack in 5x5 area around player (range from player.attack_range)
        r = self.player.attack_range
        cost = 30
        if self.player.stamina < cost:
            self.message = "NOT ENOUGH STAMINA!"
            return

        self.player.stamina -= cost
        hits = 0
        destroyed = []

        # Attack effect
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                if dx == 0 and dy == 0: continue
                if random.random() < 0.3:
                    self.add_effect(self.player.x + dx, self.player.y + dy, "*", "bold yellow", 3)

        for enemy in self.enemies:
            if isinstance(enemy, Boss):
                # Check collision with all occupied cells
                cells = enemy.get_occupied_cells()
                hit = False
                for cx, cy in cells:
                     if abs(cx - self.player.x) <= r and abs(cy - self.player.y) <= r:
                         hit = True
                         break

                if hit:
                    hits += 1
                    self.add_effect(enemy.x + enemy.width//2, enemy.y + enemy.height//2, "!", "bold red", 5)
                    if enemy.take_damage(self.player.attack_damage):
                        destroyed.append(enemy)

            elif abs(enemy.x - self.player.x) <= r and abs(enemy.y - self.player.y) <= r:
                hits += 1
                # Hit effect
                self.add_effect(enemy.x, enemy.y, "!", "bold red", 5)
                if enemy.take_damage(self.player.attack_damage):
                    destroyed.append(enemy)

        for enemy in destroyed:
            # Death effect
            for _ in range(3):
                self.add_effect(enemy.x + random.randint(-1, 1), enemy.y + random.randint(-1, 1), "#", "dim red", 8)

            if enemy in self.enemies:
                self.enemies.remove(enemy)
            if enemy in self.world.entities:
                self.world.entities.remove(enemy)

            if isinstance(enemy, Boss):
                self.player.xp += 300 # More XP for active kill
                self.player.score += 50
                self.invincible_timer = 10.0 # 10s shield reward
                self.message = "MATH LORD TERMINATED! SIGNAL SHIELD STABILIZED!"
            else:
                self.player.score += 5
                self.player.xp += 20 # XP for kills

        if hits > 0:
            self.message = f"ATTACK! Hit {hits} enemies. Destroyed {len(destroyed)}."
        else:
            self.message = "ATTACK! Missed."

    def perform_ac_skill(self):
        # All Clear skill - clears viewport enemies
        cost = 100 # Increased cost from 80
        if self.player.stamina < cost:
            self.message = "NOT ENOUGH STAMINA FOR AC!"
            return

        self.player.stamina -= cost
        self.message = "ALL CLEAR! [AC] ACTIVATED."

        destroyed = []
        for enemy in self.enemies:
            # Clear enemies in viewport
            if abs(enemy.x - self.player.x) < 20 and abs(enemy.y - self.player.y) < 10:
                destroyed.append(enemy)
                # Flashy effect
                self.add_effect(enemy.x, enemy.y, "0", "bold white reverse", 10)

        for enemy in destroyed:
            self.enemies.remove(enemy)
            if enemy in self.world.entities:
                self.world.entities.remove(enemy)

            # Bonus XP if it was a boss
            if isinstance(enemy, Boss):
                 self.player.xp += 200 # Boss bounty
                 self.player.score += 50
                 self.invincible_timer = 5.0 # 5s shield reward
                 self.message = "BOSS DEFEATED! SIGNAL SHIELD ACTIVE!"
            else:
                 self.player.score += 2
                 self.player.xp += 5

        # Screen flash effect simulation
        for _ in range(20):
             rx = self.player.x + random.randint(-20, 20)
             ry = self.player.y + random.randint(-10, 10)
             self.add_effect(rx, ry, " ", "on white", 5)

    def spawn_exit_portal(self):
        # Remove old portal if exists
        if self.exit_coords:
            self.world.set_tile(self.exit_coords[0], self.exit_coords[1], '.')

        # Spawn exit somewhere at a distance (15-25 blocks)
        while True:
            dist = random.randint(15, 25)
            angle = random.uniform(0, 6.28) # Random direction
            import math
            offset_x = int(math.cos(angle) * dist)
            offset_y = int(math.sin(angle) * dist)

            x = self.player.x + offset_x
            y = self.player.y + offset_y

            if not self.world.is_blocked(x, y):
                self.world.set_tile(x, y, 'E')
                self.exit_spawned = True
                self.exit_coords = (x, y)
                self.exit_reset_timer = 15.0 # Reset every 15s
                self.message = "EXIT PORTAL 'E' SHIFTED! HURRY!"
                break

    def update(self):
        if self.state != "GAME":
            return

        # Update player logic (stamina etc)
        level_up = self.player.update(dt=0.05)
        if level_up:
            self.state = "LEVEL_UP"
            self.level_up_options = ["MAX_HP", "MAX_STAMINA", "DAMAGE", "RANGE"]
            return

        # Update challenge timer
        if self.game_mode == "CHALLENGE" and self.timer > 0:
            self.timer -= 0.05
            if self.timer <= 0:
                self.message = "TIME EXPIRED! SYSTEM FAILURE."
                self.state = "GAME_OVER"

        # Update effects
        self.effects = [e for e in self.effects if e.duration > 0]
        for e in self.effects:
            e.duration -= 1

        # Update timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 0.05
            if self.invincible_timer <= 0:
                self.invincible_timer = 0
                self.message = "INVINCIBILITY EXPIRED!"

        # Update projectiles
        active_projectiles = []
        for proj in self.projectiles:
            hit = proj.update(self.world)
            if hit:
                self.add_effect(proj.x, proj.y, "*", "bold yellow", 3)
                continue

            # Check collision with player
            if proj.x == self.player.x and proj.y == self.player.y:
                if self.invincible_timer > 0:
                     self.message = "BLOCKED BY SHIELD!"
                else:
                     self.player.health -= proj.damage
                     self.message = "HIT BY PROJECTILE!"
                     self.add_effect(self.player.x, self.player.y, "X", "bold red reverse", 5)
                continue

            active_projectiles.append(proj)
        self.projectiles = active_projectiles

        # Despawn far enemies and spawn new ones to keep population around player
        active_enemies = []
        for enemy in self.enemies:
            dist_x = abs(enemy.x - self.player.x)
            dist_y = abs(enemy.y - self.player.y)

            if dist_x > 40 or dist_y > 30: # Increased range for Bosses
                if enemy in self.world.entities:
                    self.world.entities.remove(enemy)
                continue

            active_enemies.append(enemy)
            if isinstance(enemy, Boss):
                hit = enemy.update(self.player, self.world, self)
            else:
                hit = enemy.update(self.player, self.world)

            if hit:
                if self.invincible_timer > 0:
                    self.message = "PROTECTED BY SIGNAL SHIELD!"
                else:
                    # Enemy attack effect
                    self.add_effect(self.player.x, self.player.y, "X", "bold red reverse", 5)
                    self.player.health -= enemy.damage
                    self.message = f"Ouch! Hit by {enemy.symbol}!"

        self.enemies = active_enemies

        # Maintain enemy count
        target_count = self.diff_mods[self.difficulty]["spawn"]

        # Chance to spawn boss if score is high enough and no boss exists
        boss_present = any(isinstance(e, Boss) for e in self.enemies)
        if not boss_present and self.player.score > 100 and random.random() < 0.01:
             self.spawn_enemy_near_player(MathLord)
        elif len(self.enemies) < target_count:
             self.spawn_enemy_near_player(random.choice([Chaser, RandomWalker, Glitch, Virus]))

        # Spawn Exit logic (Challenge mode only)
        if self.game_mode == "CHALLENGE" and self.player.score >= 200:
            if not self.exit_spawned:
                self.spawn_exit_portal()
                self.message = "EXIT PORTAL 'E' OPENED! CHECK COMPASS!"
            else:
                # Update portal reset timer
                self.exit_reset_timer -= 0.05
                if self.exit_reset_timer <= 0:
                    self.spawn_exit_portal()

        if self.player.health <= 0:
            self.message = "DEFEAT: SIGNAL LOST."
            self.state = "GAME_OVER"

    def get_renderable_grid(self, force_dim=False):
        viewport, start_x, start_y = self.world.get_viewport(self.player.x, self.player.y, self.viewport_width, self.viewport_height)

        text_grid = Text()
        is_invincible = self.invincible_timer > 0 or force_dim

        for y, row in enumerate(viewport):
            for x, char in enumerate(row):
                world_x = start_x + x
                world_y = start_y + y

                entity_char = char
                style = "white"

                if char == '.': style = "grey23"
                elif char == '|': style = "bold white"
                elif char.isdigit(): style = "bold cyan"
                elif char in ['+', '-', '*', '/', '^', '%']: style = "bold yellow"
                elif char == 'E': style = "bold magenta blink"
                elif char == '&': style = "green"
                elif char in ['~', '{', '}']: style = "bold blue"

                # Overlay effects
                for effect in self.effects:
                    if effect.x == world_x and effect.y == world_y:
                        entity_char = effect.symbol
                        style = effect.style
                        break

                # Overlay entities
                is_player = False

                # Check projectiles first
                for proj in self.projectiles:
                    if proj.x == world_x and proj.y == world_y:
                        entity_char = proj.symbol
                        style = "bold yellow"
                        break

                for entity in self.world.entities:
                    if isinstance(entity, Boss):
                        # Check all occupied cells
                        cells = entity.get_occupied_cells()
                        for i, (cx, cy) in enumerate(cells):
                            if cx == world_x and cy == world_y:
                                row_idx = (cy - entity.y)
                                col_idx = (cx - entity.x)
                                entity_char = entity.symbol_matrix[row_idx][col_idx]
                                style = "bold red"
                                break
                    elif entity.x == world_x and entity.y == world_y:
                        entity_char = entity.symbol
                        if entity == self.player:
                            style = "bold green reverse"
                            if self.invincible_timer > 0:
                                style += " blink"
                            is_player = True
                        elif isinstance(entity, Chaser):
                            style = "bold red"
                        elif isinstance(entity, RandomWalker):
                            style = "bold orange1"
                        elif isinstance(entity, Glitch):
                            style = "bold cyan blink"
                        elif isinstance(entity, Virus):
                            style = "bold purple"
                        break

                if is_invincible and (not is_player or force_dim):
                    if "dim" not in style:
                        style = "dim " + style

                text_grid.append(entity_char, style=style)
            text_grid.append("\n")

        return text_grid

    def render(self):
        layout = Layout()

        if self.state == "MENU":
            menu_text = Align.center(
                "[bold green]CALCULATOR SANDBOX: INFINITE[/bold green]\n\n"
                "[1] START NEW GAME\n"
                "[2] HELP / MANUAL\n"
                "[3] EXIT\n\n"
                "[dim]Use Keyboard 1, 2, 3[/dim]"
            )
            layout.update(Panel(menu_text, title="Main Menu", border_style="green"))

        elif self.state == "DIFFICULTY_SELECT":
            diff_text = Align.center(
                "[bold yellow]SELECT DIFFICULTY[/bold yellow]\n\n"
                "[1] EASY (Low Damage, Fast Player)\n"
                "[2] NORMAL (Standard)\n"
                "[3] HARD (High Damage, Fast Enemies)\n\n"
                "[B] BACK"
            )
            layout.update(Panel(diff_text, title="Difficulty", border_style="yellow"))

        elif self.state == "MODE_SELECT":
            mode_text = Align.center(
                "[bold cyan]SELECT GAME MODE[/bold cyan]\n\n"
                "[1] CHALLENGE (Score 200 & Escape under 3 min)\n"
                "[2] ENDLESS (Survive as long as possible)\n\n"
                "[B] BACK"
            )
            layout.update(Panel(mode_text, title="Mode", border_style="cyan"))

        elif self.state == "HELP":
            # Layout for HELP
            help_layout = Layout()
            help_layout.split_column(
                Layout(name="header", size=3),
                Layout(name="tables"),
                Layout(name="footer", size=3)
            )

            help_layout["header"].update(Align.center("[bold yellow]CALCULATOR SANDBOX: MANUAL[/bold yellow]"))

            # Tables for different categories
            tables_row = Layout()
            tables_row.split_row(
                Layout(name="col1"),
                Layout(name="col2")
            )

            # Table 1: Controls & Modes
            ctrl_table = Table(title="Controls & Modes", box=None, show_header=False)
            ctrl_table.add_row("[bold cyan]W/A/S/D[/bold cyan]", "Move / Navigate")
            ctrl_table.add_row("[bold red]Space[/bold red]", "Attack (Dynamic Range & DMG)")
            ctrl_table.add_row("[bold white]E[/bold white]", "AC (All Clear) Skill (Cost 100)")
            ctrl_table.add_row("[bold cyan]P[/bold cyan]", "Pause / Resume")
            ctrl_table.add_row("[bold cyan]Q[/bold cyan]", "Quit to Menu")
            ctrl_table.add_row("", "")
            ctrl_table.add_row("[bold green]LEVEL UP[/bold green]", "Collect Numbers/Kill to gain XP")
            ctrl_table.add_row("[bold yellow]MULTIPLIERS[/bold yellow]", "* and ^ capped at +50 Score")
            ctrl_table.add_row("[bold magenta]CHALLENGE[/bold magenta]", "Score 200 to reveal Exit Portal")
            ctrl_table.add_row("[bold magenta]PORTAL[/bold magenta]", "Shifts location every 15 seconds")

            # Table 2: Enemies
            enemy_table = Table(title="Enemies", box=None)
            enemy_table.add_column("Symbol", justify="center")
            enemy_table.add_column("Name")
            enemy_table.add_column("Traits")
            enemy_table.add_row("[bold red]X[/bold red]", "Chaser", "Persistent tracking")
            enemy_table.add_row("[bold orange1]?[/bold orange1]", "Walker", "Random movement")
            enemy_table.add_row("[bold cyan blink]G[/bold cyan blink]", "Glitch", "Teleports, high HP")
            enemy_table.add_row("[bold purple]V[/bold purple]", "Virus", "Very fast, low HP")
            enemy_table.add_row("[bold red][MATH][/bold red]", "BOSS", "Ranged attacks, multi-tile")

            # Table 3: Math & Strategy
            math_table = Table(title="Math & Strategy", box=None)
            math_table.add_column("Symbol", justify="center")
            math_table.add_column("Effect")
            math_table.add_row("[bold yellow]+ / -[/bold yellow]", "HP +10 / HP -10")
            math_table.add_row("[bold yellow]* / /[/bold yellow]", "Score x2 / Score /2")
            math_table.add_row("[bold yellow]^ / %[/bold yellow]", "Score^2 / Score Mod 10")
            math_table.add_row("[bold blue]~[/bold blue]", "Reverse Score (123 -> 321)")
            math_table.add_row("[bold blue]{ / }[/bold blue]", "Sort Score Asc / Desc")

            tables_row["col1"].update(Panel(ctrl_table, border_style="cyan"))
            tables_row["col2"].split_column(
                Layout(Panel(enemy_table, border_style="red")),
                Layout(Panel(math_table, border_style="yellow"))
            )

            help_layout["tables"].update(tables_row)
            help_layout["footer"].update(Align.center("[bold cyan]Press [B] or [Q] to return to Main Menu[/bold cyan]"))

            layout.update(help_layout)

        elif self.state == "PAUSED":
            layout.update(Panel(Align.center("[bold yellow]GAME PAUSED[/bold yellow]\n\n[P] RESUME\n[Q] QUIT"), title="PAUSED", border_style="yellow"))

        elif self.state == "LEVEL_UP":
            # Show game in background but dim it
            layout.split_row(
                Layout(name="map", ratio=3),
                Layout(name="sidebar", ratio=1)
            )

            # Dimmed map
            grid_render = self.get_renderable_grid(force_dim=True)
            layout["map"].update(Panel(grid_render, title=f"World ({self.player.x}, {self.player.y})", border_style="dim blue"))

            # Dimmed sidebar
            status_text = (
                f"[dim]MODE: {self.game_mode} ({self.difficulty})[/dim]\n"
                f"[dim]LEVEL: {self.player.level} (XP: {int(self.player.xp)}/{self.player.xp_next})[/dim]\n"
                f"[dim]{self.message}[/dim]\n\n"
                f"[dim]HEALTH: {self.player.health}/{self.player.max_health}[/dim]\n"
                f"[dim]SCORE: {self.player.score}[/dim]\n"
                f"[dim]STAMINA: {int(self.player.stamina)}/{self.player.max_stamina}[/dim]\n"
            )
            layout["sidebar"].update(Panel(status_text, title="System", border_style="dim white"))

            # Center the level up window on the whole screen using a separate Align
            # Actually, to make it look like a window, we can wrap the whole layout
            options_text = ""
            for i, opt in enumerate(self.level_up_options):
                options_text += f"[bold cyan][{i+1}][/bold cyan] {opt}\n"

            level_up_panel = Panel(
                Align.center(
                    f"\n[bold green]SYSTEM UPGRADE AVAILABLE (LEVEL {self.player.level})[/bold green]\n\n"
                    f"{options_text}\n"
                    "[dim]Select an optimization module (1-4)[/dim]\n"
                ),
                title="Level Up!",
                border_style="bold green",
                expand=False,
                padding=(1, 2)
            )

            # We use a special layout trick: we wrap the game in a panel, and then
            # try to put the level up window on top.
            # Since Layout doesn't support overlays, we'll put the Level Up window
            # in the center of the 'map' layout, which is the largest area.

            modal = Align.center(level_up_panel, vertical="middle")
            # To show the map BEHIND the modal, we'd need a custom renderable.
            # Instead, we'll just show the modal prominently in the map area.
            layout["map"].update(modal)

        elif self.state == "GAME":
            layout.split_row(
                Layout(name="map", ratio=3),
                Layout(name="sidebar", ratio=1)
            )

            grid_render = self.get_renderable_grid()
            layout["map"].update(Panel(grid_render, title=f"World ({self.player.x}, {self.player.y})", border_style="blue"))

            status_text = (
                f"[bold]MODE[/bold]: {self.game_mode} ({self.difficulty})\n"
                f"[bold cyan]LEVEL[/bold cyan]: {self.player.level} ([dim]XP: {int(self.player.xp)}/{self.player.xp_next}[/dim])\n"
                f"{self.message}\n\n"
                f"[bold green]HEALTH[/bold green]: {self.player.health}/{self.player.max_health}\n"
                f"[bold cyan]SCORE [/bold cyan]: {self.player.score}\n"
                f"[bold yellow]STAMINA[/bold yellow]: {int(self.player.stamina)}/{self.player.max_stamina}\n"
            )

            if self.game_mode == "CHALLENGE":
                color = "red" if self.timer < 30 else "white"
                status_text += f"[bold {color}]TIME LEFT[/bold {color}]: {self.timer:.1f}s\n\n"
            else:
                status_text += "\n"

            if self.invincible_timer > 0:
                status_text += f"[bold yellow]SHIELD: {self.invincible_timer:.1f}s[/bold yellow]\n\n"

            if self.exit_coords:
                ex, ey = self.exit_coords
                dx = ex - self.player.x
                dy = ey - self.player.y
                direction = ""
                if dy < 0: direction += "N"
                elif dy > 0: direction += "S"
                if dx < 0: direction += "W"
                elif dx > 0: direction += "E"
                if direction == "": direction = "HERE"

                status_text += f"[bold magenta blink]EXIT PORTAL: {direction} ({dx}, {dy})[/bold magenta blink]\n"
                status_text += f"[magenta]Relocating in: {self.exit_reset_timer:.1f}s[/magenta]\n\n"

            status_text += f"[dim]Inventory:[/dim]\n" + "\n".join(self.player.inventory)
            layout["sidebar"].update(Panel(status_text, title="System", border_style="white"))

        elif self.state == "GAME_OVER":
            color = "green" if "ESCAPED" in self.message else "red"
            game_over_text = Align.center(
                f"[bold {color}]{self.message}[/bold {color}]\n\n"
                f"Mode: {self.game_mode} | Diff: {self.difficulty}\n"
                f"Final Score: {self.player.score}\n\n"
                "[R] RESTART\n"
                "[Q] MAIN MENU"
            )
            layout.update(Panel(game_over_text, title="GAME OVER", border_style=color))

        return layout

    def run(self):
        with Live(self.render(), refresh_per_second=20, screen=True) as live:
            while self.running:
                self.handle_input()
                if self.state == "GAME":
                    self.update()
                live.update(self.render())
                time.sleep(0.05)
