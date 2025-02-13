#Created by Signus (I know its cringy I will keep this as a pen name or something)
import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 1920, 1080
GRID_SIZE = 20
FPS = 60
TIME_LIMIT = 300000  # 5 minutes in milliseconds

# Colors (RGB)
WHITE      = (255, 255, 255)   # Wall / background color
BLACK      = (0, 0, 0)         # Floor color
RED        = (255, 0, 0)
GREEN      = (0, 255, 0)
BLUE       = (0, 0, 255)
YELLOW     = (255, 255, 0)
GRAY       = (100, 100, 100)
ORANGE     = (255, 165, 0)     # Basic trap
DARKORANGE = (255, 140, 0)     # Spike trap (more damaging)
DARKGRAY   = (50, 50, 50)      # Panel background
LIGHTGRAY  = (200, 200, 200)   # Panel border

# Panel settings
# Legend panel (top left)
LEGEND_PANEL_X = 10
LEGEND_PANEL_Y = 10
LEGEND_PANEL_WIDTH = 220
LEGEND_PANEL_HEIGHT = 170
# Message log panel (top middle)
LOG_BOX_WIDTH  = 600
LOG_BOX_HEIGHT = 170
LOG_BOX_X = (WIDTH - LOG_BOX_WIDTH) // 2
LOG_BOX_Y = 10
# Equipment panel (top right)
EQUIP_PANEL_X = WIDTH - 230
EQUIP_PANEL_Y = 10
EQUIP_PANEL_WIDTH = 220
EQUIP_PANEL_HEIGHT = 170
# Quit button (lower right)
QUIT_BTN_WIDTH = 100
QUIT_BTN_HEIGHT = 50
QUIT_BTN_X = WIDTH - QUIT_BTN_WIDTH - 10
QUIT_BTN_Y = HEIGHT - QUIT_BTN_HEIGHT - 10

# DnD mechanics base value
BASE_ATTACK_BONUS = 4

class Direction(Enum):
    UP    = (0, -1)
    DOWN  = (0, 1)
    LEFT  = (-1, 0)
    RIGHT = (1, 0)

class Entity:
    def __init__(self, x, y, color, char):
        self.x = x
        self.y = y
        self.color = color
        self.char = char

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, GREEN, '@')
        self.max_hp = 30
        self.hp = self.max_hp
        self.ac = 14
        self.weapon = "Dagger"
        self.weapon_damage = "1d6"
        self.inventory = []
        self.level = 1
        self.xp = 0
        self.xp_to_level = 20
        self.attack_bonus = BASE_ATTACK_BONUS

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_level
        self.xp_to_level += 10
        self.max_hp += 5
        self.hp = self.max_hp
        self.ac += 1
        self.attack_bonus += 1
        return f"You leveled up to {self.level}!"

class Enemy(Entity):
    def __init__(self, x, y, name, hp, ac, damage, xp_reward):
        super().__init__(x, y, RED, 'E')  # default color; will be set later
        self.name = name
        self.hp = hp
        self.ac = ac
        self.damage = damage
        self.xp_reward = xp_reward

class Boss(Enemy):
    def __init__(self, x, y, name, hp, ac, damage, xp_reward, heads=0):
        super().__init__(x, y, name, hp, ac, damage, xp_reward)
        self.heads = heads
        self.is_hydra = name == "5 head hydra"

class Loot(Entity):
    def __init__(self, x, y, name, damage):
        super().__init__(x, y, YELLOW, '$')
        self.name = name
        self.damage = damage
        self.rarity = random.choice(["Common", "Rare", "Epic"])

def roll_dice(dice_str):
    num, sides = map(int, dice_str.split('d'))
    return sum(random.randint(1, sides) for _ in range(num))

############################################
# Enemy Color and Type Utility
############################################

def get_enemy_color(name):
    colors = {
        "Goblin": (34, 139, 34),         # Forest Green
        "Goblin King": (0, 100, 0),        # Dark Green
        "Goblin Warlord": (85, 107, 47),   # Olive Drab
        "Orc": (139, 69, 19),              # Saddle Brown
        "Orc King": (160, 82, 45),         # Sienna
        "Orc Warlord": (165, 42, 42),       # Brownish Red
        "Sneezer": (138, 43, 226),         # Blue Violet
        "Dragon": (128, 0, 128),           # Purple
        "5 head hydra": (255, 20, 147)      # Deep Pink
    }
    return colors.get(name, RED)

############################################
# Dungeon Generation, Connectivity & Traps
############################################

def generate_dungeon():
    """
    Generates a dungeon with 10 rooms (room 0 is the starting room).
    Floors (rooms and corridors) are drawn as solid rectangles while
    walls are rendered as a smooth continuous background.
    Additional traps are placed.
    Returns the dungeon grid (2D list) and list of room tuples.
    """
    room_count = 10
    dungeon_width = WIDTH // GRID_SIZE
    dungeon_height = HEIGHT // GRID_SIZE
    dungeon = [[WHITE for _ in range(dungeon_width)] for _ in range(dungeon_height)]
    rooms = []
    
    for _ in range(room_count):
        w = random.randint(5, 8)
        h = random.randint(5, 8)
        x = random.randint(1, dungeon_width - w - 1)
        y = random.randint(1, dungeon_height - h - 1)
        room = (x, y, w, h)
        rooms.append(room)
    
    for room in rooms:
        for i in range(room[0], room[0] + room[2]):
            for j in range(room[1], room[1] + room[3]):
                dungeon[j][i] = BLACK

    connect_all_rooms(dungeon, rooms)
    add_traps(dungeon, rooms)
    
    return dungeon, rooms

def connect_all_rooms(dungeon, rooms):
    def room_center(room):
        x, y, w, h = room
        return (x + w // 2, y + h // 2)
    
    connected = [rooms[0]]
    remaining = rooms[1:]
    
    while remaining:
        best_distance = None
        best_pair = None
        best_room = None
        for room in remaining:
            cx, cy = room_center(room)
            for c_room in connected:
                ccx, ccy = room_center(c_room)
                dist = abs(cx - ccx) + abs(cy - ccy)
                if best_distance is None or dist < best_distance:
                    best_distance = dist
                    best_pair = ((ccx, ccy), (cx, cy))
                    best_room = room
        (cx, cy), (rx, ry) = best_pair
        for x in range(min(cx, rx), max(cx, rx) + 1):
            dungeon[cy][x] = BLACK
        for y in range(min(cy, ry), max(cy, ry) + 1):
            dungeon[y][rx] = BLACK
        
        connected.append(best_room)
        remaining.remove(best_room)

def add_traps(dungeon, rooms):
    """
    For each non-starting room, with an 80% chance, place a trap.
    Randomly choose between a normal trap (ORANGE) and a spike trap (DARKORANGE).
    """
    for room in rooms[1:]:
        if room[2] < 3 or room[3] < 3:
            continue
        if random.random() < 0.8:
            trap_x = random.randint(room[0] + 1, room[0] + room[2] - 2)
            trap_y = random.randint(room[1] + 1, room[1] + room[3] - 2)
            dungeon[trap_y][trap_x] = DARKORANGE if random.random() < 0.5 else ORANGE

############################################
# Enemy and Loot Spawning (Progressive)
############################################

def spawn_enemies(rooms):
    """
    Spawns enemies in the following order (rooms 1-9):
      1. Small Monster - Goblin
      2. Large Monster - Goblin King
      3. Boss - Goblin Warlord
      4. Small Monster - Orc
      5. Large Monster - Orc King
      6. Large Monster - Orc Warlord
      7. Small Monster - Sneezer
      8. Large Monster - Dragon
      9. Final Boss - 5 head hydra
    """
    enemies = []
    enemy_list = [
        {"name": "Goblin", "hp": 10, "ac": 10, "damage": "1d4", "xp_reward": 5},
        {"name": "Goblin King", "hp": 20, "ac": 12, "damage": "1d6", "xp_reward": 10},
        {"name": "Goblin Warlord", "hp": 25, "ac": 14, "damage": "1d8", "xp_reward": 20},
        {"name": "Orc", "hp": 10, "ac": 10, "damage": "1d4", "xp_reward": 5},
        {"name": "Orc King", "hp": 20, "ac": 12, "damage": "1d6", "xp_reward": 10},
        {"name": "Orc Warlord", "hp": 25, "ac": 14, "damage": "1d8", "xp_reward": 20},
        {"name": "Sneezer", "hp": 8, "ac": 9, "damage": "1d3", "xp_reward": 4},
        {"name": "Dragon", "hp": 40, "ac": 15, "damage": "2d6", "xp_reward": 30},
        {"name": "5 head hydra", "hp": 80, "ac": 16, "damage": "2d8", "xp_reward": 50, "heads": 5}
    ]
    
    # Spawn one enemy per room using rooms[1] through rooms[9]
    for idx, enemy_data in enumerate(enemy_list, start=1):
        room = rooms[idx]
        x = room[0] + room[2] // 2
        y = room[1] + room[3] // 2
        if "heads" in enemy_data:
            enemy = Boss(x, y, enemy_data["name"], enemy_data["hp"], enemy_data["ac"],
                         enemy_data["damage"], enemy_data["xp_reward"], heads=enemy_data["heads"])
        else:
            enemy = Enemy(x, y, enemy_data["name"], enemy_data["hp"], enemy_data["ac"],
                          enemy_data["damage"], enemy_data["xp_reward"])
        enemy.color = get_enemy_color(enemy_data["name"])
        enemies.append(enemy)
    
    return enemies

def spawn_loot(enemy):
    if random.random() < 0.8:
        return Loot(enemy.x, enemy.y, 
                    random.choice(["Sword", "Axe", "Bow", "Magic Staff"]),
                    random.choice(["1d8", "2d6", "1d10"]))
    return None

############################################
# Drawing Functions (Smooth Floor Only)
############################################

def draw_dungeon(screen, dungeon):
    """
    Draws only the floor tiles (rooms, corridors, and traps) as smooth rectangles.
    The walls (background) remain a continuous smooth color.
    """
    for y, row in enumerate(dungeon):
        for x, cell in enumerate(row):
            if cell in (BLACK, ORANGE, DARKORANGE):
                pygame.draw.rect(screen, cell, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))

def draw_message_log(screen, font, message_log, scroll_offset):
    log_rect = pygame.Rect(LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT)
    pygame.draw.rect(screen, DARKGRAY, log_rect)
    pygame.draw.rect(screen, LIGHTGRAY, log_rect, 2)
    line_height = font.get_height() + 2
    max_lines = LOG_BOX_HEIGHT // line_height
    start_index = max(0, len(message_log) - max_lines - scroll_offset)
    displayed_lines = message_log[start_index : start_index + max_lines]
    for i, line in enumerate(displayed_lines):
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (LOG_BOX_X + 5, LOG_BOX_Y + 5 + i * line_height))

def draw_legend_panel(screen, font, enemies, scroll_offset):
    panel_rect = pygame.Rect(LEGEND_PANEL_X, LEGEND_PANEL_Y, LEGEND_PANEL_WIDTH, LEGEND_PANEL_HEIGHT)
    pygame.draw.rect(screen, DARKGRAY, panel_rect)
    pygame.draw.rect(screen, LIGHTGRAY, panel_rect, 2)
    title_surface = font.render("Enemy Legend", True, WHITE)
    screen.blit(title_surface, (LEGEND_PANEL_X + 5, LEGEND_PANEL_Y + 5))
    line_height = font.get_height() + 2
    # Build list of legend entries (unique enemy names)
    legend_entries = list({enemy.name: enemy.color for enemy in enemies}.items())
    max_lines = (LEGEND_PANEL_HEIGHT - 25) // line_height
    start_index = scroll_offset
    displayed_entries = legend_entries[start_index:start_index + max_lines]
    offset_y = LEGEND_PANEL_Y + 25
    for name, color in displayed_entries:
        square_rect = pygame.Rect(LEGEND_PANEL_X + 5, offset_y, 15, 15)
        pygame.draw.rect(screen, color, square_rect)
        text_surface = font.render(name, True, WHITE)
        screen.blit(text_surface, (LEGEND_PANEL_X + 25, offset_y))
        offset_y += line_height

def draw_equipment_panel(screen, font, player, scroll_offset):
    panel_rect = pygame.Rect(EQUIP_PANEL_X, EQUIP_PANEL_Y, EQUIP_PANEL_WIDTH, EQUIP_PANEL_HEIGHT)
    pygame.draw.rect(screen, DARKGRAY, panel_rect)
    pygame.draw.rect(screen, LIGHTGRAY, panel_rect, 2)
    title_surface = font.render("Equipment", True, WHITE)
    screen.blit(title_surface, (EQUIP_PANEL_X + 5, EQUIP_PANEL_Y + 5))
    line_height = font.get_height() + 2
    # Prepare list of equipment lines
    lines = []
    lines.append(f"Weapon: {player.weapon} ({player.weapon_damage})")
    if player.inventory:
        lines.append("Inventory:")
        for item in player.inventory:
            lines.append(f"- {item.name} ({item.damage})")
    else:
        lines.append("Inventory: Empty")
    max_lines = (EQUIP_PANEL_HEIGHT - 25) // line_height
    start_index = scroll_offset
    displayed_lines = lines[start_index:start_index + max_lines]
    offset_y = EQUIP_PANEL_Y + 25
    for line in displayed_lines:
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (EQUIP_PANEL_X + 5, offset_y))
        offset_y += line_height

def draw_quit_button(screen, font):
    btn_rect = pygame.Rect(QUIT_BTN_X, QUIT_BTN_Y, QUIT_BTN_WIDTH, QUIT_BTN_HEIGHT)
    pygame.draw.rect(screen, DARKGRAY, btn_rect)
    pygame.draw.rect(screen, LIGHTGRAY, btn_rect, 2)
    text_surface = font.render("Quit", True, WHITE)
    text_rect = text_surface.get_rect(center=btn_rect.center)
    screen.blit(text_surface, text_rect)

def draw_instructions(screen, font):
    instructions = "WASD: Move | Mouse Wheel: Scroll Panels | Click Quit to exit"
    text_surface = font.render(instructions, True, BLACK)
    screen.blit(text_surface, (WIDTH - text_surface.get_width() - 10, HEIGHT - QUIT_BTN_HEIGHT - text_surface.get_height() - 20))

############################################
# Main Game Loop
############################################

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dungeon Crawl - 5 Minute Adventure")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 18)
    
    dungeon, rooms = generate_dungeon()
    player = Player(rooms[0][0] + 2, rooms[0][1] + 2)
    enemies = spawn_enemies(rooms)
    loot_items = []
    entities = [player] + enemies

    start_time = pygame.time.get_ticks()
    message_log = ["Welcome to the Dungeon Crawl!"]
    message_scroll_offset = 0
    legend_scroll_offset = 0
    equip_scroll_offset = 0
    win_time = None

    running = True
    while running:
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_time = max(0, TIME_LIMIT - elapsed_time) // 1000
        if remaining_time <= 0:
            message_log.append("Time's up! Game Over!")
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Define panel rectangles
                log_rect = pygame.Rect(LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT)
                legend_rect = pygame.Rect(LEGEND_PANEL_X, LEGEND_PANEL_Y, LEGEND_PANEL_WIDTH, LEGEND_PANEL_HEIGHT)
                equip_rect = pygame.Rect(EQUIP_PANEL_X, EQUIP_PANEL_Y, EQUIP_PANEL_WIDTH, EQUIP_PANEL_HEIGHT)
                if event.button in (4, 5):  # Mouse wheel scroll
                    if legend_rect.collidepoint(mouse_pos):
                        if event.button == 4:
                            legend_scroll_offset += 1
                        elif event.button == 5:
                            legend_scroll_offset = max(legend_scroll_offset - 1, 0)
                    elif equip_rect.collidepoint(mouse_pos):
                        if event.button == 4:
                            equip_scroll_offset += 1
                        elif event.button == 5:
                            equip_scroll_offset = max(equip_scroll_offset - 1, 0)
                    elif log_rect.collidepoint(mouse_pos):
                        if event.button == 4:
                            message_scroll_offset = min(message_scroll_offset + 1, max(0, len(message_log) - 1))
                        elif event.button == 5:
                            message_scroll_offset = max(message_scroll_offset - 1, 0)
                    # Otherwise, do nothing.
                elif event.button == 1:  # Left click
                    quit_btn_rect = pygame.Rect(QUIT_BTN_X, QUIT_BTN_Y, QUIT_BTN_WIDTH, QUIT_BTN_HEIGHT)
                    if quit_btn_rect.collidepoint(mouse_pos):
                        running = False
            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_w: dx, dy = Direction.UP.value
                if event.key == pygame.K_s: dx, dy = Direction.DOWN.value
                if event.key == pygame.K_a: dx, dy = Direction.LEFT.value
                if event.key == pygame.K_d: dx, dy = Direction.RIGHT.value

                new_x = player.x + dx
                new_y = player.y + dy
                dungeon_width = WIDTH // GRID_SIZE
                dungeon_height = HEIGHT // GRID_SIZE
                if 0 <= new_x < dungeon_width and 0 <= new_y < dungeon_height:
                    cell = dungeon[new_y][new_x]
                    if cell in (BLACK, ORANGE, DARKORANGE):
                        player.x = new_x
                        player.y = new_y
                        if cell in (ORANGE, DARKORANGE):
                            dungeon[new_y][new_x] = BLACK
                            trap_roll = roll_dice("1d20")
                            trap_dc = 12
                            if trap_roll < trap_dc:
                                damage = roll_dice("1d6") if cell == ORANGE else roll_dice("1d8")
                                player.hp -= damage
                                message_log.append(f"You triggered a trap and took {damage} damage!")
                            else:
                                message_log.append("You narrowly avoided a trap!")
                        
                        for enemy in enemies[:]:
                            if enemy.x == player.x and enemy.y == player.y:
                                message_log.append(f"Encounter with {enemy.name} (AC {enemy.ac})!")
                                attack_roll = roll_dice("1d20") + player.attack_bonus
                                message_log.append(f"You attack with a roll of {attack_roll}!")
                                if attack_roll >= enemy.ac:
                                    damage = roll_dice(player.weapon_damage)
                                    enemy.hp -= damage
                                    message_log.append(f"Hit! You deal {damage} damage.")
                                    if enemy.hp <= 0:
                                        message_log.append(f"{enemy.name} defeated!")
                                        player.xp += enemy.xp_reward
                                        enemies.remove(enemy)
                                        entities.remove(enemy)
                                        loot = spawn_loot(enemy)
                                        if loot:
                                            loot_items.append(loot)
                                            entities.append(loot)
                                        if player.xp >= player.xp_to_level:
                                            lvl_msg = player.level_up()
                                            message_log.append(lvl_msg)
                                else:
                                    message_log.append("Your attack missed!")
                                
                                if enemy in enemies:
                                    enemy_attack = roll_dice("1d20") + 2
                                    message_log.append(f"{enemy.name} attacks with a roll of {enemy_attack}!")
                                    if enemy_attack >= player.ac:
                                        enemy_damage = roll_dice(enemy.damage)
                                        if enemy.name == "5 head hydra" and enemy.is_hydra:
                                            if random.random() < 0.5:
                                                enemy.heads -= 1
                                                message_log.append("You cut off one of the Hydra's heads!")
                                                if enemy.heads <= 0:
                                                    enemy.hp = 0
                                            else:
                                                player.hp -= enemy_damage
                                                message_log.append(f"{enemy.name} hits you for {enemy_damage} damage!")
                                        else:
                                            player.hp -= enemy_damage
                                            message_log.append(f"{enemy.name} hits you for {enemy_damage} damage!")
                                    else:
                                        message_log.append(f"{enemy.name} missed!")
                                    if player.hp <= 0:
                                        message_log.append("YOU DIED! Game Over!")
                                        running = False

                        for item in loot_items[:]:
                            if item.x == player.x and item.y == player.y:
                                player.inventory.append(item)
                                player.weapon = item.name
                                player.weapon_damage = item.damage
                                message_log.append(f"You picked up and equipped {item.name} ({item.damage})!")
                                loot_items.remove(item)
                                entities.remove(item)
        
        # Win condition: if no enemies remain, display "You Win!" and exit after 10 seconds.
        if not enemies:
            if win_time is None:
                win_time = pygame.time.get_ticks()
            big_font = pygame.font.SysFont('Arial', 72)
            win_text = big_font.render("You Win!", True, BLUE)
            win_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, win_rect)
            if pygame.time.get_ticks() - win_time > 10000:
                running = False

        screen.fill(WHITE)
        draw_dungeon(screen, dungeon)
        for entity in entities:
            pygame.draw.rect(screen, entity.color, (entity.x * GRID_SIZE, entity.y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        
        # HUD (player stats) at bottom left
        hud_text = [
            f"HP: {player.hp}/{player.max_hp}",
            f"AC: {player.ac}",
            f"Level: {player.level}  XP: {player.xp}/{player.xp_to_level}",
            f"Time Left: {remaining_time} sec"
        ]
        for i, text_str in enumerate(hud_text):
            text = font.render(text_str, True, BLACK)
            screen.blit(text, (10, HEIGHT - 100 + i * 20))
        
        draw_legend_panel(screen, font, enemies, legend_scroll_offset)
        draw_message_log(screen, font, message_log, message_scroll_offset)
        draw_equipment_panel(screen, font, player, equip_scroll_offset)
        draw_quit_button(screen, font)
        draw_instructions(screen, font)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()

if __name__ == "__main__":
    main()
#Created by Signus (Yes, I know its cringy)