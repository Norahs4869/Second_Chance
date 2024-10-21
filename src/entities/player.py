import math
import time

import pygame as pg

from src.constants import *
from src.entities.attack import MeleeAttack
from src.entities.attack import RangeAttack
from src.utils.timer import Timer


class Player(pg.sprite.Sprite):
    """Represents the character controlled by the user.

    Args:
        x (int): x position to spawn at.
        y (int): y position to spawn at.
        platform_group (pygame.sprite.Group): Group to check collision with.
        portal_group (pygame.sprite.Group): Group to check collision with.
        obstacle_list (pygame.sprite.Group): Group to check collision with.
        enemies_group (pygame.sprite.Group): Group to check collision with.
    """

    def __init__(
            self,
            x: int, y: int,
            platform_group: pg.sprite.Group,
            portal_group: pg.sprite.Group,
            obstacle_list: pg.sprite.Group,
            enemies_group: pg.sprite.Group
    ):
        super().__init__()

        self.screen = pg.display.get_surface()
        self.size = (100, 100)
        self.animation = [
            pg.transform.scale(pg.image.load(f"assets/characters/R{i}.png"), self.size).convert_alpha()
            for i in range(1, 10)]

        self.image = pg.image.load(f"assets/characters/stand.png")
        self.image = pg.transform.scale(self.image,
                                        (self.image.get_width() * 2, self.image.get_height() * 2))  # Scale the sprite
        self.idle = self.image
        self.rect = self.image.get_rect()

        # Set the rect for the sprite
        self.rect.center = (x, y)
        self.rect.width //= 2
        self.rect.height //= 2
        self.sprite_x = 0
        self.sprite_y = 0

        # Player actions and state
        self.is_moving = False
        self.on_ground = False
        self.is_jumping = False
        self.direction = "right"
        self.last_ground_pos = pg.Rect(0, 0, 0, 0)

        # Player inputs
        self.up_press = False
        self.left_press = False
        self.right_press = False
        self.movement_pressed = False
        self.melee_pressed = False
        self.ranged_pressed = False

        # Animation variables
        self.index = 0
        self.counter = 0
        self.walk_cooldown = 3
        self.scroll = 0
        self.level_scroll = 0
        self.scroll_amount = 3

        self.platform_group = platform_group
        self.portal_group = portal_group
        self.obstacle_list = obstacle_list
        self.scale_factor = 2
        self.enemies_group = enemies_group

        self.invincible = False  # Attribute to track player's invincibility state
        self.invincible_duration = 1.5  # Duration of invincibility frames in seconds
        self.last_hit_time = 0  # Time when the player was last hit

        self.timer = Timer(start=True)
        self.last_health_increase_time = 0
        self.health_duration = 6  # How often to increase HP in seconds
        self.health_increase_amount = 10

        self.melee_attacks = pg.sprite.Group()  # Group for managing melee attack instances
        self.range_attacks = pg.sprite.Group()

        self.attack_initiated = False
        self.rangeAttack_initiated = False

        self.last_ranged_attack_time = 0  # Initialize with 0
        self.ranged_attack_cooldown = 0  # Cooldown duration for the ranged attack in seconds. Changed to no cooldown when using arrows

        self.ranged_attack_count = 0  # Initialize the counter for ranged attacks
        self.ranged_attack_max = 100  # Maximum number of ranged attack uses the player has. Changed to 100 arrows, it was 10 

        # Load the sound effects
        self.hit_sound = pg.mixer.Sound("assets/soundeffects/playerhit.mp3")
        self.melee_attack_sound = pg.mixer.Sound("assets/soundeffects/meleeattack.mp3")
        self.ranged_attack_sound = pg.mixer.Sound("assets/soundeffects/lasersound.wav")

        self.font = pg.font.Font(None, 20)  # TODO

        self.speed = 0.5
        self.gravity = 0.5
        self.vel_y = 0
        self.jump_strength = -13

        # Healthbar
        self.health = 100  # Initial health value
        self.max_health = 100  # Maximum health value
        self.health_bar_length = 100  # Length of the health bar
        self.health_bar_height = 10  # Height of the health bar
        self.health_bar_color = (0, 255, 0)  # Green color for the health bar
        self.SC_count = 0

        # Define hitbox
        self.hitbox = pg.Rect(x, y, self.rect.width, self.rect.height)

    def update(self):
        """Updates the position of the player's rect.

        Returns:
            int: The amount for other visible sprites to scroll on the screen.
        """
        self.dx = 0
        self.dy = 0
        self.scroll = 0

        # Apply gravity
        self.vel_y += self.gravity
        self.dy += self.vel_y

        # Set variables depending on input
        self.input()

        # Move depending on variables set
        self.move()

        # Get current time to check for timed events
        current_time = self.timer.get_time(ms=True)

        self.handle_animation()

        # If falling, we're not on ground
        if self.vel_y > 0:
            self.on_ground = False

        # Check collision with platforms
        self.check_collision()

        # Kill player if they have fallen into a gap
        if self.rect.top - 50 >= self.screen.get_height():
            self.health = 0

        # Jumping
        if self.on_ground and self.is_jumping:
            self.jump()

        # Update rect
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Update hitbox
        self.hitbox.y += self.vel_y

        self.check_invincibility()

        # Increase HP after a certain amount of time has passed
        if current_time - self.last_health_increase_time > self.health_duration:
            self.increase_health(self.health_increase_amount)
            self.last_health_increase_time = current_time

        # Keep rect in screen
        self.rect.x = max(0, min(self.screen.get_width() - self.rect.width, self.rect.x))

        # To center sprite in rect
        self.sprite_x = self.rect.x + (self.rect.width - self.image.get_width()) // 2
        self.sprite_y = self.rect.y + (self.rect.height - self.image.get_height()) // 2

        # Create a melee attack instance at the player's position
        if self.direction == "right":
            melee_attack = MeleeAttack(self.rect.centerx + 20, self.rect.centery, self.direction, damage_value=25)
            range_attack = RangeAttack(self.rect.centerx + 10, self.rect.centery, self.direction, damage_value=25)
        else:
            melee_attack = MeleeAttack(self.rect.centerx - 20, self.rect.centery, self.direction, damage_value=25)
            range_attack = RangeAttack(self.rect.centerx - 10, self.rect.centery, self.direction, damage_value=25)

        # Check for initiating attack
        if self.melee_pressed and not self.attack_initiated:
            self.melee_attack_sound.play()
            self.melee_attacks.add(melee_attack)
            self.attack_initiated = True

        if not self.melee_pressed:
            self.attack_initiated = False

        self.melee_attacks.update()

        # Get current time
        current_time = time.time()

        # Check if enough time has passed since the last ranged attack
        if (current_time - self.last_ranged_attack_time >= self.ranged_attack_cooldown) or (
                self.last_ranged_attack_time == 0):
            # Allow ranged attack initiation if the count is less than the maximum
            if self.ranged_pressed and not self.rangeAttack_initiated and self.ranged_attack_count < self.ranged_attack_max:
                self.ranged_attack_sound.play()
                self.range_attacks.add(range_attack)
                self.rangeAttack_initiated = True
                # Increment the ranged attack count
                self.ranged_attack_count += 1
                # Update the time of the last ranged attack
                self.last_ranged_attack_time = current_time

        if not self.ranged_pressed:
            self.rangeAttack_initiated = False

        self.range_attacks.update()

        if self.rect.x > SCREEN_WIDTH - SCROLL_THRESH:
            self.rect.x = SCREEN_WIDTH - SCROLL_THRESH
            self.scroll = self.scroll_amount

        # Scroll by the amount moved horizontally
        self.level_scroll += self.scroll

        for enemy in self.enemies_group:
            if self.direction == "right":
                enemy.rect.x -= self.scroll
            else:
                enemy.rect.x += self.scroll + 2

        return -self.scroll

    def input(self):
        """Sets player class variables according to inputs from the user."""

        keys = pg.key.get_pressed()
        mouse_buttons = pg.mouse.get_pressed()

        # self.melee_pressed = keys[pg.K_q] or mouse_buttons[0]  # Q and left click for melee attack *ORIGINAL*

        # Modified
        self.melee_pressed = keys[pg.K_j] or mouse_buttons[0]   # J and left click for melee attack
        self.ranged_pressed = keys[pg.K_k] or mouse_buttons[2]  # K and right click for ranged attack

        self.up_press = keys[pg.K_SPACE] or keys[pg.K_UP] or keys[pg.K_w]
        self.left_press = keys[pg.K_LEFT] or keys[pg.K_a]
        self.right_press = keys[pg.K_RIGHT] or keys[pg.K_d]
        self.movement_pressed = self.left_press or self.right_press

        self.is_jumping = self.up_press

        if self.movement_pressed:
            self.is_moving = True
            if self.left_press:
                self.direction = "left"
            elif self.right_press:
                self.direction = "right"
        else:
            self.is_moving = False

    def move(self):
        """Determines horizontal and scroll movement."""

        if self.movement_pressed:
            self.counter += 1

            if self.left_press and not self.right_press:
                if self.level_scroll > 0:
                    self.dx -= self.speed
                    self.scroll = -self.scroll_amount

            elif self.right_press and not self.left_press:
                if self.scroll > 5000:
                    self.dx = 0
                else:
                    self.dx += self.speed
                    self.scroll = self.scroll_amount
        else:
            self.dx = 0
            self.scroll = 0

    def jump(self):
        """Performs a jump."""

        self.vel_y = self.jump_strength
        self.dy += self.vel_y
        self.on_ground = False

    def check_collision(self):
        """
        Checks for collision with various tile sprites and adjusts the player's movement or rect position accordingly.
        """

        # Check if hitbox (after being updated) collides with platform
        hitbox_after = pg.Rect(
            self.rect.x, self.rect.y + math.ceil(self.vel_y),
            self.rect.width, self.rect.height
        )
        for platform in self.platform_group:
            if platform.rect.colliderect(hitbox_after):
                # if currently falling (and only when above the platform)
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.top:
                    self.dy = 0
                    self.vel_y = 0  # stop falling
                    self.on_ground = True

        x_check = pg.Rect(self.rect.x + self.dx, self.rect.y, self.rect.width, self.rect.height)
        y_check = pg.Rect(self.rect.x, self.rect.y + math.ceil(self.dy),
                          self.rect.width, self.rect.height)

        for tile in self.obstacle_list:
            # Horizontal collision
            if tile.rect.colliderect(x_check):
                self.scroll = 0
                self.dx = 0
                if self.right_press:
                    self.rect.right = tile.rect.left - 1
                elif self.left_press:
                    self.rect.left = tile.rect.right + 1
                continue  # Don't bother checking vertical collision if horizontal collision detected

            # Vertical collision
            if tile.rect.colliderect(y_check):
                if self.vel_y < 0:  # If jumping up
                    self.dy = 0
                    self.vel_y = 0
                    self.rect.top = tile.rect.bottom
                elif self.vel_y > 0:  # If falling
                    self.dy = tile.rect.top - self.rect.bottom
                    self.vel_y = 0
                    self.on_ground = True
                    self.is_moving = False
                    # The last position when the player was on the ground
                    if tile.rect != self.last_ground_pos:
                        self.last_ground_pos = tile.rect

    def handle_animation(self):
        """Sets the direction and current frame of animation for the player."""

        if self.counter > self.walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.animation):
                self.index = 0

        animation = self.animation[self.index]

        if not self.is_moving:
            self.image = self.idle
        else:
            self.image = animation

        flip = self.direction == "left"
        self.image = pg.transform.flip(self.image, flip, False)

    def draw(self):
        """Draws the player and any player attacks onto the screen."""

        self.screen.blit(self.image, (self.sprite_x, self.sprite_y))
        self.melee_attacks.draw(self.screen)

        # Draw melee attacks
        self.melee_attacks.draw(self.screen)
        self.range_attacks.draw(self.screen)

        # Draw the remaining ranged attacks count
        self.draw_range_attack_count()

        SC_count = f"Second Chance Count: {self.SC_count}"
        SC_count_text = self.font.render(SC_count, True, (255, 255, 255))  # White color text
        self.screen.blit(SC_count_text, (19, 100))

    def decrease_health(self, amount):
        """Decreases the player's health.

        Args:
            amount (int): Amount to decrease health.
        """
        # Check if the player is currently invincible
        if not self.invincible:
            self.health -= amount

            # Prevent the player's HP from being reduced below 0
            if self.health < 0:
                self.health = 0

            # Set the player to be invincible and record the time of the hit
            self.invincible = True
            self.last_hit_time = time.time()
            # Play the hit sound effect
            self.hit_sound.play()

    def check_invincibility(self):
        """
        Checks for player invincibility and disables it if the invincibility duration has elapsed.
        """
        if self.invincible and time.time() - self.last_hit_time > self.invincible_duration:
            self.invincible = False

    def increase_health(self, amount):
        """Increases the player's health.

        Args:
            amount (int): Amount to increase health.
        """
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def draw_range_attack_count(self):
        """Calculates and draws the range attack count."""

        # Render the text for displaying the remaining ranged attacks count
        text_count = f"{100 - self.ranged_attack_count}" # Change the count show on the screen to 100, else it will show negative
        text_surface_count = self.font.render(text_count, True, (255, 255, 255))  # White color text

        # Render the static label "Arrows Left:"
        text_label = "Arrows Left: "
        text_surface_label = self.font.render(text_label, True, (255, 255, 255))  # White color text

        # Get the width of the label
        label_width = text_surface_label.get_width()

        # Calculate the position of the label (left-aligned)
        label_x = 19  # Adjust this value as needed
        label_y = 80  # Adjust this value as needed

        # Calculate the position of the count (right-aligned)
        count_x = label_x + label_width  # Position the count to the right of the label
        count_y = label_y  # Align the count vertically with the label

        # Blit the label onto the screen
        self.screen.blit(text_surface_label, (label_x, label_y))

        # Blit the count onto the screen
        self.screen.blit(text_surface_count, (count_x, count_y))

    def _debug(self):
        text = \
            f"""
     	Grounded: {self.on_ground}
		| (dx, dy) : {(self.dx, self.dy)}
        | (rect.x, rect.y): {(self.rect.x, self.rect.y)} 
        | Vel: {self.vel_y}
        | last_ground_tile: {self.last_ground_pos}
        """
        text_surface = self.font.render(text, True, "red")
        pg.draw.rect(self.screen, (255, 255, 255), self.rect, 2)
        self.screen.blit(text_surface, (0, 100))
