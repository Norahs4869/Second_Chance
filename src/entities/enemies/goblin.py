from .enemy import Enemy

#from src.entities.enemies.goblin import Goblin

# Assuming you have a platform_group and tile_list defined
#goblin = Goblin(200, 150, platform_group, tile_list)
#enemy_group.add(goblin)  # Add the Goblin to your enemy group

class Goblin(Enemy):
    def __init__(self, x, y, platform_group, tile_list):
        super().__init__(
            x, y,
            platform_group,
            tile_list,
            "goblin", 
            speed=2,  
            vertical_speed=0,
            gravity=0.5,
            health=80,  
            max_health=80,
            strength=15  
        )
        self.health_bar_offset_x = (self.rect.width - self.health_bar_length) / 2
        self.health_bar_offset_y = self.rect.height / 2 - 30

    #     # Additional attributes for Goblin behavior
    #     self.aggressive = True  # Can be used to trigger different behaviors
    #     self.attack_range = 100  # Range within which the Goblin will attack

    # def move(self):
    #     #Adjusts the goblin's position, including aggressive behavior.
    #     super().move()  # Call the parent move method to handle basic movement

    #     # Implement aggressive behavior
    #     if self.aggressive:
    #         # Change direction towards the player if within attack range
    #         if self.rect.x < self.player.rect.x - self.attack_range:
    #             self.direction = 1  # Move right
    #         elif self.rect.x > self.player.rect.x + self.attack_range:
    #             self.direction = -1  # Move left

    # def update(self, player):
    #     """Check for conditions affecting the Goblin's position and update."""
    #     super().update(player)  # Call the parent update method

    #     # Check for additional behaviors (e.g., attacking the player)
    #     if self.rect.colliderect(player.rect) and self.aggressive:
    #         player.decrease_health(self.strength)

    #     # You can add more unique behaviors for the Goblin here