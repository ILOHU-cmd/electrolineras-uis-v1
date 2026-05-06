"""
validacion.py
Funciones para leer y validar datos que ingresa el usuario.
Se usan en todo el programa para evitar que entren valores
incorrectos como letras donde van numeros, o numeros negativos.
"""


def leer_entero(mensaje, minimo=None, maximo=None):
    # Repite la pregunta hasta que el usuario ingrese un numero valido
    while True:
        entrada = input(mensaje).strip()

        # Verificar que no este vacio
        if entrada == "":
            print("Debe ingresar un valor. No puede dejar esto en blanco.")
            continue

        # Verificar que sea un numero entero (acepta negativos con el signo -)
        es_numero = True
        texto_a_revisar = entrada

        if texto_a_revisar.startswith("-"):
            texto_a_revisar = texto_a_revisar[1:]

        if not texto_a_revisar.isdigit():
            es_numero = False

        if not es_numero:
            print("Valor invalido. Debe ingresar solo digitos enteros.")
            continue

        numero = int(entrada)

        # Verificar rango minimo
        if minimo is not None and numero < minimo:
            print("El valor minimo permitido es", minimo)
            continue

        # Verificar rango maximo
        if maximo is not None and numero > maximo:
            print("El valor maximo permitido es", maximo)
            continue

        # Si pasa todas las validaciones, retorna el numero
        return numero


def leer_flotante(mensaje, minimo=None, maximo=None):
    # Similar a leer_entero pero acepta decimales
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("Debe ingresar un valor.")
            continue

        # Intentar convertir a decimal
        try:
            numero = float(entrada)
        except ValueError:
            print("Valor invalido. Use punto decimal (ejemplo: 15.5)")
            continue

        if minimo is not None and numero < minimo:
            print("El valor minimo permitido es", minimo)
            continue

        if maximo is not None and numero > maximo:
            print("El valor maximo permitido es", maximo)
            continue

        return numero


def leer_si_no(mensaje):
    # Pide una confirmacion de si o no al usuario
    # Retorna True si responde 's', False si responde 'n'
    while True:
        respuesta = input(mensaje + " (s/n): ").strip().lower()
        if respuesta == "s":
            return True
        elif respuesta == "n":
            return False
        else:
            print("Respuesta invalida. Ingrese 's' para si o 'n' para no.")
