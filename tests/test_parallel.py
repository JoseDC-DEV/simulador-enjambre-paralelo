from dataclasses import replace
from functools import reduce

import pytest

from core.collisions import process_asteroids
from core.entities import Projectile
from core.parallel import (
    consolidate,
    create_pool,
    process_asteroids_parallel,
    split_chunks,
    update_parallel,
)
from core.simulation import LEFT, SHOOT, THRUST, create_initial_state, update
from core.waves import release_all

WIDTH, HEIGHT = 1200.0, 800.0
DT = 1 / 60
SIZES = [1000, 3000, 5000]
NO_EVENTS = frozenset()


@pytest.fixture(scope="module")
def pool():
    # Pool persistente: se crea una vez y se reutiliza en todos los tests.
    with create_pool(2) as p:
        yield p


def scenario(n):
    """Estado con proyectiles sobre algunos asteroides y un asteroide sobre la nave."""
    state = release_all(create_initial_state(n, WIDTH, HEIGHT, seed=1))
    targets = state.asteroids[10:13]
    projectiles = tuple(
        Projectile(id=i, x=a.x, y=a.y, vx=0.0, vy=0.0, ttl=1.0)
        for i, a in enumerate(targets)
    )
    victim = state.asteroids[n - 1]  # cae en el último bloque
    player = replace(state.player, x=victim.x, y=victim.y)
    return replace(state, projectiles=projectiles, player=player)


# --- Segmentación y consolidación (puras, sin procesos) ---

@pytest.mark.parametrize("n", [1, 2, 3, 7, 16])
def test_split_chunks_preserves_content_and_order(n):
    items = tuple(range(100))
    chunks = split_chunks(items, n)

    assert len(chunks) == n
    assert tuple(x for chunk in chunks for x in chunk) == items
    assert all(isinstance(c, tuple) for c in chunks)


def test_split_chunks_sizes_differ_by_at_most_one():
    sizes = [len(c) for c in split_chunks(tuple(range(10)), 3)]
    assert sizes == [4, 3, 3]
    assert max(sizes) - min(sizes) <= 1


def test_split_chunks_never_returns_empty_chunks():
    assert split_chunks((1, 2, 3), 10) == ((1,), (2,), (3,))


def test_split_chunks_empty_input():
    assert split_chunks((), 4) == ()


def test_consolidate_flattens_in_order_and_combines_hit_flags():
    assert consolidate([((1, 2), False, 1), ((3,), True, 0), ((4, 5), False, 2)]) == (
        (1, 2, 3, 4, 5),
        True,
        3,
    )
    assert consolidate([((1,), False, 0), ((2,), False, 0)]) == ((1, 2), False, 0)
    assert consolidate([]) == ((), False, 0)


# --- Equivalencia paralelo vs secuencial ---

@pytest.mark.parametrize("n", SIZES)
def test_parallel_processing_equals_sequential(pool, n):
    s = scenario(n)

    sequential = process_asteroids(
        s.asteroids, s.projectiles, s.player, DT, WIDTH, HEIGHT
    )
    parallel = process_asteroids_parallel(
        pool, s.asteroids, s.projectiles, s.player, DT, WIDTH, HEIGHT, 4
    )

    assert parallel == sequential
    assert len(parallel[0]) < n  # los proyectiles sí destruyeron asteroides
    assert parallel[1] is True  # y el asteroide sobre la nave fue detectado
    assert parallel[2] >= 3  # y se contaron los destruidos


@pytest.mark.parametrize("num_chunks", [1, 3, 7])
def test_result_does_not_depend_on_number_of_chunks(pool, num_chunks):
    s = scenario(1000)
    expected = process_asteroids(s.asteroids, s.projectiles, s.player, DT, WIDTH, HEIGHT)

    assert process_asteroids_parallel(
        pool, s.asteroids, s.projectiles, s.player, DT, WIDTH, HEIGHT, num_chunks
    ) == expected


def test_parallel_update_equals_sequential_update_over_many_frames(pool):
    initial = create_initial_state(1000, WIDTH, HEIGHT, seed=3)
    events = frozenset({THRUST, LEFT, SHOOT})

    parallel = reduce(
        lambda s, _: update_parallel(pool, s, events, DT, WIDTH, HEIGHT, 4),
        range(250),
        initial,
    )
    sequential = reduce(
        lambda s, _: update(s, events, DT, WIDTH, HEIGHT), range(250), initial
    )

    assert parallel == sequential
    assert parallel.frame == 250
    assert len(parallel.asteroids) <= parallel.max_active
    assert len(parallel.pending) < 1000  # la cola se está consumiendo


def test_parallel_update_returns_new_state_and_keeps_original(pool):
    state = create_initial_state(1000, WIDTH, HEIGHT, seed=4)
    snapshot = create_initial_state(1000, WIDTH, HEIGHT, seed=4)

    result = update_parallel(pool, state, NO_EVENTS, DT, WIDTH, HEIGHT, 4)

    assert result is not state
    assert result.frame == 1
    assert state == snapshot


def test_parallel_update_detects_game_over(pool):
    s = scenario(1000)
    result = update_parallel(pool, s, NO_EVENTS, DT, WIDTH, HEIGHT, 4)

    assert result.running is False
    assert result.player.lives == 0


def test_parallel_is_deterministic(pool):
    state = create_initial_state(3000, WIDTH, HEIGHT, seed=5)
    first = update_parallel(pool, state, NO_EVENTS, DT, WIDTH, HEIGHT, 4)
    second = update_parallel(pool, state, NO_EVENTS, DT, WIDTH, HEIGHT, 4)

    assert first == second
