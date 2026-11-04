"""
«El Archivo Perdido».
Administra el guardado y la carga de partidas JSON y la tabla histórica de
puntajes, controlando los errores de lectura y escritura para que el juego
nunca se detenga por archivos falsos, dañados o sin permisos.

Conexión con «estructura.py»:
    - crear_jugador(): reconstruye el diccionario del jugador al cargar una partida.
    - crear_fragmento(): normaliza cada fragmento leído desde el archivo.
    - convertir_y_validar_tipo(): valida los campos de texto (nombre y filas del CSV).

Convención de retorno: toda función pública que pueda fallar retorna un par
(exito: bool, resultado). Si exito es True, 'resultado' es el dato solicitado; si es
False, 'resultado' es un mensaje (str) listo para mostrarse al jugador. Ninguna
función pública lanza excepciones por problemas de archivos.

Si se ejecuta directamente corre una demostración en una
carpeta temporal, sin modificar los archivos reales de la carpeta datos.
"""
import csv
import json
import math
import os
from datetime import datetime

from estructura import convertir_y_validar_tipo, crear_fragmento, crear_jugador


# ==============================================================================
# 1. CONFIGURACIÓN GENERAL Y UTILIDADES INTERNAS
# ==============================================================================

DIRECTORIO_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
RUTA_PARTIDAS = os.path.join(DIRECTORIO_DATOS, "partidas.json")
RUTA_PUNTAJES = os.path.join(DIRECTORIO_DATOS, "puntajes.csv")

NUMERO_SALAS = 5
LONGITUD_MAXIMA_NOMBRE = 30
CARACTERES_NOMBRE_EXTRA = " -_.'"

CLAVES_JUGADOR = ("nombre", "vida", "puntaje", "nivel", "partida_activa", "inventario")
CLAVES_FRAGMENTO = ("codigo", "titulo", "sala", "valor")
COLUMNAS_PUNTAJES = ("nombre", "puntaje", "fragmentos_validos", "intentos", "fecha")


def _es_entero(valor) -> bool:
    """
    Indica si un valor es un entero «real» de Python. Se excluye bool porque en
    Python True y False son subclases de int y no deben aceptarse como números.

    Parámetros:
        valor (Any): Valor que se desea comprobar.

    Retorna:
        bool: True si el valor es de tipo int y no es bool; False en caso contrario.
    """
    return isinstance(valor, int) and not isinstance(valor, bool)


def _es_numero_finito(valor) -> bool:
    """
    Indica si un valor es un número (int o float, nunca bool) finito, es decir,
    distinto de NaN e infinito, para que no rompa el ordenamiento de los puntajes.

    Parámetros:
        valor (Any): Valor que se desea comprobar.

    Retorna:
        bool: True si es un int o float finito; False en caso contrario.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return False
    try:
        return math.isfinite(valor)
    except OverflowError:
        return False


def _marca_de_tiempo() -> str:
    """
    Genera la fecha y hora actuales con el formato AAAA-MM-DD HH:MM:SS.

    Parámetros:
        Ninguno.

    Retorna:
        str: Marca de tiempo legible para registros y tabla de puntajes.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _clave_jugador(nombre_validado: str) -> str:
    """
    Genera la clave con la que se indexa a un jugador dentro del archivo de partidas.
    Se ignoran las mayúsculas para que «Ana» y «ana» correspondan al mismo jugador.

    Parámetros:
        nombre_validado (str): Nombre ya normalizado por validar_nombre_jugador().

    Retorna:
        str: Clave en minúsculas (casefold) usada como clave del diccionario de partidas.
    """
    return nombre_validado.casefold()


def _describir_error_archivo(error: OSError, ruta: str) -> str:
    """
    Traduce una excepción de entrada/salida en un mensaje claro para el jugador.

    Parámetros:
        error (OSError): Excepción capturada al abrir, leer o escribir un archivo.
        ruta (str): Ruta del archivo involucrado.

    Retorna:
        str: Mensaje descriptivo del problema.
    """
    if isinstance(error, FileNotFoundError):
        return f"No se encontró el archivo o la carpeta: {ruta}"
    if isinstance(error, PermissionError):
        return f"No hay permisos para leer o escribir en: {ruta}"
    if isinstance(error, IsADirectoryError):
        return f"La ruta es una carpeta, no un archivo: {ruta}"
    detalle = error.strerror or str(error)
    return f"Error de lectura o escritura en {ruta}: {detalle}"


def _leer_partidas(ruta: str) -> tuple:
    """
    Lee el archivo JSON de partidas, un diccionario {clave_jugador: registro}.
    Un archivo inexistente o vacío se interpreta como «todavía no hay partidas».

    Parámetros:
        ruta (str): Ruta del archivo JSON de partidas.

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es el
               diccionario de partidas (vacío si no hay); si es False, es un mensaje de error.
    """
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
    except FileNotFoundError:
        return True, {}
    except UnicodeDecodeError:
        return False, (f"El archivo de partidas está dañado (codificación inválida): {ruta}. "
                       "Repáralo o elimínalo para continuar.")
    except OSError as error:
        return False, _describir_error_archivo(error, ruta)

    if not contenido.strip():
        return True, {}

    try:
        partidas = json.loads(contenido)
    except (json.JSONDecodeError, RecursionError):
        return False, (f"El archivo de partidas está dañado (JSON inválido): {ruta}. "
                       "Repáralo o elimínalo para continuar.")

    if not isinstance(partidas, dict):
        return False, (f"El archivo de partidas tiene un formato inesperado: {ruta}. "
                       "Repáralo o elimínalo para continuar.")
    return True, partidas


def _escribir_json_atomico(ruta: str, datos: dict) -> tuple:
    """
    Escribe un diccionario como JSON de forma segura: primero lo guarda en un archivo
    temporal y, solo si la escritura terminó bien, lo renombra sobre el destino con
    os.replace(). Así, un fallo a mitad de la escritura nunca deja el archivo real corrupto.

    Parámetros:
        ruta (str): Ruta del archivo JSON de destino (se crea la carpeta si no existe).
        datos (dict): Diccionario serializable a JSON que se desea guardar.

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es la ruta
               escrita; si es False, es un mensaje de error.
    """
    ruta_temporal = ruta + ".tmp"
    try:
        directorio = os.path.dirname(ruta)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=4, allow_nan=False)
        os.replace(ruta_temporal, ruta)
        return True, ruta
    except OSError as error:
        mensaje = _describir_error_archivo(error, ruta)
    except (TypeError, ValueError) as error:
        mensaje = f"No se pudieron convertir los datos a JSON: {error}"

    # La escritura falló: se intenta eliminar el archivo temporal incompleto.
    try:
        os.remove(ruta_temporal)
    except OSError:
        pass
    return False, mensaje


# ==============================================================================
# 2. VESTÍBULO: VALIDACIÓN DEL NOMBRE Y REGISTRO DE JUGADORES
# ==============================================================================

def validar_nombre_jugador(nombre: str) -> tuple:
    """
    Ejecuta el nodo «Verificar validez del nombre» del diagrama de flujo. Comprueba que
    el nombre sea texto no vacío (reutilizando convertir_y_validar_tipo de estructura.py),
    normaliza los espacios y aplica las reglas de longitud y de caracteres permitidos.

    Parámetros:
        nombre (str): Texto ingresado por el usuario (proveniente de input()).

    Retorna:
        tuple: Par (exito: bool, resultado: str). Si exito es True, 'resultado' es el
               nombre normalizado; si es False, es el mensaje que explica el rechazo.
    """
    if not isinstance(nombre, str):
        return False, "El nombre debe ser un texto."

    exito, texto = convertir_y_validar_tipo(nombre, str)
    if not exito:
        return False, "El nombre no puede estar vacío."

    texto = " ".join(texto.split())
    if len(texto) > LONGITUD_MAXIMA_NOMBRE:
        return False, f"El nombre no puede superar los {LONGITUD_MAXIMA_NOMBRE} caracteres."
    if not texto[0].isalnum():
        return False, "El nombre debe comenzar con una letra o un número."
    for caracter in texto:
        if not (caracter.isalnum() or caracter in CARACTERES_NOMBRE_EXTRA):
            return False, f"El nombre contiene un carácter no permitido: '{caracter}'."
    return True, texto


def existe_jugador(nombre: str, ruta: str = None) -> bool:
    """
    Ejecuta la decisión «¿El jugador existe?» del diagrama de flujo, consultando por
    clave el diccionario de partidas guardadas (búsqueda O(1) en una tabla hash).

    Parámetros:
        nombre (str): Nombre del jugador a buscar (no distingue mayúsculas).
        ruta (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).

    Retorna:
        bool: True si hay una partida guardada con ese nombre; False si no existe, si el
              nombre es inválido o si el archivo no pudo leerse.
    """
    ruta = RUTA_PARTIDAS if ruta is None else ruta
    exito, nombre_valido = validar_nombre_jugador(nombre)
    if not exito:
        return False
    exito, partidas = _leer_partidas(ruta)
    return exito and _clave_jugador(nombre_valido) in partidas


def registrar_nuevo_jugador(nombre: str, sobrescribir: bool = False, ruta: str = None) -> tuple:
    """
    Ejecuta el nodo «Guardar nombre del jugador» (rama «nueva partida»): valida el
    nombre, crea el jugador con crear_jugador() de estructura.py y escribe su registro
    inicial (vida 20, puntaje 0.0, nivel 1, inventario vacío) en el archivo de partidas.

    Parámetros:
        nombre (str): Nombre ingresado para el nuevo jugador.
        sobrescribir (bool): Si es True, reemplaza una partida existente con ese nombre;
                             si es False (por defecto), rechaza nombres ya registrados.
        ruta (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es el diccionario
               del jugador recién creado; si es False, es un mensaje de error.
    """
    ruta = RUTA_PARTIDAS if ruta is None else ruta
    exito, resultado = validar_nombre_jugador(nombre)
    if not exito:
        return False, resultado
    nombre_valido = resultado

    exito, resultado = _leer_partidas(ruta)
    if not exito:
        return False, resultado
    partidas = resultado

    if _clave_jugador(nombre_valido) in partidas and not sobrescribir:
        return False, (f"Ya existe una partida guardada para '{nombre_valido}'. "
                       "Elige otro nombre o carga esa partida.")

    jugador = crear_jugador(nombre_valido)
    exito, mensaje = guardar_partida(jugador, ruta)
    if not exito:
        return False, mensaje
    return True, jugador


# ==============================================================================
# 3. GUARDADO Y CARGA DE PARTIDA (JSON)
# ==============================================================================

def _validar_fragmento(fragmento) -> tuple:
    """
    Verifica que un fragmento cumpla el modelo de datos (claves 'codigo', 'titulo',
    'sala' y 'valor') y lo normaliza con crear_fragmento() de estructura.py. Si trae la
    clave 'ubicacion', la restituye como tupla inmutable (estante, nivel), porque JSON
    solo almacena listas. Las claves adicionales se conservan sin cambios.

    Parámetros:
        fragmento (Any): Elemento del inventario a validar (idealmente un dict).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es un nuevo
               diccionario normalizado; si es False, es un mensaje con el motivo.
    """
    if not isinstance(fragmento, dict):
        return False, "No es un diccionario."

    faltantes = [clave for clave in CLAVES_FRAGMENTO if clave not in fragmento]
    if faltantes:
        return False, "Faltan las claves: " + ", ".join(faltantes) + "."
    if not _es_entero(fragmento["codigo"]):
        return False, "'codigo' debe ser un número entero."
    for clave in ("titulo", "sala"):
        if not isinstance(fragmento[clave], str) or not fragmento[clave].strip():
            return False, f"'{clave}' debe ser un texto no vacío."
    if not _es_numero_finito(fragmento["valor"]):
        return False, "'valor' debe ser un número finito."

    limpio = crear_fragmento(fragmento["codigo"], fragmento["titulo"],
                             fragmento["sala"], fragmento["valor"])

    if "ubicacion" in fragmento:
        ubicacion = fragmento["ubicacion"]
        if (not isinstance(ubicacion, (list, tuple)) or len(ubicacion) != 2
                or not all(_es_entero(parte) for parte in ubicacion)):
            return False, "'ubicacion' debe ser un par (estante, nivel) de enteros."
        limpio["ubicacion"] = (ubicacion[0], ubicacion[1])

    for clave, valor in fragmento.items():
        if clave not in limpio:
            limpio[clave] = valor
    return True, limpio


def _validar_estado_jugador(datos) -> tuple:
    """
    Valida el estado completo de un jugador (atributos tipados e inventario), ya sea el
    diccionario que se desea guardar o el registro leído del archivo. Es la única
    puerta de entrada y salida de datos, así nunca se escribe ni se carga información
    con tipos incorrectos.

    Parámetros:
        datos (Any): Diccionario con las claves de CLAVES_JUGADOR.

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es un diccionario
               limpio con nombre, vida, puntaje, nivel, partida_activa e inventario; si es
               False, es un mensaje con el motivo.
    """
    if not isinstance(datos, dict):
        return False, "Los datos del jugador no son un diccionario."

    faltantes = [clave for clave in CLAVES_JUGADOR if clave not in datos]
    if faltantes:
        return False, "Faltan las claves: " + ", ".join(faltantes) + "."

    exito, nombre = validar_nombre_jugador(datos["nombre"])
    if not exito:
        return False, nombre
    if not _es_entero(datos["vida"]) or datos["vida"] < 0:
        return False, "'vida' debe ser un entero mayor o igual a 0."
    if not _es_numero_finito(datos["puntaje"]):
        return False, "'puntaje' debe ser un número finito."
    if not _es_entero(datos["nivel"]) or datos["nivel"] < 1:
        return False, "'nivel' debe ser un entero mayor o igual a 1."
    if not isinstance(datos["partida_activa"], bool):
        return False, "'partida_activa' debe ser un valor booleano (true/false)."
    if not isinstance(datos["inventario"], list):
        return False, "'inventario' debe ser una lista."

    inventario = []
    for posicion, fragmento in enumerate(datos["inventario"], start=1):
        exito, resultado = _validar_fragmento(fragmento)
        if not exito:
            return False, f"El fragmento #{posicion} es inválido: {resultado}"
        inventario.append(resultado)

    return True, {
        "nombre": nombre,
        "vida": datos["vida"],
        "puntaje": float(datos["puntaje"]),
        "nivel": datos["nivel"],
        "partida_activa": datos["partida_activa"],
        "inventario": inventario,
    }


def guardar_partida(jugador: dict, ruta: str = None) -> tuple:
    """
    Guarda (o actualiza) la partida de un jugador en el archivo JSON, indexada por su
    nombre. Debe invocarse en cada «Desbloquear próxima sala» y antes de entrar a la
    Sala Central, porque el Paso 1 de la reconstrucción lee el inventario desde el archivo.
    No modifica el diccionario recibido y conserva intactas las partidas de otros jugadores.

    Parámetros:
        jugador (dict): Diccionario creado por crear_jugador() con el inventario actual.
        ruta (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).

    Retorna:
        tuple: Par (exito: bool, resultado: str) con un mensaje de confirmación o de error.
    """
    ruta = RUTA_PARTIDAS if ruta is None else ruta
    exito, resultado = _validar_estado_jugador(jugador)
    if not exito:
        return False, f"No se pudo guardar la partida. {resultado}"
    estado = resultado

    exito, resultado = _leer_partidas(ruta)
    if not exito:
        return False, resultado
    partidas = resultado

    registro = dict(estado)
    registro["ultima_actualizacion"] = _marca_de_tiempo()
    partidas[_clave_jugador(estado["nombre"])] = registro

    exito, resultado = _escribir_json_atomico(ruta, partidas)
    if not exito:
        return False, f"No se pudo guardar la partida. {resultado}"
    return True, f"Partida de '{estado['nombre']}' guardada correctamente."


def cargar_partida(nombre: str, ruta: str = None) -> tuple:
    """
    Ejecuta el nodo «Sincronizar Vestíbulo con el archivo de partida guardada»: busca
    al jugador por su nombre, valida su registro y reconstruye su diccionario con
    crear_jugador() de estructura.py, restituyendo también el inventario de fragmentos
    (con las ubicaciones como tuplas). Si el jugador no existe o el archivo está dañado,
    informa el error sin detener el juego.

    Parámetros:
        nombre (str): Nombre del jugador cuya partida se desea cargar.
        ruta (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es el diccionario
               del jugador sincronizado (su clave 'nivel' indica la sala guardada); si es
               False, es un mensaje de error.
    """
    ruta = RUTA_PARTIDAS if ruta is None else ruta
    exito, resultado = validar_nombre_jugador(nombre)
    if not exito:
        return False, resultado
    nombre_valido = resultado

    exito, resultado = _leer_partidas(ruta)
    if not exito:
        return False, resultado
    partidas = resultado

    registro = partidas.get(_clave_jugador(nombre_valido))
    if registro is None:
        return False, f"No se encontró ninguna partida guardada para '{nombre_valido}'."

    exito, resultado = _validar_estado_jugador(registro)
    if not exito:
        return False, f"La partida guardada de '{nombre_valido}' está dañada. {resultado}"
    estado = resultado

    jugador = crear_jugador(estado["nombre"], estado["vida"], estado["puntaje"],
                            estado["nivel"], estado["partida_activa"])
    jugador["inventario"] = estado["inventario"]
    return True, jugador


def obtener_sala_guardada(jugador: dict) -> tuple:
    """
    Ejecuta el nodo «Sincronizar sala guardada por el jugador» y su cadena de decisiones
    «¿Sala 1?» … «¿Sala 5?»: obtiene la sala a la que debe redirigirse al jugador y
    detecta el caso de error («Informar sobre el error») si no corresponde a ninguna.

    Parámetros:
        jugador (dict): Diccionario devuelto por cargar_partida(); su clave 'nivel'
                        guarda la sala actual (de 1 a NUMERO_SALAS).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es el número
               de sala (int de 1 a 5); si es False, es un mensaje de error.
    """
    if not isinstance(jugador, dict) or not _es_entero(jugador.get("nivel")):
        return False, "No se pudo determinar la sala guardada del jugador."
    sala = jugador["nivel"]
    if not 1 <= sala <= NUMERO_SALAS:
        return False, (f"La sala guardada ({sala}) no existe: las salas válidas "
                       f"van de 1 a {NUMERO_SALAS}.")
    return True, sala


# ==============================================================================
# 4. SALA CENTRAL, PASO 1: CARGA DE LOS FRAGMENTOS RECOLECTADOS
# ==============================================================================

def cargar_fragmentos_recolectados(nombre: str, ruta: str = None) -> tuple:
    """
    Ejecuta el Paso 1 (Carga) de «La Reconstrucción del Catálogo»: lee desde el archivo
    los fragmentos recolectados durante la partida, cada uno como diccionario. La lista
    se entrega TAL CUAL fue guardada (incluidos los códigos repetidos), porque la
    depuración con conjuntos es el Paso 2 y está en ejecutar_reconstruccion_catalogo()
    de estructura.py, que debe poder contar cuántos duplicados se descartan.

    Parámetros:
        nombre (str): Nombre del jugador dueño del inventario.
        ruta (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es la lista de
               diccionarios de fragmentos lista para ejecutar_reconstruccion_catalogo();
               si es False, es un mensaje de error.
    """
    exito, resultado = cargar_partida(nombre, ruta)
    if not exito:
        return False, resultado
    return True, resultado["inventario"]


# ==============================================================================
# 5. TABLA DE PUNTAJES (CSV) Y CIERRE DE PARTIDA
# ==============================================================================

def _construir_registro_puntaje(nombre: str, puntaje: float,
                                fragmentos_validos: int, intentos: int) -> tuple:
    """
    Valida los datos de un resultado final y arma la fila (diccionario) que se agregará
    a la tabla de puntajes, con la fecha y hora actuales.

    Parámetros:
        nombre (str): Nombre del jugador.
        puntaje (float): Puntuación final calculada por la lógica del juego (finita).
        fragmentos_validos (int): Cantidad de fragmentos válidos recuperados (>= 0).
        intentos (int): Número de intentos calculado por la lógica del juego (>= 0).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es el diccionario
               con las claves de COLUMNAS_PUNTAJES; si es False, es un mensaje de error.
    """
    exito, resultado = validar_nombre_jugador(nombre)
    if not exito:
        return False, resultado
    if not _es_numero_finito(puntaje):
        return False, "El puntaje debe ser un número finito."
    if not _es_entero(fragmentos_validos) or fragmentos_validos < 0:
        return False, "Los fragmentos válidos deben ser un entero mayor o igual a 0."
    if not _es_entero(intentos) or intentos < 0:
        return False, "Los intentos deben ser un entero mayor o igual a 0."

    return True, {
        "nombre": resultado,
        "puntaje": round(float(puntaje), 2),
        "fragmentos_validos": fragmentos_validos,
        "intentos": intentos,
        "fecha": _marca_de_tiempo(),
    }


def _agregar_fila_puntaje(registro: dict, ruta: str = None) -> tuple:
    """
    Agrega una fila al final del archivo CSV de puntajes (historial). Si el archivo no
    existe o está vacío, escribe primero el encabezado. Usa utf-8-sig para que Excel
    muestre bien las tildes.

    Parámetros:
        registro (dict): Fila con las claves de COLUMNAS_PUNTAJES.
        ruta (str, opcional): Archivo CSV de puntajes (por defecto RUTA_PUNTAJES).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es la ruta
               escrita; si es False, es un mensaje de error.
    """
    ruta = RUTA_PUNTAJES if ruta is None else ruta
    try:
        directorio = os.path.dirname(ruta)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        escribir_encabezado = not os.path.isfile(ruta) or os.path.getsize(ruta) == 0
        with open(ruta, "a", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_PUNTAJES)
            if escribir_encabezado:
                escritor.writeheader()
            escritor.writerow(registro)
        return True, ruta
    except OSError as error:
        return False, _describir_error_archivo(error, ruta)
    except (csv.Error, ValueError) as error:
        return False, f"No se pudo escribir la tabla de puntajes: {error}"


def actualizar_tabla_puntajes(nombre: str, puntaje: float, fragmentos_validos: int,
                              intentos: int, ruta: str = None) -> tuple:
    """
    Agrega un resultado a la tabla histórica de puntajes (archivo CSV), validando antes
    todos los datos. No sobrescribe resultados anteriores: cada partida terminada suma una fila.

    Parámetros:
        nombre (str): Nombre del jugador.
        puntaje (float): Puntuación final de la partida.
        fragmentos_validos (int): Cantidad de fragmentos válidos recuperados.
        intentos (int): Número de intentos de la partida.
        ruta (str, opcional): Archivo CSV de puntajes (por defecto RUTA_PUNTAJES).

    Retorna:
        tuple: Par (exito: bool, resultado: str) con un mensaje de confirmación o de error.
    """
    exito, resultado = _construir_registro_puntaje(nombre, puntaje, fragmentos_validos, intentos)
    if not exito:
        return False, resultado
    registro = resultado

    exito, resultado = _agregar_fila_puntaje(registro, ruta)
    if not exito:
        return False, resultado
    return True, f"Puntaje de '{registro['nombre']}' registrado en la tabla."


def _convertir_fila_puntaje(fila: dict) -> dict:
    """
    Convierte una fila leída del CSV (todo texto) a sus tipos reales usando
    convertir_y_validar_tipo() de estructura.py. Las filas incompletas o con datos
    inválidos se descartan para que una línea dañada no impida mostrar la tabla.

    Parámetros:
        fila (dict): Fila entregada por csv.DictReader (claves y valores de tipo str).

    Retorna:
        dict: Registro con los tipos correctos (str, float, int, int, str), o None si la
              fila es inválida.
    """
    if any(fila.get(columna) is None for columna in COLUMNAS_PUNTAJES):
        return None

    exito_nombre, nombre = validar_nombre_jugador(fila["nombre"])
    exito_puntaje, puntaje = convertir_y_validar_tipo(fila["puntaje"], float)
    exito_fragmentos, fragmentos = convertir_y_validar_tipo(fila["fragmentos_validos"], int)
    exito_intentos, intentos = convertir_y_validar_tipo(fila["intentos"], int)
    if not (exito_nombre and exito_puntaje and exito_fragmentos and exito_intentos):
        return None
    if not _es_numero_finito(puntaje) or fragmentos < 0 or intentos < 0:
        return None

    return {
        "nombre": nombre,
        "puntaje": puntaje,
        "fragmentos_validos": fragmentos,
        "intentos": intentos,
        "fecha": fila["fecha"].strip(),
    }


def cargar_tabla_puntajes(limite: int = None, ruta: str = None) -> tuple:
    """
    Lee la tabla de puntajes del archivo CSV y la ordena de mayor a menor puntaje
    (ante empates se conserva el orden cronológico, porque list.sort() es estable).
    Si el archivo todavía no existe, retorna una tabla vacía sin considerarlo un error.

    Parámetros:
        limite (int, opcional): Cantidad máxima de posiciones a retornar (por ejemplo, 10).
        ruta (str, opcional): Archivo CSV de puntajes (por defecto RUTA_PUNTAJES).

    Retorna:
        tuple: Par (exito: bool, resultado). Si exito es True, 'resultado' es la lista de
               diccionarios (nombre, puntaje, fragmentos_validos, intentos, fecha) ordenada;
               si es False, es un mensaje de error.
    """
    ruta = RUTA_PUNTAJES if ruta is None else ruta
    if limite is not None and (not _es_entero(limite) or limite < 1):
        return False, "El límite de la tabla debe ser un entero positivo."

    tabla = []
    try:
        with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                registro = _convertir_fila_puntaje(fila)
                if registro is not None:
                    tabla.append(registro)
    except FileNotFoundError:
        return True, []
    except UnicodeDecodeError:
        return False, f"La tabla de puntajes está dañada (codificación inválida): {ruta}"
    except OSError as error:
        return False, _describir_error_archivo(error, ruta)
    except csv.Error as error:
        return False, f"La tabla de puntajes está dañada ({error}): {ruta}"

    tabla.sort(key=lambda registro: registro["puntaje"], reverse=True)
    if limite is not None:
        tabla = tabla[:limite]
    return True, tabla


def guardar_resultado_final(jugador: dict, fragmentos_validos: int, intentos: int,
                            ruta_partidas: str = None, ruta_puntajes: str = None) -> tuple:
    """
    Ejecuta el nodo «Guardar resultado y actualizar tabla de puntajes»: guarda el estado
    final del jugador y agrega su resultado a la tabla histórica. Los datos se validan
    ANTES de escribir, para no dejar la partida guardada y la tabla desincronizadas.
    El puntaje registrado es el de jugador["puntaje"], que la lógica del juego ya debió
    calcular en «Calcular puntuación final». No modifica el diccionario recibido.

    Parámetros:
        jugador (dict): Diccionario del jugador con su puntaje final e inventario.
        fragmentos_validos (int): Cantidad de fragmentos válidos recuperados.
        intentos (int): Número de intentos calculado por la lógica del juego.
        ruta_partidas (str, opcional): Archivo JSON de partidas (por defecto RUTA_PARTIDAS).
        ruta_puntajes (str, opcional): Archivo CSV de puntajes (por defecto RUTA_PUNTAJES).

    Retorna:
        tuple: Par (exito: bool, resultado: str) con un mensaje de confirmación o de error.
    """
    if not isinstance(jugador, dict):
        return False, "El jugador debe ser un diccionario."

    exito, resultado = _construir_registro_puntaje(jugador.get("nombre"), jugador.get("puntaje"),
                                                   fragmentos_validos, intentos)
    if not exito:
        return False, f"No se pudo guardar el resultado. {resultado}"
    registro = resultado

    exito, resultado = guardar_partida(jugador, ruta_partidas)
    if not exito:
        return False, resultado

    exito, resultado = _agregar_fila_puntaje(registro, ruta_puntajes)
    if not exito:
        return False, ("La partida se guardó, pero no se pudo actualizar la tabla "
                       f"de puntajes. {resultado}")
    return True, "Resultado guardado y tabla de puntajes actualizada."


def formatear_tabla_puntajes(tabla: list) -> str:
    """
    Da formato de texto alineado a la tabla de puntajes, lista para imprimirse en la
    consola en el nodo «Mostrar tabla de puntajes».

    Parámetros:
        tabla (list): Lista de diccionarios retornada por cargar_tabla_puntajes().

    Retorna:
        str: Tabla en varias líneas, o un aviso si todavía no hay puntajes.
    """
    if not tabla:
        return "Aún no hay puntajes registrados."

    ancho_nombre = max(len("Jugador"), max(len(fila["nombre"]) for fila in tabla))
    encabezado = (f"{'#':>3}  {'Jugador':<{ancho_nombre}}  {'Puntaje':>9}  "
                  f"{'Fragmentos':>10}  {'Intentos':>8}  Fecha")
    filas = [
        (f"{posicion:>3}  {fila['nombre']:<{ancho_nombre}}  {fila['puntaje']:>9.2f}  "
         f"{fila['fragmentos_validos']:>10}  {fila['intentos']:>8}  {fila['fecha']}")
        for posicion, fila in enumerate(tabla, start=1)
    ]
    ancho_total = max(len(encabezado), max(len(fila) for fila in filas))
    return "\n".join([encabezado, "-" * ancho_total] + filas)


# ==============================================================================
# 6. DEMOSTRACIÓN (solo al ejecutar «python persistencia.py»)
# ==============================================================================

def _demostracion() -> None:
    """
    Recorre el flujo de persistencia del diagrama (registro, guardado, carga, Paso 1 de la
    Sala Central y tabla de puntajes) en una carpeta temporal, de modo que no se
    modifiquen los archivos reales de la carpeta «datos».

    Parámetros:
        Ninguno.

    Retorna:
        None
    """
    import tempfile
    from estructura import ejecutar_reconstruccion_catalogo

    with tempfile.TemporaryDirectory() as carpeta:
        ruta_partidas = os.path.join(carpeta, "partidas.json")
        ruta_puntajes = os.path.join(carpeta, "puntajes.csv")

        print("1) Nombre inválido ->", validar_nombre_jugador("   ")[1])

        exito, jugador = registrar_nuevo_jugador("Ana María", ruta=ruta_partidas)
        print("2) Jugador nuevo   ->", jugador["nombre"], "| vida:", jugador["vida"])

        # El jugador supera las salas 1 a 4; el último fragmento se repite a propósito.
        for codigo, titulo, sala in [(30, "Tratado de Listas", "Estanterías"),
                                     (10, "Plano del Ala Norte", "Mapas"),
                                     (20, "Ficha de Autores", "Fichas"),
                                     (40, "Sello Maestro", "Sellos"),
                                     (40, "Sello Maestro", "Sellos")]:
            jugador["inventario"].append(crear_fragmento(codigo, titulo, sala, 10.0))
        jugador["nivel"] = 5
        print("3) Guardar partida ->", guardar_partida(jugador, ruta_partidas)[1])

        print("4) ¿Existe 'ana maría'? ->", existe_jugador("ana maría", ruta_partidas),
              "| ¿Existe 'Luis'? ->", existe_jugador("Luis", ruta_partidas))
        print("5) Jugador inexistente ->", cargar_partida("Luis", ruta_partidas)[1])

        exito, cargado = cargar_partida("ANA MARÍA", ruta_partidas)
        exito, sala = obtener_sala_guardada(cargado)
        print("6) Partida cargada ->", cargado["nombre"], "| sala guardada:", sala,
              "| fragmentos:", len(cargado["inventario"]))

        exito, fragmentos = cargar_fragmentos_recolectados("Ana María", ruta_partidas)
        resumen = ejecutar_reconstruccion_catalogo(fragmentos)
        print("7) Paso 1 + 2      -> cargados:", resumen["total_cargados"],
              "| descartados:", resumen["descartados"],
              "| orden inorden válido:", resumen["orden_valido"])

        cargado["inventario"] = resumen["fragmentos_depurados"]
        cargado["puntaje"] = 85.5
        validos = resumen["total_cargados"] - resumen["descartados"]
        exito, mensaje = guardar_resultado_final(cargado, validos, 3, ruta_partidas, ruta_puntajes)
        print("8) Resultado final ->", mensaje)

        exito, recargado = cargar_partida("Ana María", ruta_partidas)
        ubicacion = recargado["inventario"][0]["ubicacion"]
        print("9) Ubicación restituida como tupla ->", ubicacion, type(ubicacion).__name__)

        exito, tabla = cargar_tabla_puntajes(10, ruta_puntajes)
        print("10) Tabla de puntajes:")
        print(formatear_tabla_puntajes(tabla))


if __name__ == "__main__":
    _demostracion()
