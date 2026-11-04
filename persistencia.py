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
# configuracion importante para poder empezar
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

