def crear_fragmento(codigo:int,titulo:str,sala:str,valor:float) -> dict:
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

# ====================================================================================
# 1. VESTÍBULO (INICIAR PARTIDA, VARIABLES BASE DEL JUGADOR Y FUNCIONES DE VALIDACIÓN)
# ====================================================================================

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
        nombre (str): Nombre del jugador.
        vida (int): Puntos de vida base (20).
        puntaje (float): Puntuación acumulada en la partida (por defecto 0.0 en nueva partida).
        nivel (int): Sala actual del jugador (por defecto 1 para nueva partida).
        partida_activa (bool): Estado lógico de la partida (por defecto True para iniciar partida).
    
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