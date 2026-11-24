from dataclasses import replace

import pytest

from core.entities import Asteroid, Player
from core.simulation import create_initial_state
from core.state import DEFAULT_MAX_ACTIVE
from core.waves import (
    AIMED_EVERY,
    SAFE_SPAWN_DISTANCE,
    aim_at,
    is_safe_entry,
    is_victory,
    refill_from_queue,
    release_all,
)

WIDTH, HEIGHT = 1200.0, 800.0


def make_player(**changes) -> Player:
    base = dict(x=600.0, y=400.0, vx=0.0, vy=0.0, angle=0.0, lives=1)
    return Player(**{**base, **changes})


def make_asteroid(**changes) -> Asteroid:
    base = dict(id=1, x=0.0, y=400.0, vx=50.0, vy=0.0, radius=10.0, health=1)
    return Asteroid(**{**base, **changes})


# --- Apuntar ---

def test_aim_at_points_velocity_towards_player_and_keeps_speed():
    asteroid = make_asteroid(x=0.0, y=0.0, vx=30.0, vy=40.0)  # rapidez 50
    aimed = aim_at(asteroid, make_player(x=300.0, y=0.0))

    assert aimed.vx == pytest.approx(50.0)
    assert aimed.vy == pytest.approx(0.0, abs=1e-9)
    assert (asteroid.vx, asteroid.vy) == (30.0, 40.0)  # el original no cambia


def test_aim_at_same_position_returns_same_asteroid():
    asteroid = make_asteroid(x=600.0, y=400.0)
    assert aim_at(asteroid, make_player()) is asteroid


# --- Cola con límite simultáneo ---

def test_default_limit_is_moderate():
    assert create_initial_state(100, WIDTH, HEIGHT).max_active == DEFAULT_MAX_ACTIVE


def test_initial_fill_stops_at_the_limit_and_keeps_queue_order():
    state = create_initial_state(100, WIDTH, HEIGHT, max_active=15)
    result = refill_from_queue(state)

    assert len(result.asteroids) == 15
    assert len(result.pending) == 85
    assert tuple(a.id for a in result.asteroids) == tuple(range(15))
    assert tuple(a.id for a in result.pending) == tuple(range(15, 100))
    assert len(state.pending) == 100 and state.asteroids == ()  # original intacto


def test_refill_enters_exactly_one_per_free_slot():
    full = refill_from_queue(create_initial_state(100, WIDTH, HEIGHT, max_active=15))
    one_left = replace(full, asteroids=full.asteroids[1:])  # sale uno
    result = refill_from_queue(one_left)

    assert len(result.asteroids) == 15
    assert result.asteroids[-1].id == 15  # entra el siguiente de la cola
    assert len(result.pending) == 84


def test_refill_does_nothing_when_screen_is_full():
    full = refill_from_queue(create_initial_state(100, WIDTH, HEIGHT, max_active=15))
    assert refill_from_queue(full) is full


def test_refill_with_short_queue_releases_what_is_left():
    state = create_initial_state(4, WIDTH, HEIGHT, max_active=15)
    result = refill_from_queue(state)

    assert len(result.asteroids) == 4 and result.pending == ()


def test_refill_never_exceeds_limit_even_if_already_over():
    state = refill_from_queue(create_initial_state(30, WIDTH, HEIGHT, max_active=10))
    lowered = replace(state, max_active=5)
    assert refill_from_queue(lowered) is lowered


def test_only_marked_asteroids_are_aimed_at_the_player():
    state = create_initial_state(200, WIDTH, HEIGHT, seed=2, max_active=200)
    result = refill_from_queue(state)
    original = {a.id: a for a in state.pending}

    for a in result.asteroids:
        if a.id % AIMED_EVERY == 0:
            dx, dy = state.player.x - a.x, state.player.y - a.y
            # velocidad paralela a la dirección hacia la nave
            assert a.vx * dy - a.vy * dx == pytest.approx(0.0, abs=1e-6)
            assert a.vx * dx + a.vy * dy > 0
        else:
            assert a == original[a.id]


# --- Entrada segura ---

def test_is_safe_entry_depends_on_distance_to_player():
    player = make_player(x=100.0, y=100.0)
    assert not is_safe_entry(make_asteroid(x=100.0 + SAFE_SPAWN_DISTANCE - 1, y=100.0), player)
    assert is_safe_entry(make_asteroid(x=100.0 + SAFE_SPAWN_DISTANCE, y=100.0), player)


def test_unsafe_head_of_queue_defers_itself_and_those_behind_it():
    player = make_player(x=0.0, y=400.0)
    safe_first = make_asteroid(id=1, x=900.0, y=100.0)
    unsafe = make_asteroid(id=2, x=10.0, y=400.0)  # aparecería encima de la nave
    safe_after = make_asteroid(id=3, x=1000.0, y=700.0)
    state = replace(
        create_initial_state(0, WIDTH, HEIGHT),
        player=player,
        pending=(safe_first, unsafe, safe_after),
    )
    result = refill_from_queue(state)

    assert tuple(a.id for a in result.asteroids) == (1,)
    assert tuple(a.id for a in result.pending) == (2, 3)  # el orden se conserva


# --- Peor caso (benchmark) ---

def test_release_all():
    state = create_initial_state(50, WIDTH, HEIGHT)
    result = release_all(state)

    assert result.pending == ()
    assert len(result.asteroids) == 50
    assert len(state.pending) == 50


# --- Victoria ---

def test_is_victory_requires_empty_queue_and_empty_screen():
    asteroid = make_asteroid()

    assert is_victory((), ())
    assert not is_victory((asteroid,), ())  # aún quedan en la cola
    assert not is_victory((), (asteroid,))  # aún quedan en pantalla
