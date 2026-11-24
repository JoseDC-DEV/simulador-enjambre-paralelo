"""Colisiones puras de Fallen Asteroids.

Reglas (deliberadamente simples):
- Cualquier proyectil que toque un asteroide lo destruye (un solo impacto).
- El proyectil atraviesa: sigue vivo hasta que caduca por ttl.
- Cualquier asteroide que toque la nave termina la partida.

process_asteroids es la función que ejecuta cada worker sobre su bloque:
mueve los asteroides, descarta los que salieron de pantalla y resuelve ambas
colisiones. Recibe todo por argumentos
y devuelve valores nuevos, por lo que es determinista y serializable.
"""

from core.entities import Asteroid, Player, Projectile
from core.transformations import is_on_screen, update_asteroids

PROJECTILE_RADIUS = 2.0
PLAYER_RADIUS = 12.0


def circles_overlap(
    x1: float, y1: float, r1: float, x2: float, y2: float, r2: float
) -> bool:
    """Dos círculos se tocan si la distancia entre centros <= suma de radios."""
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= (r1 + r2) ** 2


def is_hit_by_projectile(
    asteroid: Asteroid, projectiles: tuple[Projectile, ...]
) -> bool:
    return any(
        circles_overlap(
            asteroid.x, asteroid.y, asteroid.radius, p.x, p.y, PROJECTILE_RADIUS
        )
        for p in projectiles
    )


def touches_player(asteroid: Asteroid, player: Player) -> bool:
    return circles_overlap(
        asteroid.x, asteroid.y, asteroid.radius, player.x, player.y, PLAYER_RADIUS
    )


def process_asteroids(
    asteroids: tuple[Asteroid, ...],
    projectiles: tuple[Projectile, ...],
    player: Player,
    dt: float,
    width: float,
    height: float,
) -> tuple[tuple[Asteroid, ...], bool, int]:
    """Mueve un bloque de asteroides, descarta los que salen y resuelve colisiones.

    Devuelve (asteroides que siguen en pantalla, ¿alguno toca la nave?,
    cuántos destruyeron los proyectiles).
    """
    moved = update_asteroids(asteroids, dt)
    on_screen = tuple(a for a in moved if is_on_screen(a, width, height))
    survivors = tuple(a for a in on_screen if not is_hit_by_projectile(a, projectiles))
    player_hit = any(touches_player(a, player) for a in survivors)
    return survivors, player_hit, len(on_screen) - len(survivors)
