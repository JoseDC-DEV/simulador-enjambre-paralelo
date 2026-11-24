import pytest

from core.collisions import (
    circles_overlap,
    is_hit_by_projectile,
    process_asteroids,
    touches_player,
)
from core.entities import Asteroid, Player, Projectile
from core.transformations import is_on_screen, update_asteroids

WIDTH, HEIGHT = 1200.0, 800.0
DT = 0.1


def make_asteroid(**changes) -> Asteroid:
    base = dict(id=1, x=100.0, y=100.0, vx=0.0, vy=0.0, radius=10.0, health=1)
    return Asteroid(**{**base, **changes})


def make_projectile(**changes) -> Projectile:
    base = dict(id=1, x=100.0, y=100.0, vx=0.0, vy=0.0, ttl=1.0)
    return Projectile(**{**base, **changes})


def make_player(**changes) -> Player:
    base = dict(x=600.0, y=400.0, vx=0.0, vy=0.0, angle=0.0, lives=1)
    return Player(**{**base, **changes})


def test_circles_overlap():
    assert circles_overlap(0, 0, 5, 3, 0, 5)
    assert circles_overlap(0, 0, 5, 10, 0, 5)  # justo tocándose
    assert not circles_overlap(0, 0, 5, 10.1, 0, 5)


def test_projectile_hit_detection():
    asteroid = make_asteroid()

    assert is_hit_by_projectile(asteroid, (make_projectile(x=105.0),))
    assert not is_hit_by_projectile(asteroid, (make_projectile(x=300.0),))
    assert not is_hit_by_projectile(asteroid, ())


def test_touches_player():
    asteroid = make_asteroid(x=600.0, y=400.0)

    assert touches_player(asteroid, make_player(x=615.0))
    assert not touches_player(asteroid, make_player(x=700.0))


def test_without_projectiles_nothing_is_destroyed_and_asteroids_move():
    asteroids = (
        make_asteroid(id=0, x=100.0, vx=10.0),
        make_asteroid(id=1, x=300.0, vy=-5.0),
    )
    survivors, player_hit, destroyed = process_asteroids(
        asteroids, (), make_player(), DT, WIDTH, HEIGHT
    )

    assert survivors == update_asteroids(asteroids, DT)
    assert player_hit is False
    assert destroyed == 0


def test_projectile_destroys_only_the_asteroid_it_touches():
    asteroids = (make_asteroid(id=0, x=100.0, y=100.0), make_asteroid(id=1, x=500.0, y=500.0))
    survivors, player_hit, destroyed = process_asteroids(
        asteroids, (make_projectile(x=100.0, y=100.0),), make_player(), DT, WIDTH, HEIGHT
    )

    assert tuple(a.id for a in survivors) == (1,)
    assert player_hit is False
    assert destroyed == 1


def test_one_projectile_can_destroy_several_overlapping_asteroids():
    asteroids = (
        make_asteroid(id=0, x=100.0, y=100.0),
        make_asteroid(id=1, x=104.0, y=100.0),
        make_asteroid(id=2, x=900.0, y=700.0),
    )
    survivors, _, _ = process_asteroids(
        asteroids, (make_projectile(),), make_player(), DT, WIDTH, HEIGHT
    )

    assert tuple(a.id for a in survivors) == (2,)


def test_asteroid_touching_player_sets_player_hit():
    asteroids = (make_asteroid(x=600.0, y=400.0),)
    survivors, player_hit, destroyed = process_asteroids(
        asteroids, (), make_player(), DT, WIDTH, HEIGHT
    )

    assert player_hit is True
    assert len(survivors) == 1
    assert destroyed == 0


def test_asteroid_destroyed_by_projectile_does_not_hit_player():
    asteroids = (make_asteroid(x=600.0, y=400.0),)
    projectiles = (make_projectile(x=600.0, y=400.0),)
    survivors, player_hit, destroyed = process_asteroids(
        asteroids, projectiles, make_player(), DT, WIDTH, HEIGHT
    )

    assert survivors == ()
    assert player_hit is False
    assert destroyed == 1


def test_process_asteroids_keeps_inputs_intact_and_is_deterministic():
    asteroids = (make_asteroid(id=0), make_asteroid(id=1, x=700.0))
    projectiles = (make_projectile(),)
    player = make_player()

    first = process_asteroids(asteroids, projectiles, player, DT, WIDTH, HEIGHT)
    second = process_asteroids(asteroids, projectiles, player, DT, WIDTH, HEIGHT)

    assert first == second
    assert len(asteroids) == 2 and asteroids[0].x == 100.0


def test_asteroids_leaving_the_screen_are_removed_and_do_not_score():
    leaving = make_asteroid(id=0, x=WIDTH + 9.0, y=400.0, vx=500.0, radius=10.0)  # sale
    staying = make_asteroid(id=1, x=300.0, y=300.0, vx=10.0)
    survivors, player_hit, destroyed = process_asteroids(
        (leaving, staying), (), make_player(), DT, WIDTH, HEIGHT
    )

    assert tuple(a.id for a in survivors) == (1,)
    assert destroyed == 0  # salir de pantalla no es destruirlo
    assert player_hit is False


def test_asteroid_just_outside_the_edge_is_still_alive_until_fully_out():
    assert is_on_screen(make_asteroid(x=-9.0, y=100.0, radius=10.0), WIDTH, HEIGHT)
    assert not is_on_screen(make_asteroid(x=-11.0, y=100.0, radius=10.0), WIDTH, HEIGHT)
