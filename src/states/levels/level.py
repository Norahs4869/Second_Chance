import csv
import random

import pygame as pg

import src.entities.enemies.enemy as enemy
import src.states.menu.menus as menus
import src.states.menu.winscreen as winscreen
from src.constants import *
from src.entities.enemies.archer import archer
from src.entities.enemies.eyeball import Eyeball
from src.entities.enemies.skeleton import Skeleton
from src.entities.enemies.wolf import Wolf
from src.entities.enemies.goblin import Goblin
from src.entities.player import Player
from src.objects.tiles import Tile
from src.states.minigames.minigame import Minigame
from src.states.state import State
from src.utils.leaderboard import LeaderboardManager
from src.utils.timer import Timer


# Necessary to access minigames from the minigames package
from src.states.minigames import *

class Level(State):
    """General level class.
    
    Contains all of the attributes and behavior that a level should contain.

    Args:
        level (int): Level number.
        music_file (str): Music file name for the current level.
        imgArr (list[str], optional): List of background image paths. Defaults 
            to None.
    """

    def __init__(self, level: int, music_file: str, imgArr=None):
        super().__init__()
        self.level = level
        self.scroll = 0
        self.level_scroll = 0
        self.timer = Timer(start=True)  # Timer starts when it's instantiated
        self.init_tiles()
        self.init_sprites()
        self.init_attributes()
        self.init_background(imgArr)
        self.init_music(music_file)

    def handle_events(self, events):
        for event in events:
            if event.type != pg.KEYDOWN:  # Ignore all inputs except key presses
                return
            if event.key == pg.K_ESCAPE:  # Open pause menu
                self.manager.set_state(menus.PauseMenu(self.timer), save_prev=True)

    def update(self, events):
        self.current_time = self.timer.get_time(ms=True)

        self.scroll = self.player.update()
        self.enemies.update(self.player)
        self.objects.update(self.scroll)
        self.tiles.update(self.scroll)

        # Check for collision between player's melee attacks and enemy

        collisions = pg.sprite.groupcollide(self.player.melee_attacks, self.enemies, False,
                                            False)  # Change False to True to remove the melee attack sprite upon collision
        range_attack_collisions = pg.sprite.groupcollide(self.player.range_attacks, self.enemies, True, False)

        for attack, enemies in collisions.items():
            for enemy in enemies:
                enemy.decrease_health(attack.damage_value)
        for attack, enemies in range_attack_collisions.items():
            for enemy in enemies:
                enemy.decrease_health(attack.damage_value)

        for portal in self.portals:
            if portal.rect.colliderect(self.player.rect):
                if len(self.enemies) == 0:  # If no enemies left
                    # Transition to the start menu state

                    timer = LeaderboardManager(self.game)
                    timer.update_leaderboard(self.game.username, self.current_time)

                    self.manager.set_state(winscreen.WinScreen)
                else:
                    self.last_portal_time = self.current_time

        self.update_text()

        # Check for player death
        if self.player.health <= 0:
            self.timer.pause()
            self.player.SC_count += 1
            self.manager.set_state(
                globals()[random.choice(self.minigames)],  # Select a random minigame
                save_prev=True)

    def draw(self):
        self.draw_bg()
        self.portals.draw(self.screen)
        self.enemies.draw()
        self.objects.draw(self.screen)
        self.tiles.draw(self.screen)
        self.player.draw()
        self.platforms.draw(self.screen)
        self.draw_health_bar()
        self.draw_text_surfaces()

    def init_tiles(self):
        """Initializes level tiles."""

        self.world_data = []
        self.tile_list = []

        for x in range(TILE_TYPES):
            img = pg.image.load(f"assets/tiles/{x}.png")
            img = pg.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            self.tile_list.append(img)

        # create empty tile list
        for row in range(ROWS):
            r = [-1] * COLS
            self.world_data.append(r)
        # load in level data and create world
        with open(f"assets/csvs/level{1}_data.csv", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    self.world_data[x][y] = int(tile)

    def init_sprites(self):
        """Initializes level sprites."""

        self.platforms = pg.sprite.Group()
        self.portals = pg.sprite.Group()
        self.tiles = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        self.enemies = enemy.EnemyGroup()
        self.world = World(self.tile_list, self.objects, self.tiles, self.platforms, self.enemies)
        self.player = Player(100, 100, self.platforms, self.portals, self.tiles, self.enemies)

        self.world.process_data(self.world_data)  # call method to process csv data
        self.add_portal()

    def init_attributes(self):
        """Initializes level attributes."""

        # Timed events
        self.current_time = 0
        self.last_portal_time = 0
        self.next_portal_time = 0  # Next time to display message
        self.instruction_duration = 5  # Amount of seconds to display message

        # A list of all current minigames
        self.minigames = [cls.__name__ for cls in Minigame.__subclasses__()]

        self.controls = self.get_text_surface(
            "Press 'Escape' to pause", "white", font_size=36
        )
        self.kill_instruction = self.get_text_surface(
            "You must kill all enemies before you can enter the portal", "red", font_size=36
        )
        self.timer_text = self.get_text_surface(
            f"Level {self.level} Time: {self.timer.get_time()}", "white",
            font_size=36
        )
        self.health_text_surface = self.get_text_surface(
            f"Health: {self.player.health}", "white", font_size=36
        )

    def init_background(self, imgArr):
        """Initializes level background.

        Args:
            imgArr (list[str]): List of background image paths.
        """

        self.bg_images = []

        if imgArr is not None:
            for i in range(1, 6):
                bg_image = pg.image.load(f"assets/backgrounds/plx-{i}.png").convert_alpha()
                bg_image = pg.transform.smoothscale(bg_image, self.screen.get_size())
                self.bg_images.append(bg_image)
                self.bg_width = self.bg_images[0].get_width()

    def init_music(self, music_file):
        """Initializes level music.

        Args:
            music_file (str): Music file name to load.
        """

        # Load background music
        pg.mixer.music.load(os.path.join("assets/music", f"{music_file}"))
        self.volume = menus.volume  # Initial volume level (between 0 and 1)
        pg.mixer.music.set_volume(menus.volume)
        pg.mixer.music.play(-1)  # Start playing background music on a loop

    def update_text(self):
        """Updates all text surfaces displayed within the level."""

        self.timer_text = self.get_text_surface(
            f"Level {self.level} Time: {self.timer.get_time()}", "white",
            font_size=36
        )
        self.health_text_surface = self.get_text_surface(
            f"Health: {self.player.health}", "white", font_size=36
        )

        # Determine if kill_instruction should be displayed on the screen
        if self.current_time > self.next_portal_time:
            if self.last_portal_time > self.next_portal_time:
                self.next_portal_time = self.last_portal_time + self.instruction_duration
            self.kill_instruction = pg.Surface((0, 0))
        else:
            self.kill_instruction = self.get_text_surface(
                "You must kill all enemies before you can enter the portal", "red", font_size=36
            )

    def draw_bg(self):
        """
        Draws the background images according to the player's scroll value.
        """
        for x in range(25):
            speed = 1
            for i in self.bg_images:
                self.screen.blit(i, ((x * self.bg_width) - self.player.level_scroll * speed, 0))
                speed += 0.2

    def draw_health_bar(self):
        """Draws the player's health bar."""

        # Calculate the width of the health bar based on current health
        health_bar_width = (self.player.health / self.player.max_health) * self.player.health_bar_length
        # Calculate the position of the health bar above the player
        health_bar_x = self.player.rect.x - (self.player.rect.width * (self.player.scale_factor - 1)) / 2
        health_bar_y = self.player.rect.y - 20  # Adjust this value to position the health bar properly
        # Draw the health bar
        pg.draw.rect(self.screen, (255, 0, 0),
                     (health_bar_x, health_bar_y, self.player.health_bar_length, self.player.health_bar_height))
        pg.draw.rect(self.screen, self.player.health_bar_color,
                     (health_bar_x, health_bar_y, health_bar_width, self.player.health_bar_height))

    def draw_text_surfaces(self):
        """Draws all of the visible text surfaces within the level."""

        self.screen.blit(self.controls, (20, 20))
        self.screen.blit(self.health_text_surface, (20, 50))
        self.screen.blit(self.timer_text, (self.screen.get_width() - 220, 20))
        self.screen.blit(self.kill_instruction, (100, 100))


class World:
    """
    The World class is responsible for loading all of the tiles within the
    level.

    Args:
        tile_list (list[pygame.Surface]): List of tiles.
        objects (pygame.sprite.Group): Group of objects.
        tiles (pygame.sprite.Group): Group of tiles.
        platform_group (pygame.sprite.Group): Group of platforms.
        enemy_group (pygame.sprite.Group): Group of enemies.
    """

    def __init__(self, tile_list, objects, tiles, platform_group, enemy_group):
        self.tile_list = tile_list
        self.objects = objects
        self.tiles = tiles
        self.platform_group = platform_group
        self.enemy_group = enemy_group

    def process_data(self, data):
        """
        Adds all platforms, tiles, and enemies to their corresponding
        group at their specified spawn position.

        Args:
            data (list[list[int]]): 2D list of integers that represent
                different sprites.
        """
        # iterate through data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                collision = True
                if tile in [11, 13, 14, 16, 17, 18, 19, 20]:
                    collision = False
                if tile >= 0:
                    if tile >= 0 and tile <= 8:
                        pass
                    elif tile > 9 and tile <= 10:
                        pass  # water(potentially added later to kill player when colliding)
                    elif tile >= 11 and tile <= 14:
                        pass  # decoration
                    elif tile == 15:
                        pass  # create player
                    elif tile == 16:
                        enemy = Eyeball(x * TILE_SIZE, y * TILE_SIZE, self.platform_group, self.tiles)
                        self.enemy_group.add(enemy)
                    elif tile == 17:
                        enemy = Skeleton(x * TILE_SIZE, y * TILE_SIZE, self.platform_group, self.tiles)
                        self.enemy_group.add(enemy)
                    elif tile == 18:
                        enemy = archer(x * TILE_SIZE, y * TILE_SIZE, self.platform_group, self.tiles)
                        self.enemy_group.add(enemy)
                    elif tile == 19:
                        enemy = Wolf(x * TILE_SIZE, y * TILE_SIZE, self.platform_group, self.tiles)
                        self.enemy_group.add(enemy)
                    elif tile == 20:
                        enemy = Goblin(x * TILE_SIZE, y * TILE_SIZE, self.platform_group, self.tiles)
                        self.enemy_group.add(enemy)
                    img = self.tile_list[tile]
                    t = Tile(img, x * TILE_SIZE, y * TILE_SIZE, tile)
                    if collision:
                        self.tiles.add(t)
                    else:
                        self.objects.add(t)
