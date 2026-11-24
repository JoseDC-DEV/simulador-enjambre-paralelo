import math
from collections import defaultdict

import pygame
import pytest

from core.entities import Player
from core.simulation import LEFT, SHOOT, THRUST, create_initial_state
from render.renderer import (
    SHIP_SIZE,
    build_hud,
    key_presses,
    read_events,
    ship_points,
    window_closed,
)


def make_player(**changes) -> Player:
    base = dict(x=100.0, y=200.0, vx=0.0, vy=0.0, angle=0.0, lives=3)
    return Player(**{**base, **changes})


def test_ship_has_three_points_at_ship_size_from_center():
    player = make_player(angle=0.7)
    points = ship_points(player)

    assert len(points) == 3
    for x, y in points:
        assert math.hypot(x - player.x, y - player.y) == pytest.approx(SHIP_SIZE)


def test_ship_nose_points_in_facing_direction():
    nose = ship_points(make_player(angle=0.0))[0]
    assert nose == (100.0 + SHIP_SIZE, 200.0)


def test_read_events_translates_pressed_keys():
    keys = defaultdict(bool, {pygame.K_LEFT: True, pygame.K_UP: True})
    assert read_events(keys) == frozenset({LEFT, THRUST})
    assert read_events(defaultdict(bool)) == frozenset()


def test_window_closed():
    assert window_closed([pygame.event.Event(pygame.QUIT)])
    assert not window_closed([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)])
    assert not window_closed([])


def test_key_presses_returns_only_keydown_keys():
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a),
        pygame.event.Event(pygame.QUIT),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
    ]
    assert key_presses(events) == (pygame.K_a, pygame.K_ESCAPE)


def test_space_is_mapped_to_shoot():
    keys = defaultdict(bool, {pygame.K_SPACE: True})
    assert read_events(keys) == frozenset({SHOOT})


def test_build_hud_reports_state_and_mode():
    state = create_initial_state(25, 1200.0, 800.0)
    hud = build_hud(state, "secuencial", 1.5, 60.0)

    assert isinstance(hud, tuple)
    assert any("25" in line for line in hud)
    assert any("secuencial" in line for line in hud)
