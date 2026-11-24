import dataclasses

import pygame
import pytest

from render.menu import MenuConfig, menu_lines, mode_label, next_config

SIZES = (1000, 3000, 5000)


def test_size_keys_select_asteroid_count():
    config = MenuConfig(asteroids=1000, parallel=True)

    assert next_config(config, pygame.K_2, SIZES).asteroids == 3000
    assert next_config(config, pygame.K_3, SIZES).asteroids == 5000
    assert next_config(config, pygame.K_1, SIZES).asteroids == 1000


def test_m_toggles_mode_and_other_keys_change_nothing():
    config = MenuConfig(asteroids=1000, parallel=True)

    assert next_config(config, pygame.K_m, SIZES).parallel is False
    assert next_config(next_config(config, pygame.K_m, SIZES), pygame.K_m, SIZES) == config
    assert next_config(config, pygame.K_a, SIZES) == config


def test_next_config_returns_new_object_and_keeps_original():
    config = MenuConfig(asteroids=1000, parallel=True)
    changed = next_config(config, pygame.K_3, SIZES)

    assert changed is not config
    assert config.asteroids == 1000


def test_menu_config_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        MenuConfig(asteroids=1000, parallel=True).parallel = False


def test_menu_lines_mark_selected_option_and_mode():
    lines = menu_lines(MenuConfig(3000, True), SIZES, workers=3)

    assert any(l.startswith(">") and "3000" in l for l in lines)
    assert sum(l.startswith(">") for l in lines) == 1
    assert any("paralelo (3 workers)" in l for l in lines)
    assert any("secuencial" in l for l in menu_lines(MenuConfig(3000, False), SIZES, 3))


def test_mode_label():
    assert mode_label(False, 4) == "secuencial"
    assert "4 workers" in mode_label(True, 4)
