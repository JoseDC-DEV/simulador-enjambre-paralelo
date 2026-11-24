"""Pantallas de menú y de fin de partida.

La configuración del menú es un dataclass congelado: elegir una opción
devuelve una configuración nueva, igual que en el resto del proyecto.
"""

from dataclasses import dataclass, replace

import pygame

from render.renderer import BLACK, GRAY, WHITE, YELLOW

SIZE_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)


@dataclass(frozen=True)
class MenuConfig:
    asteroids: int
    parallel: bool


def mode_label(parallel: bool, workers: int) -> str:
    return f"paralelo ({workers} workers)" if parallel else "secuencial"


def next_config(config: MenuConfig, key: int, sizes: tuple) -> MenuConfig:
    """Aplica una tecla a la configuración y devuelve la configuración nueva."""
    if key == pygame.K_m:
        return replace(config, parallel=not config.parallel)
    available = SIZE_KEYS[: len(sizes)]
    if key in available:
        return replace(config, asteroids=sizes[available.index(key)])
    return config


def menu_lines(config: MenuConfig, sizes: tuple, workers: int) -> tuple:
    options = tuple(
        f"{'>' if n == config.asteroids else ' '} [{i + 1}] {n} asteroides"
        for i, n in enumerate(sizes)
    )
    return (
        "Cantidad de asteroides:",
        *options,
        "",
        f"[M] Modo: {mode_label(config.parallel, workers)}",
        "",
        "[ENTER] Jugar        [ESC] Salir",
        "",
        "Izq/Der: rotar   Arriba: acelerar   Espacio: disparar",
    )


def draw_lines(screen, font, lines: tuple, x: int, y: int, color=WHITE) -> None:
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, color), (x, y + i * 30))


def draw_menu(screen, title_font, font, lines: tuple) -> None:
    screen.fill(BLACK)
    screen.blit(title_font.render("FALLEN ASTEROIDS", True, YELLOW), (60, 60))
    draw_lines(screen, font, lines, 60, 160)
    pygame.display.flip()


def draw_end_screen(screen, title_font, font, title: str, score: int) -> None:
    """Pantalla final: sirve para GAME OVER y para VICTORIA."""
    screen.fill(BLACK)
    screen.blit(title_font.render(title, True, YELLOW), (60, 60))
    draw_lines(
        screen,
        font,
        (f"Puntos: {score}", "", "[ENTER] Volver al menú"),
        60,
        160,
        GRAY,
    )
    pygame.display.flip()
