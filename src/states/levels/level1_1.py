from src.objects.portal import Portal  # Import portal class
from .level import Level


class Level1_1(Level):
    def __init__(self):
        imgArr = [f"plx-{i}.png" for i in range(1, 6)]
        super().__init__(
            level=1,
            music_file="Chopin_Nocturne_Op.9_No.2_-_Aurbanni.mp3",
            imgArr=imgArr
        )

    def add_portal(self):
        # Add portal at specific coordinates
        self.portal = Portal(3500, 400, "assets/backgrounds/portal.png", 150, 150)
        self.portals.add(self.portal)
        self.objects.add(self.portals)
