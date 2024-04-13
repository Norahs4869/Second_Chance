import pygame as pg
import os
import random

from src.states.minigames.minigame import Minigame
from src.utils.timer import Timer

from pygame.locals import * # To get all 


class ReactionTime(Minigame):
    """A minigame to test your reaction time."""
    
    def __init__(self):
        instructions = \
            "The goal of this minigame is to wait for a keyboard button " \
            "that will appear on the screen, and then press that key on " \
            "your keyboard as quick as possible. If you are too slow, " \
            "you lose."

        img = "minigame1.jpg"

        super().__init__(
            instructions,
            img=os.path.join("minigames", img)
        )
        
        self.reaction_timer = Timer()
        self.reaction_time = 0
        self.random_key = self.generate_random_key()
        self.random_key_name = pg.key.name(self.random_key)
        self.random_start_time = random.uniform(2, 6)
        self.key_display_text = self.get_text_surface(f"Press {self.random_key_name}", "green", 72)

    def handle_events(self, events):
        super().handle_events(events) # To enable pause menu access
        for event in events:
            if event.type == pg.KEYDOWN:
                
                # Win condition
                if event.key == self.random_key and self.reaction_timer.is_running:
                    print(f"YOU WIN! Your time: {self.reaction_time:.3f}")
                    self.reaction_timer.pause()
                    self.won = True

    def update(self, events):
        super().update(events)

        # Start reaction timer once random amount of time has passed
        if not self.reaction_timer.is_running and \
                self.timer.get_time(ms=True) >= self.random_start_time:
            self.reaction_timer.start()
        
        # Update reaction timer text
        if self.reaction_timer.is_running:
            self.reaction_time = self.reaction_timer.get_time(ms=True)
            self.reaction_timer_text = self.get_text_surface(
                f"Reaction timer: {self.reaction_time:.3f}", "white", 36)

    def draw(self):
        super().draw() # Draw minigame background
        
        # Draw text
        if self.reaction_timer.is_running:
            self.screen.blit(self.reaction_timer_text, (20, 20))
            self.screen.blit(self.key_display_text,
                ((self.screen.get_width() / 2) - 50, self.screen.get_height()/2)
            )
        
    def generate_random_key(self):
        """Generates a random lowercase key from a-z."""
        return random.choice([getattr(pg.locals, f'K_{chr(key)}') for key in range(ord('a'), ord('z') + 1)])
