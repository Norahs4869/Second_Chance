import json
import math

import pygame as pg
import pygame_menu
import redditwarp.SYNC

# Not using relative import to handle circular import issue when importing TitleScreen
# TODO Fix this later
import src.states.menu.title_screen as ts
from src.constants import *
from src.states.minigames.button_memory import ButtonMemory
from src.states.minigames.calculate import Calculate
from src.states.minigames.flying_green import FlyingGreen
from src.states.minigames.matching_game import Matching
from src.states.minigames.memory import Memory
from src.states.minigames.reaction_time import ReactionTime
from src.states.minigames.reflexes import Reflexes
from src.states.state import State, TimedState
from src.utils.leaderboard import LeaderboardManager
from src.utils.timer import Timer
from ..levels.level1_1 import Level1_1

# Global variable for volume
volume = 0.5  # Initial volume value, you can set it to any value you desire


def load_theme_config():
    """Loads the menu theme from config file."""

    try:
        with open('theme_config.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'theme': 'Light'}  # Default theme


def save_theme_config(theme):
    """Saves the current menu theme to config file.

    Args:
        theme: Theme to save.
    """
    with open('theme_config.json', 'w') as file:
        json.dump({'theme': theme}, file)


def get_news():
    client = redditwarp.SYNC.Client()
    m = next(client.p.subreddit.pull.top('Temple', amount=1, time='hour'))
    return m


class StartMenu(State):
    """State for the start menu."""

    def __init__(self):
        super().__init__("background.png")  # Change to start menu background

        self.leaderboard = LeaderboardManager(self.game)

        self.player_name = self.game.username
        self.font = pg.font.Font(None, 30)  # Assuming you want a size 20 font
        self.theme_config = load_theme_config()
        self.current_theme = self.theme_config['theme']  # Load theme from configuration

        self.main_menu()

    def handle_events(self, events):
        if self.menu.is_enabled():
            self.menu.update(events)

        for event in events:
            if event.type != pg.KEYDOWN:
                return
            if event.key == pg.K_ESCAPE:
                self.manager.set_state(ts.TitleScreen)

    def draw(self):
        self.player_name = self.game.username
        self.menu.draw(self.screen)
        username_label = f"Username: {self.player_name}"
        username_text = self.font.render(username_label, True, (255, 255, 255))

        username_rect = username_text.get_rect(topright=(SCREEN_WIDTH - 5, 5))

        self.screen.blit(username_text, username_rect)

    def main_menu(self):
        """Opens the main menu."""

        # Create menu
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)
            self.menu.add.label("Temple reddit post:: " + get_news().title, "news_banner",
                                wordwrap=True, font_size=14, font_color=(61, 170, 220),
                                margin=[0, 50])


        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
            self.menu.add.label("Temple reddit post:: " + get_news().title, "news_banner",
                                wordwrap=True, font_size=14, font_color=(200, 200, 200),
                                margin=[0, 50])

            # Add buttons to the menu
        self.menu.add.button('Start Game', self.manager.set_state, Level1_1)
        self.menu.add.button("Instructions", self.instructions_menu)
        self.menu.add.button("Minigames", self.minigames_menu)
        self.menu.add.button("Leaderboard", self.leaderboard_menu)
        self.menu.add.button("Options", self.options_menu)
        self.menu.add.button('Change Username', self.manager.set_state, UsernamePrompt)
        self.menu.add.button('Quit', pygame_menu.events.EXIT)

    def instructions_menu(self):
        """Opens the instructions menu."""

        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)

            # Add game instructions
        instructions_text = "To move, use left and right arrow keys, or a and d\nTo jump, use up arrow key, w, or spacebar\nTo melee attack, use left click or j\nTo range attack, use right click or k"
        self.menu.add.label(instructions_text, max_char=-1, font_size=20)

        # Add back button
        self.menu.add.button('Back', self.main_menu)

    def minigames_menu(self):
        """
        Opens the minigames menu and allows you to pick a specific minigame to 
        play.
        """

        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)

        self.menu.add.button('Memory', self.manager.set_state, Memory)
        self.menu.add.button('Reflexes', self.manager.set_state, Reflexes)
        self.menu.add.button('Matching', self.manager.set_state, Matching)
        self.menu.add.button('Reaction', self.manager.set_state, ReactionTime)
        self.menu.add.button('Tracking', self.manager.set_state, FlyingGreen)
        self.menu.add.button('Calculate', self.manager.set_state, Calculate)
        self.menu.add.button('ButtonMemory', self.manager.set_state, ButtonMemory)

        self.menu.add.button('Back', self.main_menu)

    def leaderboard_menu(self):
        """Opens the leaderboard menu."""

        # Fetch and display the leaderboard
        leaderboard_data = self.leaderboard.fetch_leaderboard()
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)

            # Add leaderboard entries to the menu
        if leaderboard_data:
            for i, (name, score) in enumerate(leaderboard_data.items(), start=1):
                entry_text = f"{i}. {name}: {score}"
                self.menu.add.label(entry_text, max_char=-1, font_size=20)
        else:
            self.menu.add.label("Leaderboard is empty", max_char=-1, font_size=20)

        # Add back button
        self.menu.add.button('Back', self.main_menu)

    def options_menu(self):
        """Opens the options menu."""

        # Create options menu
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)

            # Add volume control buttons
        self.volume_label = self.menu.add.label('Volume: {}'.format(int(volume * 100)))
        self.volume_label.update_font({'size': 30})  # Set font size for the label

        self.menu.add.button('Increase Volume', self.increase_volume)
        self.menu.add.button('Decrease Volume', self.decrease_volume)

        self.menu.add.button('Toggle dark mode on/off', self.toggle)

        # Add back button
        self.menu.add.button('Back', self.main_menu)

    def toggle(self):
        """Toggles the current menu theme."""

        if (self.current_theme == "Light"):

            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
            self.current_theme = "Dark"
            save_theme_config(self.current_theme)
            # Add volume control buttons
            self.volume_label = self.menu.add.label('Volume: {}'.format(int(volume * 100)))
            self.volume_label.update_font({'size': 30})  # Set font size for the label

            self.menu.add.button('Increase Volume', self.increase_volume)
            self.menu.add.button('Decrease Volume', self.decrease_volume)

            self.menu.add.button('Toggle dark mode on/off', self.toggle)

            # Add back button
            self.menu.add.button('Back', self.main_menu)

        else:

            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)
            self.current_theme = "Light"
            save_theme_config(self.current_theme)
            # Add volume control buttons
            self.volume_label = self.menu.add.label('Volume: {}'.format(int(volume * 100)))
            self.volume_label.update_font({'size': 30})  # Set font size for the label

            self.menu.add.button('Increase Volume', self.increase_volume)
            self.menu.add.button('Decrease Volume', self.decrease_volume)

            self.menu.add.button('Toggle dark mode on/off', self.toggle)

            # Add back button
            self.menu.add.button('Back', self.main_menu)

    def increase_volume(self):
        """Increases game volume."""

        global volume
        volume = min(volume + 0.1, 1.0)  # Increase volume by 0.1, but ensure it doesn't exceed 1.0
        pg.mixer.music.set_volume(volume)
        self.volume_label.set_title('Volume: {}'.format(int(volume * 100)))

    def decrease_volume(self):
        """Decreases game volume."""

        global volume
        volume = max(volume - 0.1, 0.0)  # Decrease volume by 0.1, but ensure it doesn't go below 0.0
        pg.mixer.music.set_volume(volume)
        self.volume_label.set_title('Volume: {}'.format(int(volume * 100)))


class PauseMenu(State):
    """State for the pause menu

    Args:
        timer (Timer, optional): Timer passed from level or minigame so that
            the pause menu can resume it. Defaults to None.
    """

    def __init__(self, timer: Timer = None):

        super().__init__()
        self.timer = timer
        self.theme_config = load_theme_config()
        self.current_theme = self.theme_config['theme']  # Load theme from configuration
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
        self.menu.add.button('Return to game', self.resume)
        self.menu.add.button('Options', self.options_menu)
        self.menu.add.button("Quit game", self.manager.set_state, ts.TitleScreen, clear=True, accept_kwargs=True)

        if self.timer:
            self.timer.pause()

    def handle_events(self, events):
        self.menu.update(events)

    def draw(self):
        self.menu.draw(self.screen)

    def resume(self):
        """Resumes the level/minigame timer."""

        if self.timer:
            self.timer.resume()

        self.manager.pop_state()

    def options_menu(self):
        """Opens the options menu."""

        # Create options menu
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)

            # Add volume control buttons
        self.volume_label = self.menu.add.label('Volume: {}'.format(int(volume * 100)))
        self.volume_label.update_font({'size': 30})  # Set font size for the label

        self.menu.add.button('Increase Volume', self.increase_volume)
        self.menu.add.button('Decrease Volume', self.decrease_volume)

        # Add back button
        self.menu.add.button('Back', self.back_to_pause_menu)

    def increase_volume(self):
        """Increases game volume."""

        global volume
        volume = min(volume + 0.1, 1.0)  # Increase volume by 0.1, but ensure it doesn't exceed 1.0
        pg.mixer.music.set_volume(volume)
        self.volume_label.set_title('Volume: {}'.format(int(volume * 100)))

    def decrease_volume(self):
        """Decreases game volume."""

        global volume
        volume = max(volume - 0.1, 0.0)  # Decrease volume by 0.1, but ensure it doesn't go below 0.0
        pg.mixer.music.set_volume(volume)
        self.volume_label.set_title('Volume: {}'.format(int(volume * 100)))

    def back_to_pause_menu(self):
        """Returns to the pause menu."""

        # Revert to the original pause menu
        if (self.current_theme == "Light"):
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_BLUE)

        else:
            self.menu = pygame_menu.Menu('Options', SCREEN_WIDTH, SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
        self.menu.add.button('Return to game', self.resume)
        self.menu.add.button('Options', self.options_menu)
        self.menu.add.button("Quit game", self.manager.set_state, ts.TitleScreen, clear=True, accept_kwargs=True)


class UsernamePrompt(State):
    """State for the username prompt screen."""

    def __init__(self):
        super().__init__()
        self.input_rect = pg.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 12, 200, 24)
        self.font = pg.font.Font(None, 24)
        self.active = True
        self.text_prompt = self.font.render("Enter your username: ", True, (255, 255, 255))
        self.text_prompt_rect = self.text_prompt.get_rect(midbottom=self.input_rect.topleft)
        self.username = self.game.username
        self.gradient_time = 0  # Variable to control gradient movement

    def handle_events(self, events):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.input_rect.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False
            if event.type == pg.KEYDOWN:
                if self.active:
                    if event.key == pg.K_RETURN:
                        if len(self.username) > 0:  # Make sure user has entered at least 1 character
                            self.game.username = self.username[:15]  # Limiting username to 15 characters
                            self.manager.set_state(StartMenu)
                        return
                    elif event.key == pg.K_BACKSPACE:
                        self.username = self.username[:-1] if len(self.username) > 0 else self.username
                    else:
                        if len(self.username) < 15:  # Limiting username to 15 characters
                            self.username += event.unicode

    def update(self, events):
        # Render the username directly inside the input rectangle
        self.text_surface = self.font.render(self.username, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=self.input_rect.center)
        self.gradient_time += 0.01  # Adjust speed of gradient movement

    def draw(self):
        # Create gradient background
        self.draw_gradient_background()

        # Draw input box and text
        pg.draw.rect(self.screen, (255, 255, 255), self.input_rect, 2)
        self.screen.blit(self.text_prompt, self.text_prompt_rect)
        self.screen.blit(self.text_surface, self.text_rect)

    def draw_gradient_background(self):
        """Draws a colorful, constantly changing gradient background."""

        # Draw gradient background
        for y in range(SCREEN_HEIGHT):
            # Calculate color based on y position and time for gradient movement
            red = (math.sin(0.005 * y + self.gradient_time) * 127 + 128) % 256
            green = (math.sin(0.005 * y + self.gradient_time) * 127 + 128) % 256
            blue = (math.sin(0.005 * y + self.gradient_time + 4) * 127 + 128) % 256
            color = (red, green, blue)
            # Fill each row with the calculated color
            pg.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))


class WinScreen(TimedState):
    """State for the win screen after a minigame."""

    def __init__(self, next_state, extra_text="", timer=None, img=None):
        super().__init__(time=3, next_state=next_state, clear=True, timer=timer, img=img)
        self.win_text = self.get_text_surface(f"You won! {extra_text}", "white", font_size=36)
        self.win_text_pos = \
            ((self.screen.get_width() / 2) - 350, (self.screen.get_height() / 2) - 100)

    def update(self, events):
        # Must be called to know when to change state
        super().update(events)

    def draw(self):
        super().draw()
        self.manager.get_prev_state().draw()
        self.screen.blit(self.win_text, self.win_text_pos)


class LoseScreen(TimedState):
    """State for the lose screen after a minigame."""

    def __init__(self, next_state, prev_state, extra_text="", img=None):
        super().__init__(time=3, next_state=next_state, img=img)
        self.prev_state = prev_state
        self.lose_text = self.get_text_surface(f"You lose! :( {extra_text}", "white", font_size=36)
        self.lose_text_pos = \
            ((self.screen.get_width() / 2) - 250, (self.screen.get_height() / 2) - 100)

    def update(self, events):
        # Must be called to know when to change state
        super().update(events)

    def draw(self):
        super().draw()
        self.prev_state.draw()
        self.screen.blit(self.lose_text, self.lose_text_pos)


class MinigameMenu_WinScreen(TimedState):
    """
    State for the win screen after a minigame.
    
    The only difference between this and the `WinScreen` state is that this
    state returns to the minigame menu.
    """

    def __init__(self, next_state, prev_state, extra_text="", img=None):
        super().__init__(time=3, next_state=next_state, img=img)
        self.prev_state = prev_state
        self.lose_text = self.get_text_surface(f"You won! {extra_text}", "white", font_size=36)
        self.lose_text_pos = \
            ((self.screen.get_width() / 2) - 250, (self.screen.get_height() / 2) - 100)

    def update(self, events):
        # Must be called to know when to change state
        super().update(events)

    def draw(self):
        super().draw()
        self.prev_state.draw()
        self.screen.blit(self.lose_text, self.lose_text_pos)
