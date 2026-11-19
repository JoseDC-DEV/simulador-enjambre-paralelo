import multiprocessing

# Configuración global del simulador
ANCHO_PANTALLA = 1200
ALTO_PANTALLA = 800
FPS_OBJETIVO = 60

# Configuración de entidades para el benchmark
ENTIDADES_PRUEBA = [1000, 3000, 5000]

# Configuración de paralelismo
NUCLEOS_CPU = multiprocessing.cpu_count()
WORKERS = max(1, NUCLEOS_CPU - 1) # Dejamos 1 núcleo libre para el sistema
