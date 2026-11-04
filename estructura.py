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