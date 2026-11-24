"""Capa gráfica (Pygame): dibuja un GameState y traduce el teclado a eventos.

Solo LEE el estado para dibujarlo; nunca lo modifica. core/ no depende de
pygame: toda la lógica del juego se puede probar sin ventana.
"""

import math

import pygame

from core.entities import Player
from core.simulation import LEFT, RIGHT, SHOOT, THRUST
from core.state import GameState

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
YELLOW = (255, 220, 80)

SHIP_SIZE = 14.0
SHIP_ANGLES = (0.0, 2.5, -2.5)  # nariz y dos puntas traseras (radianes)

# (tecla de Pygame, evento del juego)
KEYMAP = (
    (pygame.K_LEFT, LEFT),
    (pygame.K_RIGHT, RIGHT),
    (pygame.K_UP, THRUST),
    (pygame.K_SPACE, SHOOT),
)


# --- Funciones puras (sin ventana) ---

def read_events(keys) -> frozenset:
    """Traduce las teclas pulsadas a eventos del juego."""
    return frozenset(event for key, event in KEYMAP if keys[key])


def window_closed(pygame_events) -> bool:
    return any(e.type == pygame.QUIT for e in pygame_events)


def key_presses(pygame_events) -> tuple:
    """Teclas que se acaban de pulsar en este frame (eventos KEYDOWN)."""
    return tuple(e.key for e in pygame_events if e.type == pygame.KEYDOWN)


def ship_points(player: Player, size: float = SHIP_SIZE) -> tuple:
    """Vértices del triángulo de la nave según su posición y orientación."""
    return tuple(
        (
            player.x + size * math.cos(player.angle + offset),
            player.y + size * math.sin(player.angle + offset),
        )
        for offset in SHIP_ANGLES
    )


def build_hud(state: GameState, mode_label: str, update_ms: float, fps: float) -> tuple:
    return (
        f"Modo: {mode_label}",
        f"En pantalla: {len(state.asteroids)}/{state.max_active}   En cola: {len(state.pending)}",
        f"Actualización: {update_ms:.2f} ms",
        f"FPS: {fps:.0f}",
        f"Puntos: {state.score}",
    )


# --- Dibujo (efectos sobre la pantalla, no sobre el estado) ---

def draw_asteroids(screen, state: GameState) -> None:
    for a in state.asteroids:
        pygame.draw.circle(screen, GRAY, (int(a.x), int(a.y)), int(a.radius), 1)


def draw_projectiles(screen, state: GameState) -> None:
    for p in state.projectiles:
        pygame.draw.circle(screen, YELLOW, (int(p.x), int(p.y)), 2)


def draw_player(screen, state: GameState) -> None:
    pygame.draw.polygon(screen, WHITE, ship_points(state.player), 1)


def draw_hud(screen, font, lines: tuple) -> None:
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, WHITE), (10, 10 + i * 22))


def draw_frame(screen, font, state: GameState, hud: tuple) -> None:
    screen.fill(BLACK)
    draw_asteroids(screen, state)
    draw_projectiles(screen, state)
    draw_player(screen, state)
    draw_hud(screen, font, hud)
    pygame.display.flip()
