import dataclasses
import pickle

import pytest

from core.entities import Asteroid, Player, Projectile


def make_asteroid() -> Asteroid:
    return Asteroid(id=1, x=10.0, y=20.0, vx=1.0, vy=-1.0, radius=15.0, health=3)


def make_player() -> Player:
    return Player(x=400.0, y=300.0, vx=0.0, vy=0.0, angle=0.0, lives=3)


def make_projectile() -> Projectile:
    return Projectile(id=7, x=0.0, y=0.0, vx=200.0, vy=0.0, ttl=1.5)


@pytest.mark.parametrize(
    "entity, field",
    [
        (make_asteroid(), "x"),
        (make_player(), "lives"),
        (make_projectile(), "ttl"),
    ],
)
def test_entities_are_immutable(entity, field):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(entity, field, 999)


def test_replace_returns_new_instance_and_keeps_original():
    original = make_asteroid()
    moved = dataclasses.replace(original, x=50.0)

    assert moved is not original
    assert moved.x == 50.0
    assert original.x == 10.0


def test_equality_is_by_value_and_hashable():
    assert make_asteroid() == make_asteroid()
    assert hash(make_asteroid()) == hash(make_asteroid())


def test_entities_survive_pickle_roundtrip():
    # Necesario para enviarlas a procesos hijos con multiprocessing.
    for entity in (make_asteroid(), make_player(), make_projectile()):
        assert pickle.loads(pickle.dumps(entity)) == entity
