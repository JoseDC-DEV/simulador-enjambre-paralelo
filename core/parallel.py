"""Ejecución paralela del procesamiento de asteroides (multiprocessing).

Pipeline de un frame:
1. Segmentación: split_chunks divide la tupla de asteroides en bloques.
2. Mapeo paralelo: pool.starmap envía cada bloque a un worker, que ejecuta
   la función pura process_asteroids (movimiento + colisiones) sobre su bloque.
3. Sincronización y consolidación: starmap es bloqueante (no devuelve hasta
   que terminan todos los workers); consolidate une los bloques, en orden,
   en una nueva tupla, combina los avisos de impacto a la nave y suma los
   asteroides destruidos.

Este es el único módulo de core/ que importa multiprocessing.
"""

import multiprocessing
from itertools import chain
from multiprocessing.pool import Pool

from core.collisions import process_asteroids
from core.entities import Asteroid, Player, Projectile
from core.simulation import apply_events
from core.state import GameState
from core.transformations import next_state
from core.waves import refill_from_queue


def create_pool(workers: int) -> Pool:
    """Crea el Pool persistente. Se crea una vez y se reutiliza en todos los frames."""
    return multiprocessing.Pool(processes=workers)


def split_chunks(items: tuple, n: int) -> tuple[tuple, ...]:
    """Divide items en hasta n bloques contiguos, en orden y sin bloques vacíos.

    Los tamaños difieren como máximo en 1 (reparto equitativo).
    """
    if not items:
        return ()
    n = max(1, min(n, len(items)))
    base, extra = divmod(len(items), n)
    bounds = [i * base + min(i, extra) for i in range(n + 1)]
    return tuple(items[start:end] for start, end in zip(bounds, bounds[1:]))


def consolidate(
    results: list[tuple[tuple[Asteroid, ...], bool, int]],
) -> tuple[tuple[Asteroid, ...], bool, int]:
    """Une los resultados de los workers: asteroides en orden, impacto y destruidos."""
    asteroids = tuple(chain.from_iterable(survivors for survivors, _, _ in results))
    return (
        asteroids,
        any(hit for _, hit, _ in results),
        sum(destroyed for _, _, destroyed in results),
    )


def process_asteroids_parallel(
    pool: Pool,
    asteroids: tuple[Asteroid, ...],
    projectiles: tuple[Projectile, ...],
    player: Player,
    dt: float,
    width: float,
    height: float,
    num_chunks: int,
) -> tuple[tuple[Asteroid, ...], bool, int]:
    chunks = split_chunks(asteroids, num_chunks)
    tasks = [(chunk, projectiles, player, dt, width, height) for chunk in chunks]
    results = pool.starmap(process_asteroids, tasks)  # bloqueante
    return consolidate(results)


def update_parallel(
    pool: Pool,
    state: GameState,
    events: frozenset,
    dt: float,
    width: float,
    height: float,
    num_chunks: int,
) -> GameState:
    """Un frame, versión paralela. Mismo resultado que simulation.update."""
    controlled = refill_from_queue(apply_events(state, events, dt))
    asteroids, player_hit, destroyed = process_asteroids_parallel(
        pool,
        controlled.asteroids,
        controlled.projectiles,
        controlled.player,
        dt,
        width,
        height,
        num_chunks,
    )
    return next_state(controlled, asteroids, player_hit, destroyed, dt, width, height)
