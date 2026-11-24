# simulador-enjambre-paralelo
Simulador 2D paralelo con programación funcional

## Pruebas

    pip install -r requirements.txt pytest
    python -m pytest -v

Ejecutar siempre desde la raíz del proyecto.

## Benchmark

    python benchmark.py
    python benchmark.py --frames 100 --repeats 7 --workers 4

## Jugar

    python main.py
    python main.py --asteroids 5000 --mode sequential

Flujo: menú -> partida -> game over -> menú.
Controles: izquierda/derecha rotan, arriba acelera, espacio dispara, ESC vuelve al menú.

Reglas: los meteoritos esperan en una cola y entran por los bordes, con un **máximo de 15 a la
vez en pantalla** (`DEFAULT_MAX_ACTIVE` en `core/state.py`). Cada vez que uno sale de pantalla o es
destruido, entra el siguiente de la cola, así la densidad es constante y la dificultad del nivel
depende solo del total de meteoritos (niveles de 50 / 100 / 200 en `config.NIVELES_JUEGO`). Los
meteoritos no dan la vuelta por los bordes: al salir desaparecen (la nave sí da la vuelta). Uno de
cada 10 nace apuntando a la nave y ninguno aparece a menos de 150 px de ella. Un proyectil destruye
cualquier meteorito que toque y sigue su camino hasta caducar. Si un meteorito toca la nave, game
over. Victoria: agotar la cola y despejar la pantalla.

### Modo estrés (demo del paralelismo)

El límite de 15 mantiene el juego jugable, pero deja poco trabajo a los workers. Para ver el
paralelismo en vivo con miles de entidades a la vez:

    python main.py --asteroids 5000 --max-active 5000 --mode parallel
    python main.py --asteroids 5000 --max-active 5000 --mode sequential

La tabla formal Secuencial vs. Paralelo se obtiene con `python benchmark.py` (no usa la cola:
carga todos los meteoritos en pantalla desde el primer frame).
