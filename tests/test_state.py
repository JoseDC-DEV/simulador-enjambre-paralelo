import dataclasses

import pytest

from core.entities import Asteroid, Player, Projectile
from core.state import GameState


def make_state() -> GameState:
    return GameState(
        player=Player(x=400.0, y=300.0, vx=0.0, vy=0.0, angle=0.0, lives=3),
        asteroids=(
            Asteroid(id=0, x=10.0, y=10.0, vx=1.0, vy=1.0, radius=15.0, health=1),
            Asteroid(id=1, x=50.0, y=60.0, vx=-1.0, vy=0.0, radius=20.0, health=2),
        ),
        projectiles=(Projectile(id=0, x=0.0, y=0.0, vx=200.0, vy=0.0, ttl=1.0),),
        score=0,
        running=True,
        frame=0,
    )


def test_game_state_is_immutable():
    state = make_state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.score = 100
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.asteroids = ()


def test_game_state_rejects_new_attributes():
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_state().extra = 1


def test_entity_collections_are_tuples_and_cannot_be_modified():
    state = make_state()
    assert isinstance(state.asteroids, tuple)
    assert isinstance(state.projectiles, tuple)
    with pytest.raises(TypeError):
        state.asteroids[0] = state.asteroids[1]
    assert not hasattr(state.asteroids, "append")


def test_replace_returns_new_state_and_keeps_original():
    original = make_state()
    updated = dataclasses.replace(original, score=10, frame=1)

    assert updated is not original
    assert (updated.score, updated.frame) == (10, 1)
    assert (original.score, original.frame) == (0, 0)


def test_replace_shares_unchanged_fields():
    # replace copia referencias, no hace copia profunda: es barato y seguro
    # porque lo compartido es inmutable.
    original = make_state()
    updated = dataclasses.replace(original, score=10)

    assert updated.asteroids is original.asteroids
    assert updated.player is original.player


def test_equality_is_by_value():
    assert make_state() == make_state()


def test_pending_and_won_have_safe_defaults():
    state = make_state()
    assert state.pending == ()
    assert state.won is False


def test_max_active_has_a_moderate_default():
    from core.state import DEFAULT_MAX_ACTIVE

    assert make_state().max_active == DEFAULT_MAX_ACTIVE
