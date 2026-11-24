"""Estado completo e inmutable del juego Fallen Asteroids.

GameState es la única estructura que describe la partida en un instante.
No tiene métodos: las funciones de transformación reciben un GameState
y devuelven otro nuevo.
"""

from dataclasses import dataclass

from core.entities import Asteroid, Player, Projectile

DEFAULT_MAX_ACTIVE = 20  # meteoritos simultáneos en pantalla (ver core/waves.py)


@dataclass(frozen=True)
class GameState:
    player: Player
    asteroids: tuple[Asteroid, ...]  # asteroides en pantalla
    projectiles: tuple[Projectile, ...]
    score: int
    running: bool  # True mientras la partida continúa
    frame: int
    pending: tuple[Asteroid, ...] = ()  # cola: asteroides que aún no han aparecido
    max_active: int = DEFAULT_MAX_ACTIVE  # tope de asteroides en pantalla a la vez
    won: bool = False  # True si se terminó la partida con victoria
