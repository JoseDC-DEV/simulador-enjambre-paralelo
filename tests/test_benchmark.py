from benchmark import Result, format_table, table_lines, technical_lines
from config import ENTIDADES_PRUEBA, NUCLEOS_CPU
from core.parallel import PARTITION_STRATEGY, describe_partition


def make_result(n, seq_ms, par_ms):
    return Result(n=n, sequential_ms=seq_ms, parallel_ms=par_ms, pickle_ms=1.0, identical=True)


def test_result_fps_and_speedup():
    r = make_result(1000, seq_ms=20.0, par_ms=10.0)

    assert r.sequential_fps == 50.0
    assert r.parallel_fps == 100.0
    assert r.speedup == 2.0


def test_table_has_one_row_per_load_with_fps():
    results = tuple(make_result(n, 20.0, 10.0) for n in ENTIDADES_PRUEBA)
    lines = table_lines(results, workers=3, frames=30, repeats=3)

    assert any("1,000 entidades" in l and "50.0 FPS" in l and "100.0 FPS" in l for l in lines)
    assert any("3,000 entidades" in l for l in lines)
    assert any("5,000 entidades" in l for l in lines)
    assert any("Paralelo (3 workers)" in l for l in lines)


def test_technical_lines_expose_cores_workers_and_strategy():
    text = "\n".join(technical_lines(workers=3))

    assert f"Núcleos totales detectados: {NUCLEOS_CPU}" in text
    assert "Workers (procesos concurrentes) configurados: 3" in text
    assert PARTITION_STRATEGY[0] in text
    assert "5000 entidades -> 3 bloques de 1666-1667" in text


def test_format_table_includes_table_and_technical_data():
    results = tuple(make_result(n, 20.0, 10.0) for n in ENTIDADES_PRUEBA)
    report = format_table(results, workers=2, frames=30, repeats=3)

    assert "RENDIMIENTO" in report and "DATOS TÉCNICOS" in report


def test_describe_partition():
    assert describe_partition(1000, 4) == "1000 entidades -> 4 bloques de 250"
    assert describe_partition(10, 3) == "10 entidades -> 3 bloques de 3-4"
    assert describe_partition(0, 3) == "sin entidades"
