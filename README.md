# simulador-enjambre-paralelo
Simulador 2D paralelo con programación funcional

## Pruebas

    pip install -r requirements.txt pytest
    python -m pytest -v

Ejecutar siempre desde la raíz del proyecto.

## Benchmark

    python benchmark.py
    python benchmark.py --frames 100 --repeats 7 --workers 4

## Evidencia de paralelismo y rendimiento

La tabla obligatoria (1,000 / 3,000 / 5,000 entidades, Secuencial 1 núcleo vs Paralelo N núcleos, en FPS)
se obtiene de dos formas:

- **Dentro del juego:** en el menú pulsa **[B]**. Mide ambas versiones, muestra la tabla en pantalla junto
  con los datos técnicos (núcleos detectados, workers activos, estrategia de partición y reparto real de
  bloques) y guarda el informe en `resultados_benchmark.txt`.
- **Por consola (más preciso):** `python benchmark.py --frames 100 --repeats 7 --workers 4`

FPS = 1000 / ms por frame de simulación (sin render). **Estrategia de partición:** descomposición de datos
por bloques contiguos (`split_chunks` en `core/parallel.py`): un bloque por worker, tamaños que difieren
como máximo en 1, `pool.starmap` bloqueante como barrera y `consolidate` para unir los resultados en orden.

## Jugar

    python main.py
    python main.py --asteroids 5000 --mode sequential

Flujo: menú -> partida -> game over -> menú.
Controles: izquierda/derecha rotan, arriba acelera, espacio dispara, ESC vuelve al menú.

Reglas: los meteoritos esperan en una cola y entran por los bordes, con un **máximo de 15 a la
vez en pantalla** (`DEFAULT_MAX_ACTIVE` en `core/state.py`). Cada vez que uno sale de pantalla o es
destruido, entra el siguiente de la cola, así la densidad es constante y la dificultad del nivel
depende solo del total de meteoritos (niveles de 1000 / 3000 / 5000 en `config.NIVELES_JUEGO`). Los
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
