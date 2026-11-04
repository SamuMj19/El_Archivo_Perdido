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

 
# ==============================================================================
# 3. NÚCLEO COMÚN: VIDA, REINTENTOS, PREGUNTAS Y GUARDADO
# ==============================================================================
 
def penalizar(jugador: dict) -> bool:
    """
    Ejecuta el nodo «Vida -= 1» y la decisión «Vida > 0» del diagrama, usando
    actualizar_vida_jugador() de estructura.py.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si el jugador conserva vida (puede reintentar); False si la agotó.
    """
    sigue_con_vida = actualizar_vida_jugador(jugador, -1)
    print(f"  Fallaste: vida -= 1. Vida restante: {jugador['vida']}")
    if not sigue_con_vida:
        print("  Te quedaste sin vida.")
    return sigue_con_vida
 
 
def superar_con_reintentos(jugador: dict, intento) -> bool:
    """
    Implementa el bucle del diagrama «¿Reto cumplido? / ¿Respuesta correcta? -> No ->
    Vida -= 1 -> Vida > 0 -> reintentar»: repite el intento hasta que se supere o se
    agote la vida.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
        intento (callable): Función sin argumentos que ejecuta un intento y retorna
                            True si fue exitoso o False si falló.
 
    Retorna:
        bool: True si el intento se superó; False si el jugador se quedó sin vida.
    """
    while True:
        if intento():
            return True
        if not penalizar(jugador):
            return False
 
 
def hacer_pregunta(pregunta: dict) -> bool:
    """
    Formula una pregunta conceptual de opción múltiple (nodo «Iniciar pregunta
    conceptual»). Las opciones se barajan en cada intento para no memorizar la letra.
 
    Parámetros:
        pregunta (dict): Diccionario con 'enunciado', 'opciones' (la posición 0 es la
                         correcta) y 'explicacion'.
 
    Retorna:
        bool: True si el jugador eligió la opción correcta; False en caso contrario.
    """
    opciones = list(pregunta["opciones"])
    correcta = opciones[0]
    random.shuffle(opciones)
    letras = "ABCD"
 
    print()
    print(f"  PREGUNTA CONCEPTUAL: {pregunta['enunciado']}")
    for letra, opcion in zip(letras, opciones):
        print(f"    {letra}) {opcion}")
 
    while True:
        respuesta = leer_texto("  Tu respuesta (A-D): ").strip().upper()
        if len(respuesta) == 1 and respuesta in letras[:len(opciones)]:
            elegida = opciones[letras.index(respuesta)]
            break
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            elegida = opciones[int(respuesta) - 1]
            break
        print("  Entrada inválida: responde con una letra de la A a la D.")
 
    if elegida == correcta:
        print(f"  ¡Correcto! {pregunta['explicacion']}")
        return True
    print("  Respuesta incorrecta.")
    return False
 
 
def guardar_con_aviso(jugador: dict) -> bool:
    """
    Guarda la partida con guardar_partida() de persistencia.py. Si falla, informa el
    motivo y el juego continúa en memoria sin interrumpirse.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se guardó; False si hubo un error (ya informado al jugador).
    """
    exito, mensaje = guardar_partida(jugador)
    if exito:
        print("  Progreso guardado.")
    else:
        print(f"  Aviso: {mensaje}")
        print("  El juego continúa sin guardar este avance.")
    return exito
 
 
def desbloquear_proxima_sala(jugador: dict, sala_actual: int) -> None:
    """
    Ejecuta el nodo «Desbloquear próxima sala»: avanza el nivel del jugador y guarda
    la partida, que es el punto de reanudación al cargar.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
        sala_actual (int): Número de la sala que se acaba de superar (1 a 4).
 
    Retorna:
        None
    """
    jugador["nivel"] = sala_actual + 1
    print(f"\n  Sala superada. Se desbloquea: {NOMBRE_SALAS[jugador['nivel']]}.")
    guardar_con_aviso(jugador)
 
 
def ejecutar_sala_estandar(jugador: dict, numero_sala: int, reto) -> bool:
    """
    Recorre el ciclo común de las salas 1 a 4 según el diagrama: reto técnico ->
    añadir fragmento al inventario -> pregunta conceptual -> desbloquear próxima sala.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
        numero_sala (int): Número de la sala (1 a 4).
        reto (callable): Función reto(jugador) -> bool propia de la sala.
 
    Retorna:
        bool: True si la sala se superó; False si el jugador perdió la partida.
    """
    imprimir_titulo(f"SALA {numero_sala}: {NOMBRE_SALAS[numero_sala].upper()}  "
                    f"(vida: {jugador['vida']})")
    print(INTRODUCCIONES[numero_sala])
 
    if not reto(jugador):
        return False
 
    fragmento = crear_recompensa(numero_sala)
    insertar_fragmento_lista(jugador["inventario"], fragmento)
    print(f"\n  Reto cumplido. Fragmento recuperado: #{fragmento['codigo']} "
          f"«{fragmento['titulo']}» (valor {fragmento['valor']}).")
    if numero_sala == 4:
        generar_eco_duplicado(jugador)
 
    if not superar_con_reintentos(jugador, lambda: hacer_pregunta(PREGUNTAS[numero_sala])):
        return False
 
    desbloquear_proxima_sala(jugador, numero_sala)
    return True
 
 
def crear_recompensa(numero_sala: int) -> dict:
    """
    Construye con crear_fragmento() de estructura.py el fragmento que otorga una sala.
 
    Parámetros:
        numero_sala (int): Número de la sala (1 a 4).
 
    Retorna:
        dict: Fragmento con las claves 'codigo', 'titulo', 'sala' y 'valor'.
    """
    codigo, titulo, valor = RECOMPENSAS[numero_sala]
    return crear_fragmento(codigo, titulo, NOMBRE_SALAS[numero_sala], valor)
 
 
def generar_eco_duplicado(jugador: dict) -> None:
    """
    Simula la corrupción del índice: deja en el inventario una copia repetida del
    fragmento anterior, de modo que el Paso 2 de la Sala Central tenga un duplicado real
    que depurar con un conjunto.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador (inventario con al menos 2 fragmentos).
 
    Retorna:
        None
    """
    anteriores = jugador["inventario"][:-1]
    if not anteriores:
        return
    eco = dict(anteriores[-1])
    insertar_fragmento_lista(jugador["inventario"], eco)
    print(f"  El índice corrupto dejó una COPIA repetida del fragmento #{eco['codigo']} "
          "en tu inventario. La Sala Central se encargará de depurarla.")

    
# ==============================================================================
# 4. SALA 1: ESTANTERÍAS (LISTAS)
# ==============================================================================
 
def reto_estanterias(jugador: dict) -> bool:
    """
    Reto de la Sala 1: eliminar un registro dañado, insertar un fragmento nuevo en su
    posición correcta de una lista ordenada, buscar el fragmento de mayor valor y filtrar
    con una comprensión de listas. Cada paso se reintenta por separado (con -1 de vida
    por fallo) y solo modifica la lista cuando se resuelve bien.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se completaron los cuatro pasos; False si se agotó la vida.
    """
    inventario = [crear_fragmento(c, t, NOMBRE_SALAS[1], v) for c, t, v in INVENTARIO_PRELIMINAR]
    random.shuffle(inventario)
    codigo_extra, titulo_extra, valor_extra = FRAGMENTO_EXTRA_SALA_1
    extra = crear_fragmento(codigo_extra, titulo_extra, NOMBRE_SALAS[1], valor_extra)
 
    print("\n  Inventario preliminar (desordenado):")
    mostrar_fragmentos(inventario)
 
    # Paso A: eliminación con .remove()
    print("\n  Paso A (eliminación): un fragmento está dañado (valor 0.0).")
 
    def intento_eliminar() -> bool:
        """
        Pide el código del fragmento dañado y lo elimina con remove() solo si realmente está dañado.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        codigo = leer_entero("  Código del fragmento dañado que quieres eliminar: ")
        candidato = next((f for f in inventario if f["codigo"] == codigo), None)
        if candidato is None:
            print("  No hay ningún fragmento con ese código en la lista.")
            return False
        if candidato["valor"] > 0:
            print("  Ese fragmento está sano: no se elimina.")
            return False
        eliminar_fragmento_lista(inventario, codigo)
        print(f"  Fragmento #{codigo} eliminado con remove().")
        return True
 
    if not superar_con_reintentos(jugador, intento_eliminar):
        return False
 
    # Paso B: ordenamiento con .sort() e inserción en la posición correcta
    ordenar_inventario_lista(inventario, "codigo")
    print("\n  Paso B (ordenamiento e inserción): la lista se ordenó por código con sort().")
    mostrar_fragmentos(inventario)
    print(f"  Llega un fragmento nuevo: #{extra['codigo']} «{extra['titulo']}».")
    print("  Insértalo en la posición que mantenga la lista ordenada por código.")
 
    def intento_insertar() -> bool:
        """
        Pide la posición de inserción y la acepta solo si la lista conserva el orden por código.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        posicion = leer_entero(f"  Posición de inserción (0 a {len(inventario)}): ",
                               0, len(inventario))
        prueba = list(inventario)
        insertar_fragmento_lista(prueba, extra, posicion)
        codigos = [f["codigo"] for f in prueba]
        if codigos != sorted(codigos):
            print("  Con esa posición la lista deja de estar ordenada.")
            return False
        insertar_fragmento_lista(inventario, extra, posicion)
        print(f"  Insertado en la posición {posicion} con insert().")
        return True
 
    if not superar_con_reintentos(jugador, intento_insertar):
        return False
 
    # Paso C: búsqueda del fragmento de mayor valor
    print("\n  Paso C (búsqueda): revisa la lista actual.")
    mostrar_fragmentos(inventario)
    mejor = max(inventario, key=lambda f: f["valor"])
 
    def intento_buscar() -> bool:
        """
        Pide el código del fragmento de mayor valor y lo compara con el resultado de la búsqueda.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        codigo = leer_entero("  ¿Qué código tiene el fragmento de MAYOR valor? ")
        if codigo != mejor["codigo"]:
            print("  Ese no es el fragmento de mayor valor.")
            return False
        print(f"  Correcto: #{mejor['codigo']} con valor {mejor['valor']}.")
        return True
 
    if not superar_con_reintentos(jugador, intento_buscar):
        return False
 
    # Paso D: filtrado con comprensión de listas
    print("\n  Paso D (comprensión de listas): se aplicará")
    print("      [f for f in inventario if f['valor'] >= umbral]")
    print(f"  Elige un umbral para que queden EXACTAMENTE {FRAGMENTOS_ESPERADOS_FILTRO} fragmentos.")
 
    def intento_filtrar() -> bool:
        """
        Pide un umbral y comprueba que el filtrado con comprensión de listas deje la cantidad exigida.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        umbral = leer_flotante("  Umbral de valor: ")
        filtrados = filtrar_fragmentos_por_valor(inventario, umbral)
        if len(filtrados) != FRAGMENTOS_ESPERADOS_FILTRO:
            print(f"  Con ese umbral quedan {len(filtrados)} fragmentos.")
            return False
        print(f"  Quedaron {len(filtrados)} fragmentos: "
              f"{[f['codigo'] for f in filtrados]}.")
        return True
 
    return superar_con_reintentos(jugador, intento_filtrar)
 
 
def sala_estanterias(jugador: dict) -> bool:
    """
    Sala 1 del diagrama: Sala de Estanterías (listas).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se superó la sala; False si el jugador perdió la partida.
    """
    return ejecutar_sala_estandar(jugador, 1, reto_estanterias)


# ==============================================================================
# 5. SALA 2: MAPAS (TUPLAS)
# ==============================================================================
 
def mostrar_mapa(ruta: list = None) -> None:
    """
    Dibuja el mapa de la biblioteca: I = inicio, M = meta, X = zona clausurada,
    * = casilla recorrida y . = casilla libre.
 
    Parámetros:
        ruta (list, opcional): Lista de tuplas (fila, columna) ya recorridas.
 
    Retorna:
        None
    """
    recorrido = set(ruta) if ruta else set()
    filas, columnas = DIMENSIONES_MAPA
    print("         " + " ".join(f"c{c}" for c in range(columnas)))
    for fila in range(filas):
        simbolos = []
        for columna in range(columnas):
            coordenada = (fila, columna)
            if coordenada == PUNTO_PARTIDA:
                simbolos.append("I")
            elif coordenada == PUNTO_META:
                simbolos.append("M")
            elif coordenada in ZONAS_CLAUSURADAS:
                simbolos.append("X")
            elif coordenada in recorrido:
                simbolos.append("*")
            else:
                simbolos.append(".")
        print(f"    f{fila}   " + "  ".join(simbolos))
 
 
def reto_mapas(jugador: dict) -> bool:
    """
    Reto de la Sala 2: demuestra que una tupla es inmutable y pide una ruta de movimientos
    que lleve del inicio a la meta sin pisar zonas clausuradas. La ruta se convierte en
    una lista de tuplas (fila, columna) y se valida recorriéndola con desempaquetado.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si la ruta fue válida y llegó a la meta; False si se agotó la vida.
    """
    coordenada = crear_coordenada(*PUNTO_PARTIDA)
    print(f"\n  Tu posición inicial es la tupla {coordenada}. Intento modificarla: coord[0] = 99")
    try:
        coordenada[0] = 99
    except TypeError as error:
        print(f"  -> TypeError: {error}. Las coordenadas fijas no se pueden alterar.")
 
    print("\n  Mapa (I = inicio, M = meta, X = zona clausurada):")
    mostrar_mapa()
    print("  Movimientos: N = arriba, S = abajo, E = derecha, O = izquierda.")
    print("  Ejemplo de entrada: SSEE")
 
    def intento_ruta() -> bool:
        """
        Pide una ruta, la convierte en tuplas (fila, columna) y la valida desempaquetando cada paso.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        movimientos = leer_movimientos("  Tu ruta: ")
        ruta = [crear_coordenada(*PUNTO_PARTIDA)]
        for letra in movimientos:
            delta_fila, delta_columna = MOVIMIENTOS[letra]
            fila, columna = ruta[-1]
            ruta.append(crear_coordenada(fila + delta_fila, columna + delta_columna))
 
        valida, registro = recorrer_y_validar_ruta_mapa(ruta, ZONAS_CLAUSURADAS, DIMENSIONES_MAPA)
        if not valida:
            fila, columna = registro[-1]["coordenada"]
            print(f"  En el paso {len(registro) - 1} llegaste a ({fila}, {columna}): "
                  "fuera del mapa o zona clausurada.")
            return False
        if ruta[-1] != PUNTO_META:
            fila, columna = ruta[-1]
            print(f"  Tu ruta termina en ({fila}, {columna}), pero la meta es {PUNTO_META}.")
            return False
        print("  Ruta válida. Recorrido:")
        mostrar_mapa(ruta)
        return True
 
    return superar_con_reintentos(jugador, intento_ruta)
 
 
def sala_mapas(jugador: dict) -> bool:
    """
    Sala 2 del diagrama: Sala de Mapas (tuplas).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se superó la sala; False si el jugador perdió la partida.
    """
    return ejecutar_sala_estandar(jugador, 2, reto_mapas)

 
# ==============================================================================
# 6. SALA 3: FICHAS (DICCIONARIOS)
# ==============================================================================
 
def reto_fichas(jugador: dict) -> bool:
    """
    Reto de la Sala 3: consultar atributos por clave, detectar una ficha con una clave
    ausente y reconocer un código inexistente, sin que el programa colapse (uso de
    .get() y de captura de KeyError).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se completaron los tres pasos; False si se agotó la vida.
    """
    catalogo = construir_catalogo_fichas([dict(ficha) for ficha in FICHAS_BASE])
    print("\n  Catálogo de fichas (código -> ficha):")
    for codigo, ficha in catalogo.items():
        print(f"    {codigo}: {ficha}")
 
    # Paso A: consulta por clave
    codigo_a = random.choice([c for c, f in catalogo.items() if "titulo" in f])
    print("\n  Paso A (consulta por clave): lee el catálogo.")
 
    def intento_valor() -> bool:
        """
        Pide el valor de una ficha y lo compara con el obtenido por consulta de clave.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        respuesta = leer_flotante(f"  ¿Cuál es el 'valor' de la ficha {codigo_a}? ")
        esperado = float(consultar_atributo_fragmento(catalogo[codigo_a], "valor"))
        if abs(respuesta - esperado) > 1e-9:
            print("  Ese no es el valor registrado en la ficha.")
            return False
        print("  Correcto: catalogo[codigo]['valor'] se resuelve en O(1).")
        return True
 
    if not superar_con_reintentos(jugador, intento_valor):
        return False
 
    # Paso B: clave ausente en una ficha
    print("\n  Paso B (clave ausente): una ficha no tiene la clave 'titulo'.")
 
    def intento_ficha_danada() -> bool:
        """
        Pide el código de la ficha sin la clave 'titulo' y demuestra .get() y KeyError.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        codigo = leer_entero("  Código de la ficha sin 'titulo': ")
        ficha = catalogo.get(codigo)
        if ficha is None:
            print("  Ese código no existe en el catálogo.")
            return False
        encontrado, resultado = consultar_ficha_con_excepcion(ficha, "titulo")
        if encontrado:
            print("  Esa ficha sí tiene título.")
            return False
        print(f"  Correcto. ficha.get('titulo', 'No registrado') -> "
              f"{consultar_atributo_fragmento(ficha, 'titulo')!r}")
        print(f"  Y con ficha['titulo'] se captura KeyError: {resultado}")
        return True
 
    if not superar_con_reintentos(jugador, intento_ficha_danada):
        return False
 
    # Paso C: código inexistente
    existentes = random.sample(list(catalogo), 2)
    inexistente = random.choice([c for c in range(900, 1000) if c not in catalogo])
    opciones = existentes + [inexistente]
    random.shuffle(opciones)
    print("\n  Paso C (código inexistente): uno de estos códigos NO está en el catálogo.")
    for numero, codigo in enumerate(opciones, start=1):
        print(f"    {numero}) {codigo}")
 
    def intento_inexistente() -> bool:
        """
        Pide cuál de tres códigos no existe en el catálogo y demuestra la consulta segura.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        eleccion = leer_entero("  ¿Cuál no existe? (1-3): ", 1, len(opciones))
        codigo = opciones[eleccion - 1]
        if codigo in catalogo:
            print("  Ese código sí existe en el catálogo.")
            return False
        titulo = consultar_atributo_fragmento(catalogo.get(codigo), "titulo")
        print(f"  Correcto. catalogo.get({codigo}) -> None; consultar su título da {titulo!r}.")
        return True
 
    return superar_con_reintentos(jugador, intento_inexistente)
 
 
def sala_fichas(jugador: dict) -> bool:
    """
    Sala 3 del diagrama: Sala de Fichas (diccionarios).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se superó la sala; False si el jugador perdió la partida.
    """
    return ejecutar_sala_estandar(jugador, 3, reto_fichas)

 
# ==============================================================================
# 7. SALA 4: SELLOS (CONJUNTOS)
# ==============================================================================
 
def reto_sellos(jugador: dict) -> bool:
    """
    Reto de la Sala 4: depurar lotes de sellos con conjuntos. El jugador cuenta los sellos
    distintos de un lote (unicidad), halla los sellos comunes a dos lotes (intersección)
    y autentica el sello maestro descartando los corruptos (diferencia).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se completaron los tres pasos; False si se agotó la vida.
    """
    analisis = validar_pistas_conjuntos(LOTE_SELLOS_A, LOTE_SELLOS_B, SELLOS_CORRUPTOS)
    print(f"\n  Lote A: {LOTE_SELLOS_A}")
    print(f"  Lote B: {LOTE_SELLOS_B}")
    print(f"  Sellos corruptos: {SELLOS_CORRUPTOS}")
 
    def intento_distintos() -> bool:
        """
        Pide la cantidad de sellos distintos del lote A (unicidad de un set).
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        respuesta = leer_entero("\n  Paso A: ¿cuántos sellos DISTINTOS hay en el lote A? ", 0)
        if respuesta != len(analisis["conjunto_a"]):
            print("  Recuerda: un conjunto elimina automáticamente los repetidos.")
            return False
        print(f"  Correcto: set(lote_a) = {sorted(analisis['conjunto_a'])}.")
        return True
 
    if not superar_con_reintentos(jugador, intento_distintos):
        return False
 
    def intento_interseccion() -> bool:
        """
        Pide los sellos comunes a ambos lotes y los compara con la intersección A & B.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        respuesta = leer_conjunto_enteros("\n  Paso B: ¿qué sellos aparecen en AMBOS lotes (A & B)? ")
        if respuesta != analisis["interseccion"]:
            print("  Esa no es la intersección de los dos lotes.")
            return False
        print(f"  Correcto: A & B = {sorted(analisis['interseccion'])}.")
        return True
 
    if not superar_con_reintentos(jugador, intento_interseccion):
        return False
 
    def intento_autenticar() -> bool:
        """
        Pide los sellos que quedan sin los corruptos y los compara con la diferencia de conjuntos.
 
        Parámetros:
            Ninguno.
 
        Retorna:
            bool: True si el intento fue exitoso; False si falló (cuesta 1 de vida).
        """
        respuesta = leer_conjunto_enteros(
            "\n  Paso C: quita los sellos corruptos de esa intersección. ¿Cuáles quedan? ")
        if respuesta != analisis["sello_autenticado"]:
            print("  Esa no es la diferencia (A & B) - corruptos.")
            return False
        print(f"  Correcto: sellos autenticados = {sorted(analisis['sello_autenticado'])}.")
        return True
 
    return superar_con_reintentos(jugador, intento_autenticar)
 
 
def sala_sellos(jugador: dict) -> bool:
    """
    Sala 4 del diagrama: Sala de Sellos (conjuntos).
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        bool: True si se superó la sala; False si el jugador perdió la partida.
    """
    return ejecutar_sala_estandar(jugador, 4, reto_sellos)
 
 
# ==============================================================================
# 8. SALA 5: CENTRAL («LA RECONSTRUCCIÓN DEL CATÁLOGO») Y CIERRE
# ==============================================================================
 
def calcular_puntuacion_final(fragmentos_validos: list, vida_restante: int) -> float:
    """
    Ejecuta el nodo «Calcular puntuación final»: suma el valor de los fragmentos válidos
    recuperados y bonifica cada intento (punto de vida) que le quedó al jugador.
 
    Parámetros:
        fragmentos_validos (list): Fragmentos únicos recuperados (diccionarios con 'valor').
        vida_restante (int): Vida con la que el jugador termina la partida.
 
    Retorna:
        float: Puntaje final redondeado a dos decimales.
    """
    suma_valores = sum(float(f["valor"]) for f in fragmentos_validos)
    return round(suma_valores + max(0, int(vida_restante)) * PUNTOS_POR_VIDA, 2)
 
 
def calcular_intentos(jugador: dict) -> int:
    """
    Ejecuta el nodo «Calcular intentos»: los intentos restantes equivalen a los puntos de
    vida que conserva el jugador al terminar.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        int: Intentos restantes (mayor o igual a 0).
    """
    return max(0, int(jugador["vida"]))
 
 
def obtener_fragmentos_para_reconstruccion(jugador: dict) -> list:
    """
    Paso 1 (Carga): guarda la partida y vuelve a leer los fragmentos desde el archivo con
    cargar_fragmentos_recolectados(). Si el archivo no está disponible, usa el inventario
    en memoria y lo avisa, para que la partida pueda continuar.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        list: Lista de diccionarios de fragmentos, con los códigos repetidos incluidos.
    """
    exito_guardado = guardar_con_aviso(jugador)
    if exito_guardado:
        exito, resultado = cargar_fragmentos_recolectados(jugador["nombre"])
        if exito:
            return resultado
        print(f"  Aviso: {resultado}")
    print("  Se usará el inventario en memoria.")
    return [dict(fragmento) for fragmento in jugador["inventario"]]
 
 
def consultar_codigo(arbol, fragmentos: list) -> None:
    """
    Paso 6 (Consulta): pide un código y muestra el fragmento hallado junto con el número
    de comparaciones del ABB frente a la búsqueda secuencial en la lista. Permite repetir.
 
    Parámetros:
        arbol (ArbolBinarioBusqueda): ABB construido en el Paso 4.
        fragmentos (list): Lista depurada sobre la que se hace la búsqueda secuencial.
 
    Retorna:
        None
    """
    while True:
        codigo = leer_entero("\n  Código numérico del fragmento a buscar: ")
        resultado = comparar_busqueda_abb_vs_lista(arbol, fragmentos, codigo)
        if resultado["encontrado"]:
            fragmento = resultado["fragmento"]
            estante, nivel = fragmento["ubicacion"]
            print(f"  Fragmento encontrado: #{fragmento['codigo']} «{fragmento['titulo']}» "
                  f"({fragmento['sala']}), valor {fragmento['valor']}, "
                  f"estante {estante}, nivel {nivel}.")
        else:
            print(f"  No existe ningún fragmento con el código {codigo}.")
        print(f"  Comparaciones en el ABB:   {resultado['comparaciones_abb']}")
        print(f"  Comparaciones en la lista: {resultado['comparaciones_lista']}")
        if not leer_booleano("  ¿Buscar otro código? (si/no): "):
            return
 
 
def mostrar_retroalimentacion(resumen: dict, puntaje: float, jugador: dict) -> None:
    """
    Ejecuta el nodo «Mostrar retroalimentación»: resume el desempeño, relaciona cada sala
    con su estructura y contrasta el ABB balanceado con el degenerado con datos reales
    de generar_experimento_comparativo().
 
    Parámetros:
        resumen (dict): Resultado de ejecutar_reconstruccion_catalogo().
        puntaje (float): Puntaje final calculado.
        jugador (dict): Diccionario con el estado del jugador.
 
    Retorna:
        None
    """
    total = len(resumen["fragmentos_depurados"])
    altura_minima = int(math.log2(total)) if total >= 1 else -1
    imprimir_titulo("RETROALIMENTACIÓN")
    print(f"  Explorador: {jugador['nombre']}  |  Fragmentos válidos: {total}  |  "
          f"Vida final: {jugador['vida']}  |  Puntaje: {puntaje:.2f}")
    print("\n  Qué estructura usaste en cada sala y por qué:")
    print("    Estanterías -> lista: ordenada, mutable, acceso por índice O(1).")
    print("    Mapas       -> tupla: inmutable y hashable, ideal para coordenadas fijas.")
    print("    Fichas      -> diccionario: consulta por clave O(1) amortizado.")
    print("    Sellos      -> conjunto: unicidad automática y operaciones |, & y -.")
    print("    Central     -> ABB: búsqueda O(log n) si está balanceado e inorden ordenado.")
    print(f"\n  Tu ABB tiene altura {resumen['altura_abb']} (la mínima posible con "
          f"{total} nodos es {altura_minima}).")
 
    print("\n  Comparación de comparaciones al buscar la última clave (peor caso):")
    print(f"    {'n':>5}  {'h balanc.':>9}  {'ABB bal.':>8}  {'h degener.':>10}  "
          f"{'ABB degen.':>10}  {'Lista':>6}")
    for fila in generar_experimento_comparativo():
        print(f"    {fila['tamano_n']:>5}  {fila['altura_abb_balanceado']:>9}  "
              f"{fila['comparaciones_abb_balanceado']:>8}  {fila['altura_abb_degenerado']:>10}  "
              f"{fila['comparaciones_abb_degenerado']:>10}  "
              f"{fila['comparaciones_lista_secuencial']:>6}")
    print("  Si los códigos se insertan ya ordenados, el ABB se degenera (h = n - 1) y "
          "buscar cuesta lo mismo que recorrer la lista.")
 
 
def sala_central(jugador: dict) -> bool:
    """
    Sala 5 del diagrama: Sala Central. Ejecuta de forma visible los seis pasos de «La
    Reconstrucción del Catálogo» (carga, depuración con set, ubicación con tuple,
    construcción del ABB, verificación inorden y consulta comparativa), responde la
    pregunta de cierre y finaliza con puntaje, persistencia, tabla y retroalimentación.
 
    Parámetros:
        jugador (dict): Diccionario con el estado del jugador (nivel 5, inventario cargado).
 
    Retorna:
        bool: True si se completó la partida; False si el jugador perdió o el índice no
              pasó la verificación inorden.
    """
    imprimir_titulo(f"SALA 5: SALA CENTRAL — LA RECONSTRUCCIÓN  (vida: {jugador['vida']})")
 
    # Paso 1: carga desde el archivo
    print("\n  PASO 1 — Carga: leyendo los fragmentos recolectados desde el archivo...")
    fragmentos = obtener_fragmentos_para_reconstruccion(jugador)
    if not fragmentos:
        print("  No hay fragmentos que reconstruir. La partida no puede continuar.")
        return False
    mostrar_fragmentos(fragmentos)
    pausar()
 
    # Pasos 2 a 5: los ejecuta estructura.py; aquí se muestra cada resultado en orden
    resumen = ejecutar_reconstruccion_catalogo(fragmentos)
    depurados = resumen["fragmentos_depurados"]
 
    print("\n  PASO 2 — Depuración: eliminando códigos repetidos con un conjunto (set)...")
    print(f"  Fragmentos cargados: {resumen['total_cargados']}  |  "
          f"duplicados descartados: {resumen['descartados']}  |  únicos: {len(depurados)}")
    pausar()
 
    print("\n  PASO 3 — Ubicación: asignando una tupla (estante, nivel) a cada fragmento...")
    for fragmento in depurados:
        estante, nivel = fragmento["ubicacion"]
        print(f"    #{fragmento['codigo']:<4} «{fragmento['titulo']}» -> "
              f"(estante={estante}, nivel={nivel})")
    pausar()
 
    print("\n  PASO 4 — Construcción: insertando en el ABB usando 'codigo' como clave...")
    print(f"  Orden de inserción: {[f['codigo'] for f in depurados]}")
    print(f"  ABB construido: {resumen['arbol_abb'].total_nodos} nodos, "
          f"altura {resumen['altura_abb']}.")
    pausar()
 
    print("\n  PASO 5 — Verificación: recorrido inorden (izquierdo -> raíz -> derecho)...")
    codigos_inorden = [f["codigo"] for f in resumen["catalogo_inorden"]]
    print(f"  Inorden: {codigos_inorden}")
    if not resumen["orden_valido"]:
        print("  ERROR: la lista inorden NO está estrictamente ordenada. "
              "El índice reconstruido es inválido y la partida termina.")
        return False
    print("  Verificado: la lista está en orden ascendente estricto.")
    pausar()
 
    print("\n  PASO 6 — Consulta: busca un fragmento y compara el costo de ambas búsquedas.")
    print(f"  Códigos disponibles: {codigos_inorden}")
    consultar_codigo(resumen["arbol_abb"], depurados)
 
    if not superar_con_reintentos(jugador, lambda: hacer_pregunta(PREGUNTAS[5])):
        return False
 
    # Cierre: puntaje, intentos, persistencia, tabla y retroalimentación
    imprimir_titulo("CIERRE DE LA PARTIDA")
    puntaje = calcular_puntuacion_final(depurados, jugador["vida"])
    intentos = calcular_intentos(jugador)
    jugador["puntaje"] = puntaje
    jugador["inventario"] = depurados
    jugador["partida_activa"] = False
    print(f"  Puntaje final: {puntaje:.2f}  (fragmentos válidos: {len(depurados)}, "
          f"intentos restantes: {intentos})")
 
    exito, mensaje = guardar_resultado_final(jugador, len(depurados), intentos)
    print(f"  {mensaje}" if exito else f"  Aviso: {mensaje}")
 
    exito, tabla = cargar_tabla_puntajes(10)
    print("\n  TABLA DE PUNTAJES (mejores 10)")
    print(formatear_tabla_puntajes(tabla) if exito else f"  Aviso: {tabla}")
 
    mostrar_retroalimentacion(resumen, puntaje, jugador)
    return True
 
 
# ==============================================================================
# 9. VESTÍBULO: NUEVA PARTIDA O CARGAR PARTIDA
# ==============================================================================
 
def mostrar_bienvenida() -> None:
    """
    Muestra el título del juego y su contexto narrativo (nodo «Cargar Vestíbulo»).
 
    Parámetros:
        Ninguno.
 
    Retorna:
        None
    """
    imprimir_titulo("EL ARCHIVO PERDIDO")
    print("  Tras un fallo crítico en los sistemas de indexación de la Biblioteca Central")
    print("  Universitaria, el catálogo maestro quedó fragmentado y corrompido.")
    print("  Eres un Explorador de Datos: recorre cinco salas, recupera los fragmentos")
    print(f"  y reconstruye el índice. Empiezas con {VIDA_INICIAL} puntos de vida; "
          "cada fallo cuesta 1.")
 
 
def iniciar_nueva_partida() -> dict:
    """
    Rama «Sí» de «¿Iniciar nueva partida?»: pide el nombre, lo valida, registra al jugador
    en el archivo con registrar_nuevo_jugador() y retorna su estado inicial. Si el nombre
    ya existe pregunta si se sobrescribe. Si el archivo no se puede escribir, avisa y
    continúa con un jugador en memoria.
 
    Parámetros:
        Ninguno.
 
    Retorna:
        dict: Diccionario del jugador (vida 20, puntaje 0.0, nivel 1, inventario vacío).
    """
    while True:
        exito, resultado = validar_nombre_jugador(leer_texto("\n  Ingresa el nombre del nuevo jugador: "))
        if not exito:
            print(f"  {resultado}")
            continue
        nombre = resultado
 
        sobrescribir = False
        if existe_jugador(nombre):
            if not leer_booleano(f"  Ya existe una partida de '{nombre}'. ¿Sobrescribirla? (si/no): "):
                continue
            sobrescribir = True
 
        exito, resultado = registrar_nuevo_jugador(nombre, sobrescribir)
        if exito:
            print(f"  Bienvenido, {resultado['nombre']}.")
            return resultado
        print(f"  Aviso: {resultado}")
        print("  Jugarás sin guardado automático.")
        return crear_jugador(nombre, VIDA_INICIAL)
 
 
def cargar_partida_guardada():
    """
    Rama «No» de «¿Iniciar nueva partida?»: pide el nombre, verifica su validez y su
    existencia, sincroniza el Vestíbulo con la partida guardada y comprueba que la sala
    guardada sea válida. Cualquier problema se informa sin detener el juego.
 
    Parámetros:
        Ninguno.
 
    Retorna:
        dict: Jugador sincronizado, o None si no se pudo cargar (el llamador vuelve al menú).
    """
    exito, resultado = validar_nombre_jugador(leer_texto("\n  Ingresa el nombre del jugador: "))
    if not exito:
        print(f"  {resultado}")
        return None
    nombre = resultado
 
    # Decisión «¿El jugador existe?»: cargar_partida() la resuelve y, si falla, explica el
    # motivo real (jugador inexistente o archivo dañado) para no confundir ambos casos.
    exito, resultado = cargar_partida(nombre)
    if not exito:
        print(f"  {resultado}")
        return None
    jugador = resultado
 
    exito, resultado = obtener_sala_guardada(jugador)
    if not exito:
        print(f"  Error: {resultado}")
        return None
 
    if jugador["vida"] <= 0 or not jugador["partida_activa"]:
        print(f"  La partida de '{nombre}' ya terminó. Inicia una nueva partida con ese nombre.")
        return None
 
    print(f"  Partida cargada: {jugador['nombre']} | vida {jugador['vida']} | "
          f"fragmentos {len(jugador['inventario'])} | continúas en la "
          f"{NOMBRE_SALAS[resultado]}.")
    return jugador
 
 
def vestibulo() -> dict:
    """
    Fase I del juego (Vestíbulo): repite la pregunta «¿Iniciar nueva partida?» hasta que el
    jugador queda listo, ya sea con una partida nueva o con una cargada.
 
    Parámetros:
        Ninguno.
 
    Retorna:
        dict: Diccionario del jugador listo para entrar a la sala indicada en 'nivel'.
    """
    mostrar_bienvenida()
    while True:
        if leer_booleano("\n  ¿Iniciar nueva partida? (si = nueva, no = cargar guardada): "):
            return iniciar_nueva_partida()
        jugador = cargar_partida_guardada()
        if jugador is not None:
            return jugador
 
