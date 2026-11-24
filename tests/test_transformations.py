from dataclasses import replace

import pytest

from core.entities import Asteroid, Player, Projectile
from core.state import GameState
from core.transformations import (
    move_asteroid,
    move_player,
    move_projectile,
    POINTS_PER_ASTEROID,
    next_state,
    remove_expired_projectiles,
    update_asteroid,
    update_asteroids,
    update_projectiles,
    is_on_screen,
)

WIDTH, HEIGHT = 1200.0, 800.0


def make_asteroid(**changes) -> Asteroid:
    base = dict(id=1, x=100.0, y=200.0, vx=10.0, vy=-20.0, radius=10.0, health=1)
    return Asteroid(**{**base, **changes})


def make_projectile(**changes) -> Projectile:
    base = dict(id=1, x=0.0, y=0.0, vx=100.0, vy=0.0, ttl=1.0)
    return Projectile(**{**base, **changes})


def make_player(**changes) -> Player:
    base = dict(x=400.0, y=300.0, vx=0.0, vy=0.0, angle=0.0, lives=3)
    return Player(**{**base, **changes})


def make_state() -> GameState:
    return GameState(
        player=make_player(vx=50.0),
        asteroids=(make_asteroid(id=0), make_asteroid(id=1)),
        projectiles=(make_projectile(id=0, ttl=1.0), make_projectile(id=1, ttl=0.05)),
        score=7,
        running=True,
        frame=3,
    )


# --- Asteroides ---

def test_move_asteroid_advances_position_and_keeps_original():
    original = make_asteroid()
    moved = move_asteroid(original, 0.5)

    assert moved.x == pytest.approx(105.0)
    assert moved.y == pytest.approx(190.0)
    assert (moved.id, moved.vx, moved.vy) == (original.id, original.vx, original.vy)
    assert (original.x, original.y) == (100.0, 200.0)


def test_asteroids_do_not_wrap_around_the_edges():
    a = make_asteroid(x=1195.0, y=5.0, vx=100.0, vy=-100.0)
    updated = update_asteroid(a, 0.1)

    assert updated.x == pytest.approx(1205.0)  # sigue de largo: no vuelve por el otro lado
    assert updated.y == pytest.approx(-5.0)


def test_is_on_screen_boundaries():
    assert is_on_screen(make_asteroid(x=600.0, y=400.0), WIDTH, HEIGHT)
    assert is_on_screen(make_asteroid(x=WIDTH + 10.0, y=0.0, radius=10.0), WIDTH, HEIGHT)
    assert not is_on_screen(make_asteroid(x=WIDTH + 10.1, y=0.0, radius=10.0), WIDTH, HEIGHT)
    assert not is_on_screen(make_asteroid(x=600.0, y=-10.1, radius=10.0), WIDTH, HEIGHT)


def test_update_asteroids_returns_new_tuple_preserving_order_and_ids():
    original = tuple(make_asteroid(id=i, x=float(i)) for i in range(5))
    updated = update_asteroids(original, 1.0)

    assert isinstance(updated, tuple)
    assert updated is not original
    assert tuple(a.id for a in updated) == (0, 1, 2, 3, 4)
    assert tuple(a.x for a in original) == (0.0, 1.0, 2.0, 3.0, 4.0)


def test_update_asteroids_is_deterministic():
    asteroids = tuple(make_asteroid(id=i, x=float(i * 7)) for i in range(100))
    first = update_asteroids(asteroids, 0.016)
    second = update_asteroids(asteroids, 0.016)
    assert first == second


def test_update_asteroids_empty_tuple():
    assert update_asteroids((), 0.1) == ()


# --- Proyectiles ---

def test_move_projectile_advances_position_and_reduces_ttl():
    original = make_projectile()
    moved = move_projectile(original, 0.1)

    assert moved.x == pytest.approx(10.0)
    assert moved.ttl == pytest.approx(0.9)
    assert (original.x, original.ttl) == (0.0, 1.0)


def test_remove_expired_projectiles():
    projectiles = (
        make_projectile(id=0, ttl=0.5),
        make_projectile(id=1, ttl=0.0),
        make_projectile(id=2, ttl=-0.1),
    )
    remaining = remove_expired_projectiles(projectiles)

    assert tuple(p.id for p in remaining) == (0,)
    assert len(projectiles) == 3


def test_update_projectiles_moves_and_discards_expired():
    projectiles = (make_projectile(id=0, ttl=1.0), make_projectile(id=1, ttl=0.05))
    updated = update_projectiles(projectiles, 0.1)

    assert tuple(p.id for p in updated) == (0,)
    assert updated[0].ttl == pytest.approx(0.9)


# --- Nave ---

def test_move_player_moves_and_wraps():
    player = make_player(x=1195.0, y=5.0, vx=100.0, vy=-100.0)
    moved = move_player(player, 0.1, WIDTH, HEIGHT)

    assert moved.x == pytest.approx(5.0)
    assert moved.y == pytest.approx(795.0)
    assert (player.x, player.y) == (1195.0, 5.0)


# --- Estado ---

def test_next_state_returns_new_state_and_keeps_original():
    state = make_state()
    new_asteroids = (make_asteroid(id=9),)
    result = next_state(state, new_asteroids, False, 1, 0.1, WIDTH, HEIGHT)  # 1 destruido

    assert result is not state
    assert result.frame == 4
    assert result.asteroids is new_asteroids
    assert result.player.x == pytest.approx(405.0)
    assert tuple(p.id for p in result.projectiles) == (0,)
    assert result.score == 7 + POINTS_PER_ASTEROID
    assert result.running is True

    # El estado original permanece intacto.
    assert state.frame == 3
    assert state.player.x == 400.0
    assert state.score == 7
    assert len(state.asteroids) == 2
    assert len(state.projectiles) == 2


def test_next_state_without_destroyed_asteroids_keeps_score():
    state = make_state()
    result = next_state(state, state.asteroids, False, 0, 0.1, WIDTH, HEIGHT)
    assert result.score == state.score


def test_next_state_player_hit_ends_the_game():
    state = make_state()
    result = next_state(state, state.asteroids, True, 0, 0.1, WIDTH, HEIGHT)

    assert result.player.lives == 0
    assert result.running is False
    assert state.player.lives == 3 and state.running is True


def test_next_state_without_destroyed_asteroids_keeps_score_even_if_some_left():
    state = make_state()
    result = next_state(state, state.asteroids[:1], False, 0, 0.1, WIDTH, HEIGHT)  # uno salió
    assert result.score == state.score


def test_next_state_declares_victory_when_queue_and_screen_are_empty():
    state = replace(make_state(), pending=())
    result = next_state(state, (), False, 0, 0.1, WIDTH, HEIGHT)

    assert result.won is True
    assert result.running is False
    assert result.player.lives == 3  # ganó, no murió
    assert state.won is False and state.running is True


def test_next_state_no_victory_while_asteroids_are_still_on_screen():
    state = replace(make_state(), pending=())
    result = next_state(state, state.asteroids, False, 0, 0.1, WIDTH, HEIGHT)

    assert result.won is False and result.running is True


def test_next_state_no_victory_while_asteroids_are_queued():
    state = replace(make_state(), pending=(make_asteroid(id=99),))
    result = next_state(state, (), False, 0, 0.1, WIDTH, HEIGHT)

    assert result.won is False and result.running is True


def test_player_hit_beats_victory():
    state = replace(make_state(), pending=())
    result = next_state(state, (), True, 0, 0.1, WIDTH, HEIGHT)

    assert result.won is False
    assert result.running is False and result.player.lives == 0
