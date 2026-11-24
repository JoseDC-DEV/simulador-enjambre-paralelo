"""Inicialización y actualización secuencial del juego Fallen Asteroids.

- create_initial_state: única fuente de aleatoriedad (reproducible por semilla).
- update: versión secuencial de referencia de un frame.
- run_frames: encadena varios frames (útil para pruebas y benchmark).

Eventos: un frozenset de cadenas con las teclas activas en el frame.
Ángulos: la dirección de la nave es (cos(angle), sin(angle)); con el eje Y
hacia abajo (Pygame), angle = -pi/2 apunta hacia arriba.
"""

import math
import random
from dataclasses import replace
from functools import reduce

from core.collisions import process_asteroids
from core.entities import Asteroid, Player, Projectile
from core.state import DEFAULT_MAX_ACTIVE, GameState
from core.transformations import next_state
from core.waves import refill_from_queue

# --- Eventos soportados ---
LEFT = "left"
RIGHT = "right"
THRUST = "thrust"
SHOOT = "shoot"

# --- Parámetros de juego (constantes inmutables) ---
ROTATION_SPEED = 3.0  # rad/s
THRUST_ACCEL = 200.0  # px/s^2
PROJECTILE_SPEED = 600.0  # px/s
PROJECTILE_TTL = 1.5  # s
SHOOT_COOLDOWN = 0.25  # s entre disparos
MUZZLE_OFFSET = 14.0  # px: el proyectil nace en la punta de la nave
MIN_ASTEROID_SPEED = 30.0  # px/s, componente que entra a la pantalla
MAX_ASTEROID_SPEED = 100.0  # px/s
MIN_ASTEROID_RADIUS = 5.0
MAX_ASTEROID_RADIUS = 20.0
INITIAL_LIVES = 1  # un impacto termina la partida


# --- Inicialización (aquí vive toda la aleatoriedad) ---

def random_spawn(rng: random.Random, width: float, height: float) -> tuple:
    """Punto de un borde de la pantalla y velocidad que entra hacia el interior.

    Devuelve (x, y, vx, vy).
    """
    along = rng.uniform(0.0, 1.0)  # posición a lo largo del borde
    inward = rng.uniform(MIN_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    lateral = rng.uniform(-MAX_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    sides = (
        (0.0, along * height, inward, lateral),  # izquierda
        (width - 1.0, along * height, -inward, lateral),  # derecha
        (along * width, 0.0, lateral, inward),  # arriba
        (along * width, height - 1.0, lateral, -inward),  # abajo
    )
    return sides[rng.randrange(4)]


def create_asteroid(
    asteroid_id: int, rng: random.Random, width: float, height: float
) -> Asteroid:
    x, y, vx, vy = random_spawn(rng, width, height)
    return Asteroid(
        id=asteroid_id,
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        radius=rng.uniform(MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS),
        health=1,  # todos mueren de un impacto
    )


def create_initial_state(
    num_asteroids: int,
    width: float,
    height: float,
    seed: int = 0,
    max_active: int = DEFAULT_MAX_ACTIVE,
) -> GameState:
    """Crea una partida inicial. La misma semilla produce el mismo estado.

    Ningún asteroide está en pantalla todavía: los num_asteroids esperan en
    la cola state.pending y entran según haya huecos, con un máximo de
    max_active simultáneos (ver core/waves.py).
    """
    rng = random.Random(seed)  # generador local: no toca el estado global
    return GameState(
        player=Player(
            x=width / 2,
            y=height / 2,
            vx=0.0,
            vy=0.0,
            angle=-math.pi / 2,
            lives=INITIAL_LIVES,
        ),
        asteroids=(),
        projectiles=(),
        score=0,
        running=True,
        frame=0,
        pending=tuple(
            create_asteroid(i, rng, width, height) for i in range(num_asteroids)
        ),
        max_active=max_active,
    )


# --- Actualización de un frame ---

def create_projectile(player: Player, frame: int) -> Projectile:
    dx, dy = math.cos(player.angle), math.sin(player.angle)
    return Projectile(
        id=frame,  # a lo sumo un disparo por frame: el frame es un id único
        x=player.x + dx * MUZZLE_OFFSET,
        y=player.y + dy * MUZZLE_OFFSET,
        vx=dx * PROJECTILE_SPEED,
        vy=dy * PROJECTILE_SPEED,
        ttl=PROJECTILE_TTL,
    )


def can_shoot(projectiles: tuple[Projectile, ...]) -> bool:
    """Hay cadencia de disparo si ningún proyectil es más joven que el cooldown.

    Se deduce de los propios proyectiles: no hace falta un campo extra en el estado.
    """
    return not any(p.ttl > PROJECTILE_TTL - SHOOT_COOLDOWN for p in projectiles)


def apply_events(state: GameState, events: frozenset, dt: float) -> GameState:
    """Aplica los controles del jugador (rotar, acelerar, disparar)."""
    player = state.player
    turn = int(RIGHT in events) - int(LEFT in events)  # -1, 0 o +1
    angle = player.angle + turn * ROTATION_SPEED * dt
    accel = THRUST_ACCEL * dt if THRUST in events else 0.0
    new_player = replace(
        player,
        angle=angle,
        vx=player.vx + math.cos(angle) * accel,
        vy=player.vy + math.sin(angle) * accel,
    )
    fires = SHOOT in events and can_shoot(state.projectiles)
    projectiles = (
        (*state.projectiles, create_projectile(new_player, state.frame))
        if fires
        else state.projectiles
    )
    return replace(state, player=new_player, projectiles=projectiles)


def update(
    state: GameState, events: frozenset, dt: float, width: float, height: float
) -> GameState:
    """Un frame, versión secuencial: recibe un estado y devuelve uno nuevo."""
    controlled = refill_from_queue(apply_events(state, events, dt))
    asteroids, player_hit, destroyed = process_asteroids(
        controlled.asteroids,
        controlled.projectiles,
        controlled.player,
        dt,
        width,
        height,
    )
    return next_state(controlled, asteroids, player_hit, destroyed, dt, width, height)


def run_frames(
    state: GameState, num_frames: int, dt: float, width: float, height: float
) -> GameState:
    """Encadena num_frames frames sin eventos, sin bucles que mutan estado."""
    return reduce(
        lambda current, _: update(current, frozenset(), dt, width, height),
        range(num_frames),
        state,
    )
