# Simulador Enjambre Paralelo — Fallen Asteroids

Simulador 2D desarrollado en Python que combina **programación funcional, inmutabilidad de datos y computación paralela** mediante `multiprocessing`.

El proyecto implementa un juego basado en asteroides donde se comparan dos estrategias de ejecución para actualizar las entidades de la simulación:

- **Modo secuencial:** procesa los asteroides en un único flujo de ejecución.
- **Modo paralelo:** distribuye el procesamiento de los asteroides entre varios procesos trabajadores (*workers*).

El objetivo es estudiar cómo la programación funcional facilita la distribución del trabajo y evaluar experimentalmente el rendimiento de ambas implementaciones.

---

## 1. Requisitos e instalación

Se necesita Python y las dependencias declaradas en `requirements.txt`.

Desde la raíz del proyecto, ejecutar:

```bash
python -m pip install -r requirements.txt
```

Las dependencias incluyen:

- `pygame-ce`: interfaz gráfica y ejecución del simulador.
- `pytest`: ejecución de las pruebas automatizadas.

**Importante:** todos los comandos deben ejecutarse desde la raíz del proyecto.

## 2. Pruebas automatizadas

El proyecto incluye pruebas para verificar el comportamiento de las entidades, el estado de la partida, las transformaciones funcionales, las colisiones, la ejecución paralela, las oleadas, el menú y el renderizado.

Para ejecutar todas las pruebas:

```bash
python -m pytest -v
```

La opción `-v` permite visualizar individualmente los resultados de cada prueba.

## 3. Arquitectura del proyecto

La implementación está organizada en módulos que separan la lógica de simulación, el procesamiento paralelo y la presentación gráfica.

| Directorio / archivo | Responsabilidad |
|---|---|
| `core/entities.py` | Definición de las entidades del juego mediante estructuras inmutables. |
| `core/state.py` | Representación inmutable del estado completo de la partida (`GameState`). |
| `core/transformations.py` | Transformaciones funcionales para actualizar posiciones, proyectiles y estados. |
| `core/collisions.py` | Movimiento de asteroides y comprobación de colisiones. |
| `core/waves.py` | Administración de la cola de asteroides y su entrada progresiva en pantalla. |
| `core/simulation.py` | Actualización secuencial y ciclo de simulación. |
| `core/parallel.py` | Distribución del procesamiento mediante `multiprocessing`. |
| `render/` | Interfaz gráfica, menú y representación visual del simulador. |
| `benchmark.py` | Comparación experimental entre las versiones secuencial y paralela. |
| `config.py` | Configuración de pantalla, niveles y cantidad de trabajadores. |
| `main.py` | Punto de entrada y coordinación general del juego. |
| `tests/` | Pruebas automatizadas de los componentes del proyecto. |

### Principios de implementación

**Programación funcional e inmutabilidad**

Las entidades y el estado de la partida utilizan estructuras inmutables. Las funciones de transformación reciben los datos necesarios y generan nuevas estructuras, evitando modificar directamente los objetos originales.

**Separación de responsabilidades**

El núcleo de simulación se encuentra separado de la interfaz gráfica. Esto permite ejecutar y evaluar la lógica de actualización sin incluir el coste del renderizado.

**Procesamiento paralelo**

El módulo `core/parallel.py` utiliza `multiprocessing.Pool` para distribuir el procesamiento de los asteroides entre varios procesos independientes.

---

## 4. Ejecución del juego

Para iniciar el simulador:

```bash
python main.py
```

Por defecto, el juego utiliza el modo paralelo, el nivel intermedio de 3000 asteroides y un máximo de 35 asteroides simultáneos en pantalla.

También se puede seleccionar explícitamente el nivel y el modo de ejecución.

**Ejemplo: modo secuencial**

```bash
python main.py --asteroids 5000 --mode sequential
```

**Ejemplo: modo paralelo**

```bash
python main.py --asteroids 5000 --mode parallel
```

**Parámetros disponibles**

| Parámetro | Descripción | Valor predeterminado |
|---|---|---|
| `--asteroids` | Cantidad total de asteroides del nivel. | 3000 |
| `--max-active` | Máximo de asteroides simultáneos en pantalla. | 35 |
| `--mode` | Modo de ejecución: `parallel` o `sequential`. | `parallel` |
| `--workers` | Cantidad de procesos trabajadores. | Núcleos detectados menos uno, mínimo 1 |
| `--seed` | Semilla para la generación inicial. | 0 |

Ejemplo de configuración personalizada:

```bash
python main.py --asteroids 5000 --max-active 1000 --mode parallel --workers 3 --seed 42
```

### Controles

| Tecla | Acción |
|---|---|
| Flecha izquierda | Rotar la nave hacia la izquierda. |
| Flecha derecha | Rotar la nave hacia la derecha. |
| Flecha arriba | Acelerar la nave. |
| Espacio | Disparar proyectiles. |
| ESC | Regresar al menú o salir de la partida actual. |
| ENTER | Confirmar la selección del menú. |
| B | Ejecutar el benchmark desde el menú. |

Flujo general: menú principal → partida → victoria o game over → menú principal.

---

## 5. Mecánicas y reglas del simulador

El juego utiliza una cola de asteroides para administrar la cantidad total de entidades que deben aparecer durante una partida.

**Entrada progresiva de asteroides**

Todos los asteroides se generan inicialmente y permanecen en una cola FIFO hasta que existen espacios disponibles en pantalla.

El límite predeterminado es de **35 asteroides simultáneos**, definido mediante `DEFAULT_MAX_ACTIVE` en `core/state.py`.

Cada vez que un asteroide es destruido o sale de los límites de la pantalla, queda disponible un espacio para introducir el siguiente elemento de la cola.

Esto permite mantener una cantidad controlada de entidades activas, independientemente del tamaño total del nivel.

**Comportamiento de los asteroides**

- Los asteroides ingresan por los bordes de la pantalla.
- Uno de cada diez asteroides nace con una trayectoria dirigida hacia la nave.
- No se permite su aparición a menos de 150 píxeles de la nave. Si no se cumple esta condición, su entrada se aplaza.
- Los asteroides desaparecen cuando salen de los límites de la pantalla; no reaparecen por el borde contrario.
- La nave, en cambio, sí utiliza un comportamiento de envoltura de pantalla (*screen wrapping*).

**Proyectiles y colisiones**

- Los proyectiles destruyen cualquier asteroide que toquen.
- Después de impactar, los proyectiles continúan su trayectoria hasta que expira su tiempo de vida.
- Si un asteroide colisiona con la nave, la partida termina.

**Condición de victoria**

El jugador gana cuando se han liberado todos los asteroides de la cola y no quedan asteroides activos en pantalla.

### Niveles disponibles

Los niveles se encuentran definidos en `config.NIVELES_JUEGO`.

| Nivel | Cantidad total de asteroides |
|---|---:|
| 1 | 1000 |
| 2 | 3000 |
| 3 | 5000 |

La dificultad de cada nivel depende de la cantidad total de asteroides que deben procesarse.

---

## 6. Arquitectura del procesamiento paralelo

El procesamiento paralelo se implementa en `core/parallel.py` mediante `multiprocessing.Pool`.

La distribución del trabajo sigue tres etapas:

**1. Segmentación de datos**

La función `split_chunks` divide la tupla de asteroides en bloques contiguos y equilibrados.

Cada bloque se asigna a un proceso trabajador. Los tamaños de los bloques difieren como máximo en una entidad.

**2. Ejecución concurrente**

Los bloques se envían mediante `pool.starmap` para ejecutar `process_asteroids` en los procesos trabajadores.

Cada proceso actualiza las posiciones de los asteroides y comprueba sus colisiones utilizando los datos recibidos.

El `Pool` es persistente y se reutiliza durante los distintos frames de la simulación.

**3. Sincronización y consolidación**

La operación `pool.starmap` es bloqueante: el proceso principal espera a que todos los trabajadores terminen.

Posteriormente, `consolidate` reúne los asteroides supervivientes, combina los indicadores de colisión y suma los asteroides destruidos.

El resultado consolidado se utiliza para construir el siguiente `GameState`.

Los eventos del jugador, la nave, la cola de asteroides y la construcción del siguiente estado permanecen en el proceso principal.

La arquitectura utiliza datos inmutables y resultados independientes para evitar modificaciones concurrentes del estado compartido de la simulación.

---

## 7. Benchmark: comparación de rendimiento

El proyecto incluye `benchmark.py`, encargado de comparar el rendimiento de las implementaciones secuencial y paralela.

La evaluación utiliza tres cargas de trabajo:

- 1000 asteroides.
- 3000 asteroides.
- 5000 asteroides.

Para cada escenario se mide el tiempo de actualización de la simulación, sin incluir el renderizado gráfico.

### Ejecución desde consola

Ejecutar el benchmark con sus parámetros predeterminados:

```bash
python benchmark.py
```

Ejecutar con una configuración personalizada:

```bash
python benchmark.py --frames 100 --repeats 7 --workers 4
```

Parámetros disponibles:

| Parámetro | Descripción | Valor predeterminado |
|---|---|---:|
| `--frames` | Frames medidos en cada repetición. | 60 |
| `--repeats` | Cantidad de repeticiones de la medición. | 5 |
| `--warmup` | Frames de calentamiento descartados. | 5 |
| `--workers` | Cantidad de procesos paralelos. | `WORKERS` de `config.py` |

El benchmark utiliza el mismo estado inicial y la misma semilla para ambas implementaciones, con el propósito de comparar resultados equivalentes.

Además, utiliza la mediana de los tiempos por frame para reducir la influencia de variaciones puntuales durante las mediciones.

### Ejecución desde el juego

También es posible realizar la evaluación desde la interfaz gráfica:

1. Ejecutar `python main.py`.
2. Esperar a que aparezca el menú principal.
3. Pulsar la tecla **B**.
4. Esperar a que finalicen las mediciones.
5. Consultar la tabla comparativa y los datos técnicos en pantalla.

El sistema genera automáticamente el archivo:

```text
resultados_benchmark.txt
```

Este informe contiene los resultados de rendimiento, la información del entorno de ejecución, los procesos trabajadores y el reparto de las entidades entre los bloques.

Para regresar al menú se puede pulsar ENTER o ESC.

### Métricas utilizadas

**FPS de simulación**

Se calcula mediante la siguiente relación:

\[
FPS = \frac{1000}{ms\ por\ frame}
\]

Representa la cantidad de actualizaciones de simulación que pueden realizarse por segundo, sin considerar el renderizado.

**Speedup o aceleración**

Se calcula mediante:

\[
Speedup = \frac{Tiempo\ secuencial}{Tiempo\ paralelo}
\]

Interpretación:

- `Speedup > 1`: la versión paralela es más rápida.
- `Speedup = 1`: ambas versiones tienen el mismo tiempo de ejecución