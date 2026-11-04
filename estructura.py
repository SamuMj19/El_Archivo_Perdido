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
        tuple: Par (exito: bool, valor_convertido: Any) indicando si la conversión fue válida 
        y el dato resultante (o None si falló).
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
    if not isinstance(fragmento,dict):
        return valor_por_defecto
    return fragmento.get(clave, valor_por_defecto)

def consultar_ficha_con_excepcion(fragmento:dict,clave:str)->tuple:
    """
    Realiza la lectura directa de una clave sobre un diccionario capturando
    la excepción KeyError en caso de que la clave sea inexistente.

    Parámetros:
        fragmento(dict): Diccionario del fragmento a inspeccionar.
        clave(str): Clave que se intenta buscar directamente.

    Retorna:
        tuple: Par (encontrado: bool, resultado: Any) con el valor o mensaje de control.
    """
    try:
        return True, fragmento[clave]
    except KeyError:
        return False, f"La clave '{clave}' no existe en la ficha consultada."


def construir_catalogo_fichas(lista_fragmentos:list)->dict:
    """
    Construye un diccionario de acceso rápido indexado por el código del fragmento
    mediante comprensión de diccionarios (dict comprehension).

    Parámetros:
        lista_fragmentos(list): Lista de diccionarios de fragmentos.

    Retorna:
        dict: Diccionario donde cada clave es el 'codigo' (int) y el valor es el fragmento.
    """
    return {frag["codigo"]:frag for frag in lista_fragmentos if "codigo" in frag}

# ==============================================================================
# SALA DE ESTANTERÍAS (SALA 1) CON LISTAS Y COMPRENSIÓN DE LISTAS
# ==============================================================================

def insertar_fragmento_lista(
        inventario:list,
        fragmento:dict,
        posicion:int=None
)->list:
    """
    Inserta un fragmento en la lista de inventario. Si no se indica posición,
    se agrega al final con .append() en O(1) amortizado; si se indica, usa .insert() en O(n).

    Parámetros:
        inventario(list): Lista actual de fragmentos recolectados.
        fragmento(dict): Fragmento que se desea añadir.
        posicion(int, opcional): Índice donde se insertará el fragmento.

    Retorna:
        list: La lista de inventario actualizada.
    """
    if posicion is None or posicion>=len(inventario):
        inventario.append(fragmento)
    else:
        indice_seguro=max(0, int(posicion))
        inventario.insert(indice_seguro, fragmento)
    return inventario


def eliminar_fragmento_lista(inventario:list,codigo_objetivo:int)->tuple:
    """
    Busca y elimina la primera aparición de un fragmento según su código dentro
    de la lista de inventario utilizando .remove().

    Parámetros:
        inventario(list): Lista de fragmentos del jugador.
        codigo_objetivo(int): Código numérico del fragmento a eliminar.

    Retorna:
        tuple: Par (eliminado: bool, fragmento_eliminado: dict o None).
    """
    for fragmento in inventario:
        if fragmento.get("codigo")==codigo_objetivo:
            inventario.remove(fragmento)
            return True, fragmento
    return False, None


def extraer_fragmento_por_indice(inventario: list, indice: int = -1)->tuple:
    """
    Extrae y retorna un fragmento de la lista según su posición usando .pop(),
    controlando índices fuera de rango.

    Parámetros:
        inventario (list): Lista de fragmentos del jugador.
        indice (int): Posición de la cual extraer (por defecto -1, el último).

    Retorna:
        tuple: Par (exito: bool, fragmento: dict o None).
    """
    if not inventario:
        return False, None
    try:
        fragmento_extraido=inventario.pop(indice)
        return True, fragmento_extraido
    except IndexError:
        return False, None


def buscar_fragmento_secuencial(lista_fragmentos: list, codigo_objetivo: int)->tuple:
    """
    Realiza una búsqueda secuencial O(n) sobre una lista de fragmentos,
    contando el número exacto de comparaciones de claves realizadas.

    Parámetros:
        lista_fragmentos (list): Lista de diccionarios de fragmentos.
        codigo_objetivo (int): Código numérico del fragmento buscado.

    Retorna:
        tuple: Par (fragmento_encontrado: dict o None, comparaciones: int).
    """
    comparaciones=0
    for fragmento in lista_fragmentos:
        comparaciones+=1
        if fragmento.get("codigo")==codigo_objetivo:
            return fragmento, comparaciones
    return None, comparaciones


def ordenar_inventario_lista(
        inventario:list,
        clave_orden:str="codigo",
        reverso:bool=False
)->list:
    """
    Ordena in-place la lista de fragmentos según la clave especificada ('codigo' o 'valor')
    utilizando el método nativo .sort() (Timsort, O(n log n)).

    Parámetros:
        inventario(list): Lista de fragmentos a ordenar.
        clave_orden(str): Campo del diccionario por el cual ordenar ('codigo' o 'valor').
        reverso(bool): Si es True, ordena de forma descendente; si es False, ascendente.

    Retorna:
        list: La lista de inventario ordenada.
    """
    inventario.sort(key=lambda frag: frag.get(clave_orden, 0), reverse=reverso)
    return inventario


def filtrar_fragmentos_por_valor(inventario: list, umbral: float) -> list:
    """
    Filtra los fragmentos del inventario cuyo valor de relevancia sea mayor o igual
    al umbral indicado, empleando obligatoriamente una comprensión de listas.

    Parámetros:
        inventario(list): Lista de fragmentos (diccionarios) a filtrar.
        umbral(float): Valor mínimo de relevancia requerido.

    Retorna:
        list: Nueva lista con los fragmentos que cumplen la condición.
    """
    return [f for f in inventario if f.get("valor", 0.0) >= float(umbral)]