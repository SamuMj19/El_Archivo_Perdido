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


