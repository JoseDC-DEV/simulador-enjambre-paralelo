"""Cola de asteroides con límite simultáneo y condición de victoria (funciones puras).

Todos los asteroides del nivel se generan al inicio (la aleatoriedad vive solo
en simulation.create_initial_state) y esperan en state.pending, que funciona
como una cola FIFO. En pantalla nunca hay más de state.max_active a la vez:
cada vez que un asteroide sale de pantalla (o es destruido) queda un hueco y
entra el siguiente de la cola. La densidad en pantalla se mantiene así
constante y la dificultad del nivel depende solo del TOTAL de asteroides.

Un asteroide de cada AIMED_EVERY nace apuntando a la nave; el resto deriva.
Para no matar a la nave de forma injusta, un asteroide no entra mientras su
punto de aparición esté a menos de SAFE_SPAWN_DISTANCE de ella (espera en la
cola; entrará en cuanto la nave se aleje).

Victoria: la cola está vacía y ya no queda ningún asteroide en pantalla.
"""

import math
from dataclasses import replace
from itertools import takewhile

from core.entities import Asteroid, Player
from core.state import GameState

AIMED_EVERY = 10  # 1 de cada 10 asteroides nace apuntando a la nave
SAFE_SPAWN_DISTANCE = 150.0  # px: no aparecen asteroides encima de la nave


def aim_at(asteroid: Asteroid, player: Player) -> Asteroid:
    """Redirige el asteroide hacia la nave, conservando su rapidez."""
    dx, dy = player.x - asteroid.x, player.y - asteroid.y
    distance = math.hypot(dx, dy)
    if distance == 0:
        return asteroid
    speed = math.hypot(asteroid.vx, asteroid.vy)
    return replace(asteroid, vx=dx / distance * speed, vy=dy / distance * speed)


def aim_if_marked(asteroid: Asteroid, player: Player) -> Asteroid:
    return aim_at(asteroid, player) if asteroid.id % AIMED_EVERY == 0 else asteroid


def is_safe_entry(asteroid: Asteroid, player: Player) -> bool:
    """¿Su punto de aparición está lo bastante lejos de la nave?"""
    return math.hypot(asteroid.x - player.x, asteroid.y - player.y) >= SAFE_SPAWN_DISTANCE


def refill_from_queue(state: GameState) -> GameState:
    """Rellena los huecos libres de pantalla con los siguientes de la cola.

    Entran, en orden, tantos asteroides como huecos haya (max_active menos los
    que ya están en pantalla). Si el siguiente de la cola aparecería encima de
    la nave, la entrada se aplaza (y con ella las de detrás, para no alterar el
    orden de la cola).
    """
    free_slots = max(0, state.max_active - len(state.asteroids))
    entering = tuple(
        takewhile(lambda a: is_safe_entry(a, state.player), state.pending[:free_slots])
    )
    if not entering:
        return state
    released = tuple(aim_if_marked(a, state.player) for a in entering)
    return replace(
        state,
        asteroids=state.asteroids + released,
        pending=state.pending[len(entering):],
    )


def release_all(state: GameState) -> GameState:
    """Activa todos los asteroides de golpe (peor caso; útil para benchmark y tests)."""
    return replace(state, asteroids=state.asteroids + state.pending, pending=())


def is_victory(pending: tuple[Asteroid, ...], asteroids: tuple[Asteroid, ...]) -> bool:
    """Se gana al agotar la cola y dejar la pantalla vacía."""
    return not pending and not asteroids
