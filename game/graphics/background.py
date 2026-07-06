# game/graphics/background.py
import pygame
import random
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BG_THEMES, BG_TRANSITION_DURATION
from game.settings import BOSS_BG_OVERLAY_COLOR, BOSS_BG_OVERLAY_ALPHA, BOSS_PARTICLE_TYPE, BOSS_PARTICLE_RATE


def generate_layer_surface(layer_config):
    """Generate a pixel-art scrolling surface for a background layer.

    layer_config can contain:
      - name (str): layer type ("sky", "clouds", "mountains", "city", "ground", "foreground")
      - color (tuple): base color
      - alpha (int, optional): transparency 0-255
      - seed (int, optional): RNG seed for reproducibility
      - stars (int, optional): number of stars for sky layer
    """
    name = layer_config["name"]
    color = layer_config["color"]
    alpha = layer_config.get("alpha", 255)
    seed = layer_config.get("seed", None)

    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # Set RNG seed for deterministic generation
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    if name == "sky":
        stars_count = layer_config.get("stars", 40)
        sky_color = color
        # Fill sky base
        surf.fill(sky_color)
        # Draw stars
        for _ in range(stars_count):
            x = rng.randint(0, SCREEN_WIDTH)
            y = rng.randint(0, SCREEN_HEIGHT)
            r = rng.randint(1, 2)
            bright = rng.randint(30, 80) if seed is None else rng.randint(30, 80)
            star_color = (bright, bright, bright + 20)
            pygame.draw.circle(surf, star_color, (x, y), r)

    elif name == "clouds":
        # Semi-transparent cloud wisps
        hue_r, hue_g, hue_b = color
        for _ in range(12):
            cx = rng.randint(0, SCREEN_WIDTH)
            cy = rng.randint(0, SCREEN_HEIGHT)
            cw = rng.randint(60, 150)
            ch = rng.randint(20, 50)
            cloud_color = (
                min(255, hue_r + rng.randint(-10, 30)),
                min(255, hue_g + rng.randint(-10, 30)),
                min(255, hue_b + rng.randint(-10, 30)),
            )
            cloud_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
            # Draw overlapping circles for cloud shape
            for _ in range(5):
                ox = rng.randint(0, cw)
                oy = rng.randint(0, ch)
                or_ = rng.randint(10, 25)
                ca = rng.randint(60, 140)
                cloud_color_alpha = (*cloud_color, ca)
                pygame.draw.circle(cloud_surf, cloud_color_alpha, (ox, oy), or_)
            surf.blit(cloud_surf, (cx, cy), special_flags=pygame.BLEND_ALPHA_SDL2)

    elif name == "mountains":
        # Procedural mountain silhouette
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 10, 10):
            h = SCREEN_HEIGHT - rng.randint(40, 120)
            points.append((x, h))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)

    elif name == "city":
        # City skyline — random rectangles
        x = 0
        while x < SCREEN_WIDTH:
            w = rng.randint(20, 60)
            h = rng.randint(60, 180)
            y = SCREEN_HEIGHT - h
            pygame.draw.rect(surf, color, (x, y, w, h))
            # Window lights
            for wx in range(x + 4, x + w - 4, 10):
                for wy in range(y + 4, y + h - 4, 12):
                    if rng.random() < 0.3:
                        pygame.draw.rect(surf, (60, 60, 30), (wx, wy, 4, 6))
            x += w + rng.randint(5, 15)

    elif name == "ground":
        # Ground silhouette with slight texture
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 10, 10):
            h = SCREEN_HEIGHT - rng.randint(10, 30)
            points.append((x, h))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)

    elif name == "foreground":
        # Very close silhouette (trees, poles) — fast moving
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 10, 10):
            h = SCREEN_HEIGHT - rng.randint(5, 18)
            points.append((x, h))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)

    # Apply alpha if specified and not already fully transparent
    if alpha < 255:
        surf.set_alpha(alpha)

    return surf


class TransitionEffect:
    """Manages a crossfade between old and new background layers.

    During transition:
      - Frame 0 to DURATION//2: old layers fade from 255->0
      - Frame DURATION//2 to DURATION: new layers fade from 0->255
    """

    def __init__(self, old_layers, new_layers, duration=None):
        self.duration = duration or BG_TRANSITION_DURATION
        self.frame = 0
        self.old_layers = old_layers
        self.new_layers = new_layers
        self.midpoint = self.duration // 2

    def update(self):
        self.frame += 1

    def is_done(self):
        return self.frame >= self.duration

    def get_layer_alpha(self, layer_index):
        """Return alpha value for the given layer index.

        During first half: layers fade out (255->0).
        During second half: layers fade in (0->255).

        Each layer gets a 3-frame stagger for organic parallax feel.
        """
        stagger = layer_index * 3
        adjusted = max(0, self.frame - stagger)

        if self.frame < self.midpoint:
            progress = adjusted / self.midpoint
            alpha = max(0, int(255 * (1.0 - progress)))
            return alpha
        else:
            progress = (adjusted - self.midpoint) / (self.duration - self.midpoint)
            alpha = min(255, int(255 * progress))
            return alpha


class BackgroundParticles:
    """Manages spawning and updating of background particle effects.

    Each active theme provides a list of particle configs:
      [{"type": "shooting_star", "rate": 0.01}, ...]
    """

    def __init__(self):
        self.particles = []
        self.configs = []
        self.frame = 0

    def reset(self, configs):
        """Set new particle configs for the current theme."""
        self.configs = configs if configs else []
        self.particles.clear()
        self.frame = 0

    def update(self):
        self.frame += 1
        for cfg in self.configs:
            if random.random() < cfg.get("rate", 0):
                particle = self._spawn(cfg["type"])
                if particle:
                    self.particles.append(particle)

        # Update + cull
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

        # Cap
        if len(self.particles) > 200:
            self.particles = self.particles[-200:]

    def _spawn(self, ptype):
        """Spawn a single particle based on type."""
        if ptype == "shooting_star":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=random.randint(0, SCREEN_HEIGHT // 3),
                vx=random.uniform(2, 5),
                vy=random.uniform(1, 3),
                color=(200, 200, 255),
                life=random.randint(20, 50),
                size=random.randint(1, 2),
            )
        elif ptype == "bird":
            return Particle(
                x=-10,
                y=random.randint(SCREEN_HEIGHT // 3, SCREEN_HEIGHT // 2),
                vx=random.uniform(1, 3),
                vy=random.uniform(-0.5, 0.5),
                color=(40, 40, 50),
                life=random.randint(120, 200),
                size=2,
            )
        elif ptype == "lightning":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=random.randint(0, SCREEN_HEIGHT // 3),
                vx=0,
                vy=random.uniform(8, 15),
                color=(200, 200, 255),
                life=random.randint(3, 8),
                size=3,
            )
        elif ptype == "rain":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=0,
                vx=-0.5,
                vy=random.uniform(6, 10),
                color=(100, 120, 180),
                life=random.randint(60, 120),
                size=1,
            )
        elif ptype == "spore":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=SCREEN_HEIGHT,
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(-2, -1),
                color=(120, 200, 120),
                life=random.randint(80, 150),
                size=random.randint(2, 4),
            )
        elif ptype == "ember":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=SCREEN_HEIGHT,
                vx=random.uniform(-1, 1),
                vy=random.uniform(-3, -1),
                color=(random.randint(200, 255), random.randint(80, 150), 20),
                life=random.randint(30, 80),
                size=random.randint(1, 3),
            )
        elif ptype == "boss_storm":
            return Particle(
                x=random.randint(0, SCREEN_WIDTH),
                y=random.randint(-50, 0),
                vx=random.uniform(-1, 1),
                vy=random.uniform(1, 4),
                color=(random.randint(150, 255), 50, 50),
                life=random.randint(40, 80),
                size=random.randint(1, 3),
            )
        return None

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


class Particle:
    """A single background particle with position, velocity, color, and life."""

    def __init__(self, x, y, vx, vy, color, life, size=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        alpha = int(255 * (self.life / self.max_life))
        if alpha <= 0:
            return
        size = max(1, int(self.size * (self.life / self.max_life)))
        if size < 1:
            return
        pygame.draw.circle(screen, self.color[:3], (int(self.x), int(self.y)), size)


class LevelBackgroundManager:
    """Manages parallax scrolling backgrounds with level-aware theming.

    Switches visual themes as the game level increases, handles smooth
    transitions, and applies boss-fight overlays.
    """

    def __init__(self):
        self.current_level = 0
        self.current_theme = BG_THEMES[0]
        self.boss_active = False
        self.transition = None
        self.particle_system = BackgroundParticles()
        self._build_layers()
        self.particle_system.reset(self.current_theme.get("particles", []))

    def _build_layers(self):
        """(Re)build scrolling layers from self.current_theme."""
        self.layers = []
        for cfg in self.current_theme["layers"]:
            surf = generate_layer_surface(cfg)
            self.layers.append({
                "surface": surf,
                "speed": cfg["speed"],
                "y_offset": 0.0,
            })

    def switch_to_level(self, level):
        """Initiate a transition to a new level's theme.

        Returns True if level actually changed (vs same level).
        """
        if level == self.current_level:
            return False
        if level not in BG_THEMES:
            level = max(BG_THEMES.keys())

        old_layers = self.layers
        self.current_level = level
        self.current_theme = BG_THEMES[level]

        # Build new layers at zero offset
        new_layers = []
        for cfg in self.current_theme["layers"]:
            surf = generate_layer_surface(cfg)
            new_layers.append({
                "surface": surf,
                "speed": cfg["speed"],
                "y_offset": 0.0,
            })

        # Start transition effect
        self.transition = TransitionEffect(
            old_layers=old_layers,
            new_layers=new_layers,
            duration=BG_TRANSITION_DURATION,
        )

        # Swap layers immediately but transition manages alpha
        self.layers = new_layers

        # Reset particle system for new theme
        self.particle_system.reset(self.current_theme.get("particles", []))

        return True

    def set_boss_mode(self, active):
        """Toggle boss-fight visual overlay."""
        self.boss_active = active
        if active:
            self.particle_system.reset([{"type": "boss_storm", "rate": BOSS_PARTICLE_RATE}])
        else:
            self.particle_system.reset(self.current_theme.get("particles", []))

    def update(self):
        """Scroll each layer downward; update transition and particles."""
        speed_mult = 1.0 + self.current_level * 0.15  # 15% faster per level

        for layer in self.layers:
            layer["y_offset"] += layer["speed"] * speed_mult
            if layer["y_offset"] >= SCREEN_HEIGHT:
                layer["y_offset"] -= SCREEN_HEIGHT

        if self.transition and not self.transition.is_done():
            self.transition.update()

        self.particle_system.update()

    def draw(self, screen):
        """Draw all layers in order (back to front); apply transition alpha."""
        for i, layer in enumerate(self.layers):
            y_int = int(layer["y_offset"])
            surf = layer["surface"]

            # Apply transition alpha if active
            draw_surf = surf
            if self.transition and not self.transition.is_done():
                alpha = self.transition.get_layer_alpha(i)
                draw_surf = surf.copy()
                draw_surf.set_alpha(alpha)

            screen.blit(draw_surf, (0, y_int))
            # Tile the wrapping slice
            if y_int > 0:
                screen.blit(draw_surf, (0, y_int - SCREEN_HEIGHT))
            else:
                screen.blit(draw_surf, (0, y_int + SCREEN_HEIGHT))

        # Draw particles on top of layers
        self.particle_system.draw(screen)

        # Draw boss overlay if active
        if self.boss_active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(BOSS_BG_OVERLAY_COLOR)
            overlay.set_alpha(BOSS_BG_OVERLAY_ALPHA)
            screen.blit(overlay, (0, 0))


# Backward-compatible alias
ScrollingBackground = LevelBackgroundManager