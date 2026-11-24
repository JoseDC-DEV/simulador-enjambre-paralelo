"""Benchmark: actualización secuencial vs paralela de los asteroides.

Mide cuántos FPS de simulación (solo la actualización del estado, sin render)
alcanza cada versión con cada cantidad de asteroides de config.ENTIDADES_PRUEBA
(1000 / 3000 / 5000) e imprime la tabla Secuencial vs Paralelo junto con los
datos técnicos: núcleos detectados, workers y estrategia de partición.

Uso, desde la raíz del proyecto:
    python benchmark.py
    python benchmark.py --frames 100 --repeats 7 --workers 4
"""

import argparse
import pickle
import platform
import statistics
from dataclasses import dataclass
from functools import reduce
from time import perf_counter

from config import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    ENTIDADES_PRUEBA,
    FPS_OBJETIVO,
    NUCLEOS_CPU,
    WORKERS,
)
from core.parallel import (
    PARTITION_STRATEGY,
    create_pool,
    describe_partition,
    update_parallel,
)
from core.simulation import create_initial_state, update
from core.waves import release_all

DT = 1 / FPS_OBJETIVO  # paso fijo: la simulación no depende del reloj real
NO_EVENTS = frozenset()
SEED = 1  # mismo estado inicial para ambas versiones y en todas las corridas


@dataclass(frozen=True)
class Result:
    n: int
    sequential_ms: float  # mediana de ms por frame
    parallel_ms: float
    pickle_ms: float  # referencia del costo de comunicación
    identical: bool  # ¿ambas versiones terminan en el mismo GameState?

    @property
    def sequential_fps(self) -> float:
        return 1000 / self.sequential_ms

    @property
    def parallel_fps(self) -> float:
        return 1000 / self.parallel_ms

    @property
    def speedup(self) -> float:
        return self.sequential_ms / self.parallel_ms


# --- Medición ---

def time_frames(step, state, frames):
    """Aplica step (GameState -> GameState) `frames` veces y mide el tiempo."""
    start = perf_counter()
    final = reduce(lambda s, _: step(s), range(frames), state)
    return perf_counter() - start, final


def measure(step, state, frames, repeats, warmup):
    """Devuelve (mediana de ms/frame, estado final de la primera corrida)."""
    time_frames(step, state, warmup)  # calentamiento: se descarta
    runs = [time_frames(step, state, frames) for _ in range(repeats)]
    ms_per_frame = [seconds * 1000 / frames for seconds, _ in runs]
    return statistics.median(ms_per_frame), runs[0][1]


def measure_pickle_ms(items, repeats):
    """Costo de serializar y deserializar la tupla una vez (referencia)."""
    def once():
        start = perf_counter()
        pickle.loads(pickle.dumps(items))
        return (perf_counter() - start) * 1000

    return statistics.median([once() for _ in range(repeats)])


def benchmark_size(n, pool, workers, frames, repeats, warmup):
    # Peor caso: los n asteroides ya están en pantalla (lo que el juego alcanza al final).
    state = release_all(create_initial_state(n, ANCHO_PANTALLA, ALTO_PANTALLA, seed=SEED))

    def sequential(s):
        return update(s, NO_EVENTS, DT, ANCHO_PANTALLA, ALTO_PANTALLA)

    def parallel(s):
        return update_parallel(
            pool, s, NO_EVENTS, DT, ANCHO_PANTALLA, ALTO_PANTALLA, workers
        )

    seq_ms, seq_final = measure(sequential, state, frames, repeats, warmup)
    par_ms, par_final = measure(parallel, state, frames, repeats, warmup)
    return Result(
        n=n,
        sequential_ms=seq_ms,
        parallel_ms=par_ms,
        pickle_ms=measure_pickle_ms(state.asteroids, repeats),
        identical=seq_final == par_final,
    )


def run_benchmark(pool, workers, frames, repeats, warmup, sizes=ENTIDADES_PRUEBA):
    """Mide todas las cargas. Lo usan la línea de comandos y la pantalla del juego."""
    return tuple(
        benchmark_size(n, pool, workers, frames, repeats, warmup) for n in sizes
    )


# --- Presentación (líneas de texto: sirven para consola y para la pantalla del juego) ---

def technical_lines(workers, sizes=ENTIDADES_PRUEBA):
    """Datos técnicos a exponer: núcleos, workers y estrategia de partición."""
    return (
        "DATOS TÉCNICOS",
        f"Núcleos totales detectados: {NUCLEOS_CPU}",
        f"Workers (procesos concurrentes) configurados: {workers}",
        f"Sistema: {platform.system()} | Python {platform.python_version()}",
        "Estrategia de partición de entidades:",
        *(f"  {line}" for line in PARTITION_STRATEGY),
        "Reparto real con esta configuración:",
        *(f"  {describe_partition(n, workers)}" for n in sizes),
    )


def table_lines(results, workers, frames, repeats):
    """Tabla comparativa Secuencial (1 núcleo) vs Paralelo (N nucleos) en FPS."""
    header = (
        f"{'Cantidad de entidades':>21} | {'Secuencial (1 núcleo)':>21} | "
        f"{f'Paralelo ({workers} workers)':>21} | {'Aceleración':>11} | {'Idéntico':>8}"
    )
    rows = tuple(
        f"{f'{r.n:,} entidades':>21} | {f'{r.sequential_fps:,.1f} FPS':>21} | "
        f"{f'{r.parallel_fps:,.1f} FPS':>21} | {f'{r.speedup:.2f}x':>11} | "
        f"{'sí' if r.identical else 'NO':>8}"
        for r in results
    )
    notes = (
        f"{frames} frames por corrida, mediana de {repeats} corridas.",
        "FPS = 1000 / ms por frame de simulación (sin render).",
        f"Objetivo: {FPS_OBJETIVO} FPS. Aceleración < 1.00x: el paralelo fue más lento.",
    )
    return ("RENDIMIENTO (FPS de simulación)", header, "-" * len(header), *rows, "", *notes)


def format_table(results, workers, frames, repeats):
    return "\n".join(
        [*table_lines(results, workers, frames, repeats), "", *technical_lines(workers)]
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--workers", type=int, default=WORKERS)
    return parser.parse_args()


def main():
    args = parse_args()
    # Un único Pool persistente para todas las mediciones.
    with create_pool(args.workers) as pool:
        results = run_benchmark(
            pool, args.workers, args.frames, args.repeats, args.warmup
        )
    print(format_table(results, args.workers, args.frames, args.repeats))


if __name__ == "__main__":  # imprescindible en Windows (spawn)
    main()
