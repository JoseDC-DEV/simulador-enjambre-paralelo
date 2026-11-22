"""Entidades inmutables del juego Fallen Asteroids.

Convenciones de unidades:
- Posiciones en píxeles, velocidades en píxeles por segundo.
- Ángulos en radianes.
- Tiempos (ttl) en segundos.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Asteroid:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    health: int


@dataclass(frozen=True)
class Player:
    x: float
    y: float
    vx: float
    vy: float
    angle: float
    lives: int


@dataclass(frozen=True)
class Projectile:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    ttl: float  # tiempo de vida restante, en segundos
