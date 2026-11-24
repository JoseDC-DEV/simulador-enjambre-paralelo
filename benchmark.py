"""Benchmark: actualización secuencial vs paralela de los asteroides.

Mide cuántos milisegundos tarda un frame de simulación (solo la actualización
del estado, sin render) con cada versión y cada cantidad de asteroides de
config.ENTIDADES_PRUEBA.

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
from core.parallel import create_pool, update_parallel
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


# --- Presentación ---

def format_table(results, workers, frames, repeats):
    header = (
        f"{'Asteroides':>10} | {'Secuencial':>11} | {'Paralelo':>10} | "
        f"{'Aceleración':>11} | {'Pickle ref.':>11} | {'¿Idéntico?':>10}"
    )
    rows = [
        f"{r.n:>10} | {r.sequential_ms:>8.2f} ms | {r.parallel_ms:>7.2f} ms | "
        f"{r.sequential_ms / r.parallel_ms:>10.2f}x | {r.pickle_ms:>8.2f} ms | "
        f"{'sí' if r.identical else 'NO':>10}"
        for r in results
    ]
    info = [
        f"Python {platform.python_version()} | {platform.system()} | "
        f"núcleos: {NUCLEOS_CPU} | workers: {workers}",
        f"{frames} frames por corrida, mediana de {repeats} corridas (ms por frame).",
        f"Presupuesto por frame a {FPS_OBJETIVO} FPS: {1000 / FPS_OBJETIVO:.2f} ms "
        "(solo cubre la actualización; el render se suma).",
        "Aceleración < 1.00x significa que la versión paralela fue más lenta.",
    ]
    return "\n".join([*info, "", header, "-" * len(header), *rows])


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
        results = [
            benchmark_size(
                n, pool, args.workers, args.frames, args.repeats, args.warmup
            )
            for n in ENTIDADES_PRUEBA
        ]
    print(format_table(results, args.workers, args.frames, args.repeats))


if __name__ == "__main__":  # imprescindible en Windows (spawn)
    main()
