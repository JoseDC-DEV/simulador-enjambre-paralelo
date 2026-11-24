"""Fallen Asteroids: punto de entrada.

Uso, desde la raíz del proyecto:
    python main.py
    python main.py --asteroids 100 --mode parallel --workers 4
    python main.py --asteroids 5000 --max-active 5000   # modo estrés (demo de paralelismo)

Flujo: menú -> partida -> (game over o victoria) -> menú.
Cola de meteoritos: nunca hay más de --max-active en pantalla; cada vez que uno
sale (o es destruido) entra el siguiente. Victoria: agotar la cola y despejar la pantalla.
Controles: izquierda/derecha rotan, arriba acelera, espacio dispara,
ESC vuelve al menú (o sale, si ya estás en él).

Arquitectura: núcleo funcional + capa imperativa fina. Este archivo es la
capa imperativa: lee el teclado, llama a la función pura de actualización y
dibuja. El único "cambio" es volver a enlazar la variable local `state` con
el GameState nuevo en cada frame; ningún GameState se modifica.
"""

import argparse
from functools import reduce
from time import perf_counter

import pygame

from config import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    FPS_OBJETIVO,
    NIVELES_JUEGO,
    WORKERS,
)
from core.parallel import create_pool, update_parallel
from core.simulation import create_initial_state, update
from core.state import DEFAULT_MAX_ACTIVE
from render.menu import (
    MenuConfig,
    draw_end_screen,
    draw_menu,
    menu_lines,
    mode_label,
    next_config,
)
from render.renderer import (
    build_hud,
    draw_frame,
    key_presses,
    read_events,
    window_closed,
)

DT = 1 / FPS_OBJETIVO  # paso de tiempo fijo, igual que en el benchmark
EXIT, MENU, GAME_OVER, VICTORY = "exit", "menu", "game_over", "victory"  # resultados


END_TITLES = {GAME_OVER: "GAME OVER", VICTORY: "¡VICTORIA!"}


def make_step(parallel, pool, workers):
    """Devuelve la función (state, events) -> GameState del modo elegido."""
    if parallel:
        def step(state, events):
            return update_parallel(
                pool, state, events, DT, ANCHO_PANTALLA, ALTO_PANTALLA, workers
            )
    else:
        def step(state, events):
            return update(state, events, DT, ANCHO_PANTALLA, ALTO_PANTALLA)
    return step


def run_menu(screen, title_font, font, clock, config, sizes, workers):
    """Muestra el menú. Devuelve la MenuConfig elegida, o None si se sale."""
    while True:
        pygame_events = pygame.event.get()
        keys = key_presses(pygame_events)
        if window_closed(pygame_events) or pygame.K_ESCAPE in keys:
            return None
        config = reduce(lambda c, k: next_config(c, k, sizes), keys, config)
        if pygame.K_RETURN in keys:
            return config
        draw_menu(screen, title_font, font, menu_lines(config, sizes, workers))
        clock.tick(FPS_OBJETIVO)


def play(screen, font, clock, initial_state, step, label):
    """Bucle de la partida. Devuelve (resultado, estado final)."""
    state = initial_state
    while state.running:
        pygame_events = pygame.event.get()
        if window_closed(pygame_events):
            return EXIT, state
        if pygame.K_ESCAPE in key_presses(pygame_events):
            return MENU, state
        events = read_events(pygame.key.get_pressed())

        start = perf_counter()
        state = step(state, events)
        update_ms = (perf_counter() - start) * 1000

        hud = build_hud(state, label, update_ms, clock.get_fps())
        draw_frame(screen, font, state, hud)
        clock.tick(FPS_OBJETIVO)
    # El núcleo puso running=False: por un impacto (derrota) o por victoria.
    return (VICTORY if state.won else GAME_OVER), state


def show_end_screen(screen, title_font, font, clock, title, score):
    """Pantalla de fin. Devuelve True para volver al menú, False para salir."""
    while True:
        pygame_events = pygame.event.get()
        if window_closed(pygame_events):
            return False
        if {pygame.K_RETURN, pygame.K_ESCAPE} & set(key_presses(pygame_events)):
            return True
        draw_end_screen(screen, title_font, font, title, score)
        clock.tick(FPS_OBJETIVO)


def app(args, pool):
    pygame.init()
    try:
        screen = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
        pygame.display.set_caption("Fallen Asteroids")
        title_font = pygame.font.Font(None, 72)
        font = pygame.font.Font(None, 24)
        menu_font = pygame.font.Font(None, 32)
        clock = pygame.time.Clock()
        sizes = tuple(NIVELES_JUEGO)
        config = MenuConfig(args.asteroids, args.mode == "parallel")

        while True:
            config = run_menu(
                screen, title_font, menu_font, clock, config, sizes, args.workers
            )
            if config is None:
                return
            state = create_initial_state(
                config.asteroids,
                ANCHO_PANTALLA,
                ALTO_PANTALLA,
                seed=args.seed,
                max_active=args.max_active,
            )
            outcome, final = play(
                screen,
                font,
                clock,
                state,
                make_step(config.parallel, pool, args.workers),
                mode_label(config.parallel, args.workers),
            )
            if outcome == EXIT:
                return
            if outcome in END_TITLES and not show_end_screen(
                screen, title_font, menu_font, clock, END_TITLES[outcome], final.score
            ):
                return
    finally:
        pygame.quit()


def parse_args():
    parser = argparse.ArgumentParser(description="Fallen Asteroids")
    parser.add_argument("--asteroids", type=int, default=NIVELES_JUEGO[1])
    parser.add_argument(
        "--max-active",
        type=int,
        default=DEFAULT_MAX_ACTIVE,
        help="máximo de asteroides simultáneos en pantalla",
    )
    parser.add_argument("--mode", choices=("parallel", "sequential"), default="parallel")
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def main():
    args = parse_args()
    # El Pool se crea ANTES de pygame.init() (dentro de app): evita problemas
    # al crear procesos con la librería gráfica ya inicializada. Se reutiliza
    # en todas las partidas y se cierra al salir.
    with create_pool(args.workers) as pool:
        app(args, pool)


if __name__ == "__main__":  # imprescindible en Windows (spawn)
    main()
