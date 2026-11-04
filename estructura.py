# ===================================================================================
# VESTÍBULO (INICIAR PARTIDA, VARIABLES BASE DEL JUGADOR Y FUNCIONES DE VALIDACIÓN)
# ===================================================================================

def crear_jugador(
        nombre:str,
        vida:int=20,
        puntaje:float=0.0,
        nivel:int=1,
        partida_activa:bool=True
)->dict:
    """
    Inicializa y retorna el estado base del jugador.
    
    Parámetros:
        nombre(str): Nombre del jugador.
        vida(int): Puntos de vida base (20).
        puntaje(float): Puntuación acumulada en la partida (por defecto 0.0 en nueva partida).
        nivel(int): Sala actual del jugador (por defecto 1 para nueva partida).
        partida_activa(bool): Estado lógico de la partida (por defecto True para iniciar partida).
    
    Retorna:
        dict: Diccionario con los atributos tipados del jugador e inventario vacío.
    """
    return {
        "nombre":str(nombre).strip(),
        "vida":int(vida),
        "puntaje":float(puntaje),
        "nivel":int(nivel),
        "partida_activa":bool(partida_activa),
        "inventario":[]
    }

def actualizar_vida_jugador(jugador: dict, cambio: int = -1)->bool:
    """
    Modifica los puntos de vida del jugador (por ejemplo, restando 1 tras un fallo)
    y actualiza el estado booleano 'partida_activa' verificando si vida > 0.

    Parámetros:
        jugador(dict): Diccionario con el estado actual del jugador.
        cambio(int): Cantidad entera a sumar o restar a la vida (por defecto -1).

    Retorna:
        bool: True si el jugador sigue con vida (vida > 0), False si perdió la partida.
    """
    jugador["vida"]=int(jugador["vida"])+int(cambio)
    if jugador["vida"]<=0:
        jugador["vida"]=0
        jugador["partida_activa"]=False
    else:
        jugador["partida_activa"]=True
    return jugador["partida_activa"]

def convertir_y_validar(entrada_usuario:str, tipo_esperado:type):
    """
    Convierte una cadena de texto ingresada por el usuario al tipo de dato
    especificado en cada variable (int, float, str o bool), controlando errores de conversión.

    Parámetros:
        entrada_usuario(str): Texto crudo proveniente de input().
        tipo_esperado(type): Tipo de dato al que se desea convertir (int, float, str, bool).

    Retorna:
        tuple: Par (exito: bool, valor_convertido: Any) indicando si la conversión fue válida y el dato resultante (o None si falló).
    """
    texto_limpio=str(entrada_usuario).strip()
    try:
        if tipo_esperado is int:
            return True, int(texto_limpio)
        elif tipo_esperado is float:
            return True, float(texto_limpio)
        elif tipo_esperado is bool:
            if texto_limpio.lower() in ("true", "1", "si", "sí", "s", "verdadero"):
                return True, True
            elif texto_limpio.lower() in ("false", "0", "no", "n", "falso"):
                return True, False
            else:
                raise ValueError("Entrada booleana no reconocida.")
        elif tipo_esperado is str:
            if len(texto_limpio)==0:
                raise ValueError("La cadena de texto no puede estar vacía.")
            return True, texto_limpio
        else:
            raise ValueError("Tipo de dato no soportado.")
    except ValueError:
        return False, None

# =============================================================================
# CARGAR MODELO DEL FRAGMENTO Y SALA 3 (SALA DE FICHAS) CON DICCIONARIOS
# =============================================================================

def crear_fragmento(codigo:int,titulo:str,sala:str,valor:float)->dict:
    """
    Crea y retorna un diccionario que representa los fragmentos del juego.
    
    Parámetros del diccionario:
        codigo(int): Código único del fragmento.
        titulo(str): Nombre del fragmento.
        sala(str): Sala en la que se encuentra el fragmento.
        valor(float): Valor de relevancia del fragmento.
    
    Retorna:
        dict: Diccionario que incluye las cuatro claves requeridas para los fragmentos.
    """
    fragmento = {
        "codigo": codigo,
        "titulo": titulo,
        "sala": sala,
        "valor": valor
    }
    return fragmento


def consultar_atributo_fragmento(
        fragmento:dict,
        clave:str,
        valor_por_defecto:str="No registrado"
):
    """
    Consulta de forma segura en tiempo O(1) amortizado un atributo dentro de un
    fragmentO, manejando claves inexistentes sin detener el programa.

    Parámetros:
        fragmento(dict): Diccionario que representa el fragmento.
        clave(str): Nombre de la clave que se desea consultar.
        valor_por_defecto(str): Valor retornado si la clave no existe en el diccionario.
    
    Retorna:
        Any: El valor asociado a la clave solicitada o el mensaje por defecto.
    """
    if not isinstance(fragmento, dict):
        return valor_por_defecto
    return fragmento.get(clave, valor_por_defecto)