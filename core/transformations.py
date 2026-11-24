"""Transformaciones puras del juego Fallen Asteroids.

Todas las funciones reciben valores y devuelven valores nuevos: ninguna
modifica sus argumentos ni lee estado externo. Las dimensiones del mundo
(width, height) y el paso de tiempo (dt) llegan siempre como parámetros.
"""

from dataclasses import replace

from core.entities import Asteroid, Player, Projectile
from core.state import GameState
from core.waves import is_victory


# --- Utilidad ---------------------------------------------------------------

def wrap(value: float, limit: float) -> float:
    """Pantalla envolvente: devuelve value dentro de [0, limit)."""
    return value % limit


# --- Asteroides -------------------------------------------------------------

def move_asteroid(asteroid: Asteroid, dt: float) -> Asteroid:
    return replace(
        asteroid,
        x=asteroid.x + asteroid.vx * dt,
        y=asteroid.y + asteroid.vy * dt,
    )


def is_on_screen(asteroid: Asteroid, width: float, height: float) -> bool:
    """Un asteroide sigue en pantalla mientras algo de él sea visible.

    Los asteroides NO dan la vuelta por los bordes (a diferencia de la nave):
    al salir por completo dejan de existir y liberan su hueco en la cola.
    """
    r = asteroid.radius
    return -r <= asteroid.x <= width + r and -r <= asteroid.y <= height + r


def update_asteroid(asteroid: Asteroid, dt: float) -> Asteroid:
    """Mueve un asteroide."""
    return move_asteroid(asteroid, dt)


def update_asteroids(
    asteroids: tuple[Asteroid, ...], dt: float
) -> tuple[Asteroid, ...]:
    """Actualiza un bloque de asteroides (o todos, en la versión secuencial)."""
    return tuple(update_asteroid(a, dt) for a in asteroids)


# --- Proyectiles ------------------------------------------------------------

def move_projectile(projectile: Projectile, dt: float) -> Projectile:
    return replace(
        projectile,
        x=projectile.x + projectile.vx * dt,
        y=projectile.y + projectile.vy * dt,
        ttl=projectile.ttl - dt,
    )


def is_alive(projectile: Projectile) -> bool:
    return projectile.ttl > 0


def remove_expired_projectiles(
    projectiles: tuple[Projectile, ...],
) -> tuple[Projectile, ...]:
    return tuple(filter(is_alive, projectiles))


def update_projectiles(
    projectiles: tuple[Projectile, ...], dt: float
) -> tuple[Projectile, ...]:
    moved = tuple(move_projectile(p, dt) for p in projectiles)
    return remove_expired_projectiles(moved)


# --- Nave -------------------------------------------------------------------

def move_player(player: Player, dt: float, width: float, height: float) -> Player:
    return replace(
        player,
        x=wrap(player.x + player.vx * dt, width),
        y=wrap(player.y + player.vy * dt, height),
    )


# --- Estado -----------------------------------------------------------------

POINTS_PER_ASTEROID = 10


def next_state(
    state: GameState,
    asteroids: tuple[Asteroid, ...],
    player_hit: bool,
    destroyed: int,
    dt: float,
    width: float,
    height: float,
) -> GameState:
    """Construye el GameState del siguiente frame sin modificar el anterior.

    Los asteroides llegan ya procesados (movimiento, salidas de pantalla y
    colisiones, en secuencial o en paralelo), junto con cuántos destruyeron
    los proyectiles (los que salen de pantalla no puntúan). Aquí se actualiza
    lo demás: nave, proyectiles, puntuación, fin de partida y frame.
    """
    frame = state.frame + 1
    player = move_player(state.player, dt, width, height)
    won = state.running and not player_hit and is_victory(state.pending, asteroids)
    return replace(
        state,
        player=replace(player, lives=0) if player_hit else player,
        asteroids=asteroids,
        projectiles=update_projectiles(state.projectiles, dt),
        score=state.score + destroyed * POINTS_PER_ASTEROID,
        running=state.running and not player_hit and not won,
        frame=frame,
        won=state.won or won,
    )
