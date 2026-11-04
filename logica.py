import math
import random
import sys
 
from estructura import (
    actualizar_vida_jugador,
    comparar_busqueda_abb_vs_lista,
    consultar_atributo_fragmento,
    consultar_ficha_con_excepcion,
    construir_catalogo_fichas,
    convertir_y_validar_tipo,
    crear_coordenada,
    crear_fragmento,
    crear_jugador,
    ejecutar_reconstruccion_catalogo,
    eliminar_fragmento_lista,
    filtrar_fragmentos_por_valor,
    generar_experimento_comparativo,
    insertar_fragmento_lista,
    ordenar_inventario_lista,
    recorrer_y_validar_ruta_mapa,
    validar_pistas_conjuntos,
)
from persistencia import (
    NUMERO_SALAS,
    cargar_fragmentos_recolectados,
    cargar_partida,
    cargar_tabla_puntajes,
    existe_jugador,
    formatear_tabla_puntajes,
    guardar_partida,
    guardar_resultado_final,
    obtener_sala_guardada,
    registrar_nuevo_jugador,
    validar_nombre_jugador,
)
 
 
# ==============================================================================
# 1. CONSTANTES Y DATOS DEL JUEGO
# ==============================================================================
 
VIDA_INICIAL = 20
PUNTOS_POR_VIDA = 5.0
ANCHO_PANTALLA = 74
 
NOMBRE_SALAS = {
    1: "Sala de Estanterías",
    2: "Sala de Mapas",
    3: "Sala de Fichas",
    4: "Sala de Sellos",
    5: "Sala Central",
}
 
# Fragmento que se obtiene al superar el reto de cada sala: (codigo, titulo, valor).
RECOMPENSAS = {
    1: (150, "Tratado de Listas Dinámicas", 10.0),
    2: (75, "Plano del Ala Norte", 12.5),
    3: (230, "Ficha Maestra de Autores", 15.0),
    4: (310, "Sello Maestro del Archivo", 20.0),
}
 
INTRODUCCIONES = {
    1: ("Las estanterías están desordenadas y algunos registros están dañados.\n"
        "Debes gestionar el inventario preliminar usando LISTAS."),
    2: ("El plano de la biblioteca tiene zonas clausuradas que no debes pisar.\n"
        "Cada posición es una TUPLA inmutable (fila, columna)."),
    3: ("Las fichas bibliográficas son DICCIONARIOS: algunas están incompletas\n"
        "y otras ni siquiera existen en el catálogo."),
    4: ("Llegaron lotes de sellos repetidos y algunos son falsos.\n"
        "Depúralos con CONJUNTOS (set) y autentica el sello maestro."),
}
 
# --- Sala 1: inventario preliminar (codigo, titulo, valor). Valor 0.0 = dañado ---
INVENTARIO_PRELIMINAR = [
    (305, "Manual de Recursividad", 8.0),
    (112, "Atlas de Bibliotecas", 6.5),
    (478, "Catálogo de Revistas", 9.5),
    (219, "Registro de Préstamos", 7.0),
    (391, "Fragmento ilegible", 0.0),
]
FRAGMENTO_EXTRA_SALA_1 = (260, "Boletín de Adquisiciones", 7.5)
FRAGMENTOS_ESPERADOS_FILTRO = 3
 
# --- Sala 2: mapa 5x5. I = inicio, M = meta, X = zona clausurada ---
DIMENSIONES_MAPA = (5, 5)
PUNTO_PARTIDA = (0, 0)
PUNTO_META = (4, 4)
ZONAS_CLAUSURADAS = {(0, 2), (1, 1), (1, 4), (2, 3), (3, 0), (3, 2)}
MOVIMIENTOS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}
MAXIMO_MOVIMIENTOS = 40
 
# --- Sala 3: fichas (la ficha 637 no tiene la clave 'titulo') ---
FICHAS_BASE = [
    {"codigo": 410, "titulo": "Historia de la Imprenta", "sala": "Sala de Fichas", "valor": 6.0},
    {"codigo": 522, "titulo": "Guía de Paleografía", "sala": "Sala de Fichas", "valor": 7.5},
    {"codigo": 637, "sala": "Sala de Fichas", "valor": 5.0},
    {"codigo": 748, "titulo": "Tratado de Clasificación Dewey", "sala": "Sala de Fichas", "valor": 9.0},
    {"codigo": 859, "titulo": "Memorias del Archivo", "sala": "Sala de Fichas", "valor": 8.0},
]
 
# --- Sala 4: lotes de sellos con repetidos y sellos corruptos ---
LOTE_SELLOS_A = [7, 3, 7, 12, 5, 3, 9]
LOTE_SELLOS_B = [5, 9, 14, 12, 14, 2]
SELLOS_CORRUPTOS = [9]
 
# --- Preguntas conceptuales: la opción en la posición 0 es siempre la correcta ---
PREGUNTAS = {
    1: {
        "enunciado": ("Sobre listas: ¿cuál afirmación es correcta?"),
        "opciones": [
            "sort() ordena la lista en el sitio, reverse() solo invierte el orden actual e "
            "index(x) devuelve la posición de la primera aparición de x; insert(0, v) cuesta "
            "O(n) porque desplaza todos los elementos, mientras append(v) es O(1) amortizado.",
            "sort() devuelve una lista nueva sin modificar la original, reverse() ordena de mayor "
            "a menor e index(x) elimina x; insert(0, v) y append(v) cuestan lo mismo.",
            "sort(), reverse() e index(x) hacen lo mismo con distinto nombre; insert(0, v) es "
            "más barato que append(v) porque no recorre la lista.",
            "index(x) ordena la lista según x; append(v) es más costoso que insert(0, v) porque "
            "debe recorrer toda la lista para llegar al final.",
        ],
        "explicacion": ("insert(0, v) obliga a mover cada elemento una posición (O(n)); append(v) "
                        "solo escribe al final (O(1) amortizado)."),
    },
    2: {
        "enunciado": ("¿Por qué se eligen tuplas en lugar de listas para representar coordenadas "
                      "como (fila, columna) o (estante, nivel)?"),
        "opciones": [
            "Porque son inmutables: nadie puede alterar una coordenada fija por error, y al ser "
            "hashables pueden guardarse en un set o usarse como clave de un diccionario.",
            "Porque ocupan siempre más memoria y por eso son más seguras.",
            "Porque las tuplas admiten append() y sort(), lo que facilita mover las coordenadas.",
            "Porque no se pueden desempaquetar, así la fila y la columna nunca se separan.",
        ],
        "explicacion": ("La inmutabilidad protege el mapa (coord[0] = 99 lanza TypeError) y hace "
                        "que la tupla sea hashable."),
    },
    3: {
        "enunciado": ("¿Qué estructura interna implementa un diccionario en Python y por qué "
                      "consultar por clave es O(1) amortizado frente al O(n) de una lista?"),
        "opciones": [
            "Una tabla hash: la función hash convierte la clave en una posición, así que no hay "
            "que recorrer los elementos; en una lista hay que comparar uno por uno.",
            "Un árbol binario de búsqueda: descarta la mitad de los elementos en cada paso, "
            "por eso siempre cuesta O(1).",
            "Una lista de pares ordenada alfabéticamente sobre la que se hace búsqueda secuencial.",
            "Una pila: la última clave insertada es la primera en consultarse.",
        ],
        "explicacion": ("Al ser una tabla hash, la clave se transforma en un índice directo; "
                        "la lista, en cambio, se recorre elemento por elemento."),
    },
    4: {
        "enunciado": ("¿Cómo evita Python que se agregue un elemento duplicado a un conjunto y "
                      "por qué un conjunto vacío se crea con set() y no con {}?"),
        "opciones": [
            "Usa una tabla hash: calcula el hash del elemento y, si ya hay uno igual en esa "
            "posición, no lo agrega; {} crea un diccionario vacío, por eso se usa set().",
            "Recorre toda la colección comparando uno a uno; {} crea un conjunto vacío, pero "
            "set() es más legible.",
            "Ordena los elementos al insertarlos y descarta los vecinos iguales; {} crea una "
            "lista vacía.",
            "Guarda un contador por elemento y lo incrementa; {} crea una tupla vacía.",
        ],
        "explicacion": ("Los conjuntos y los diccionarios comparten la sintaxis de llaves; "
                        "{} está reservado para el diccionario vacío."),
    },
    5: {
        "enunciado": ("¿Por qué el recorrido inorden de un ABB entrega las claves en orden "
                      "ascendente y qué ocurre con la altura h y el costo de búsqueda si los "
                      "códigos se insertan ya ordenados?"),
        "opciones": [
            "Porque el subárbol izquierdo tiene claves menores y el derecho mayores, y inorden "
            "visita izquierdo, raíz, derecho. Si se insertan ordenados el árbol se degenera en "
            "una lista: h = n - 1 y la búsqueda pasa de O(log n) a O(n).",
            "Porque inorden ordena los datos mientras recorre. Si se insertan ordenados el árbol "
            "queda perfectamente balanceado y la búsqueda sigue siendo O(log n).",
            "Porque la raíz siempre es la clave mayor. Si se insertan ordenados la altura "
            "disminuye a 1 y la búsqueda cuesta O(1).",
            "Porque inorden visita primero la raíz y luego las hojas. Si se insertan ordenados "
            "el árbol duplica su altura pero la búsqueda no cambia.",
        ],
        "explicacion": ("Con claves ya ordenadas cada inserción cae siempre al mismo lado: el "
                        "ABB se vuelve una cadena y buscar equivale a recorrer una lista."),
    },
}


# ==============================================================================
# 2. ENTRADA Y SALIDA DE CONSOLA (VALIDACIÓN DE ENTRADAS)
# ==============================================================================
 
class AbandonarPartida(Exception):
    """
    Señal interna que indica que el jugador cerró la entrada (Ctrl+C o Ctrl+D). Permite
    salir limpiamente desde cualquier punto del juego sin mostrar un traceback.
    """
 
 
def configurar_consola() -> None:
    """
    Evita que un terminal con codificación limitada detenga el juego al imprimir
    tildes o símbolos: los caracteres no representables se reemplazan en vez de fallar.
 
    Parámetros:
        Ninguno.
 
    Retorna:
        None
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
 
 
def imprimir_titulo(texto: str) -> None:
    """
    Imprime un encabezado enmarcado para separar visualmente las fases del juego.
 
    Parámetros:
        texto (str): Título que se mostrará centrado entre dos líneas.
 
    Retorna:
        None
    """
    print()
    print("=" * ANCHO_PANTALLA)
    print(texto.center(ANCHO_PANTALLA))
    print("=" * ANCHO_PANTALLA)
 
 
def leer_texto(mensaje: str) -> str:
    """
    Lee una línea con input(), convirtiendo el cierre de la entrada (Ctrl+C o Ctrl+D)
    en la excepción controlada AbandonarPartida.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador antes de leer.
 
    Retorna:
        str: Línea escrita por el jugador, sin el salto de línea final.
    """
    try:
        return input(mensaje)
    except (EOFError, KeyboardInterrupt):
        print()
        raise AbandonarPartida
 
 
def leer_entero(mensaje: str, minimo: int = None, maximo: int = None) -> int:
    """
    Pide un número entero y repite la pregunta hasta recibir uno válido. Usa
    convertir_y_validar_tipo() de estructura.py dentro de un bucle while, de modo que
    un texto donde se espera un número nunca detiene el juego.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador.
        minimo (int, opcional): Valor mínimo aceptado (inclusive).
        maximo (int, opcional): Valor máximo aceptado (inclusive).
 
    Retorna:
        int: Número entero válido dentro del rango indicado.
    """
    while True:
        exito, valor = convertir_y_validar_tipo(leer_texto(mensaje), int)
        if not exito:
            print("  Entrada inválida: escribe un número entero (por ejemplo, 42).")
            continue
        if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
            limite_inferior = "-infinito" if minimo is None else minimo
            limite_superior = "infinito" if maximo is None else maximo
            print(f"  El número debe estar entre {limite_inferior} y {limite_superior}.")
            continue
        return valor
 
 
def leer_flotante(mensaje: str) -> float:
    """
    Pide un número decimal finito y repite la pregunta hasta recibir uno válido. Se
    rechazan «nan» e «inf», que float() acepta pero no sirven como respuesta.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador.
 
    Retorna:
        float: Número decimal finito.
    """
    while True:
        exito, valor = convertir_y_validar_tipo(leer_texto(mensaje), float)
        if exito and math.isfinite(valor):
            return valor
        print("  Entrada inválida: escribe un número (por ejemplo, 7.5).")
 
 
def leer_booleano(mensaje: str) -> bool:
    """
    Pide una respuesta de tipo sí/no y repite la pregunta hasta recibir una válida.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador (por ejemplo, «... (si/no): »).
 
    Retorna:
        bool: True para sí, False para no.
    """
    while True:
        exito, valor = convertir_y_validar_tipo(leer_texto(mensaje), bool)
        if exito:
            return valor
        print("  Entrada inválida: responde «si» o «no».")
 
 
def leer_conjunto_enteros(mensaje: str) -> set:
    """
    Pide una lista de enteros separados por comas o espacios y la entrega como conjunto
    (los repetidos se eliminan solos). Repite la pregunta si algún elemento no es entero.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador.
 
    Retorna:
        set: Conjunto no vacío de enteros.
    """
    while True:
        fichas = leer_texto(mensaje).replace(",", " ").split()
        resultados = [convertir_y_validar_tipo(ficha, int) for ficha in fichas]
        if fichas and all(exito for exito, _ in resultados):
            return {valor for _, valor in resultados}
        print("  Entrada inválida: escribe números enteros separados por comas (ej. 3, 8, 12).")
 
 
def leer_movimientos(mensaje: str) -> list:
    """
    Pide una secuencia de movimientos N (arriba), S (abajo), E (derecha) y O (izquierda),
    con o sin separadores, y repite la pregunta si hay letras no válidas.
 
    Parámetros:
        mensaje (str): Texto que se muestra al jugador.
 
    Retorna:
        list: Lista de letras mayúsculas, cada una una clave de MOVIMIENTOS.
    """
    while True:
        texto = leer_texto(mensaje).upper()
        letras = [c for c in texto if not c.isspace() and c not in ",;-"]
        invalidas = sorted({c for c in letras if c not in MOVIMIENTOS})
        if not letras:
            print("  Escribe al menos un movimiento (N, S, E u O).")
        elif invalidas:
            print(f"  Movimientos no válidos: {' '.join(invalidas)}. Usa solo N, S, E u O.")
        elif len(letras) > MAXIMO_MOVIMIENTOS:
            print(f"  Demasiados movimientos: el máximo es {MAXIMO_MOVIMIENTOS}.")
        else:
            return letras
 
 
def pausar() -> None:
    """
    Detiene la ejecución hasta que el jugador presione Enter, para que cada paso de la
    Sala Central sea visible antes de continuar con el siguiente.
 
    Parámetros:
        Ninguno.
 
    Retorna:
        None
    """
    leer_texto("  (Enter para continuar) ")
 
 
def mostrar_fragmentos(fragmentos: list) -> None:
    """
    Imprime una lista de fragmentos como tabla (posición, código, título y valor).
 
    Parámetros:
        fragmentos (list): Lista de diccionarios de fragmentos.
 
    Retorna:
        None
    """
    if not fragmentos:
        print("  (sin fragmentos)")
        return
    print(f"  {'Pos':>3}  {'Código':>6}  {'Título':<32}  {'Valor':>6}")
    for posicion, fragmento in enumerate(fragmentos):
        print(f"  {posicion:>3}  {fragmento['codigo']:>6}  "
              f"{fragmento['titulo']:<32}  {fragmento['valor']:>6.1f}")
 