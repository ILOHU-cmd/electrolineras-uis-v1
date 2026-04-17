"""
Funciones sencillas para validar entradas del usuario.
"""

import os


def limpiar_pantalla():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def leer_entero(mensaje, minimo=None, maximo=None):
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("Entrada vacia. Digite un numero entero.")
        else:
            if entrada[0] == "-":
                parte_numerica = entrada[1:]
            else:
                parte_numerica = entrada

            if parte_numerica == "" or not parte_numerica.isdigit():
                print("Solo se permiten numeros enteros.")
            else:
                valor = int(entrada)

                if minimo is not None and valor < minimo:
                    print("El numero debe ser mayor o igual a", minimo)
                elif maximo is not None and valor > maximo:
                    print("El numero debe ser menor o igual a", maximo)
                else:
                    return valor

        print()


def leer_flotante(mensaje, minimo=None, maximo=None):
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("Entrada vacia. Digite un numero.")
        else:
            entrada = entrada.replace(",", ".")

            try:
                valor = float(entrada)

                if minimo is not None and valor < minimo:
                    print("El numero debe ser mayor o igual a", minimo)
                elif maximo is not None and valor > maximo:
                    print("El numero debe ser menor o igual a", maximo)
                else:
                    return valor

            except ValueError:
                print("Formato invalido. Ejemplo valido: 12.5")

        print()


def leer_texto(mensaje, solo_alfa=False, max_len=100):
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("Este campo no puede quedar vacio.")
        elif len(entrada) > max_len:
            print("El texto es demasiado largo. Maximo:", max_len)
        elif solo_alfa and not entrada.replace(" ", "").isalpha():
            print("Solo se permiten letras y espacios.")
        else:
            return entrada

        print()


def validar_nivel_bateria(nivel):
    if nivel >= 0 and nivel <= 100:
        return True
    else:
        return False


def confirmar(mensaje):
    while True:
        respuesta = input(mensaje + " [s/n]: ").strip().lower()

        if respuesta == "s":
            return True
        elif respuesta == "n":
            return False
        else:
            print("Respuesta invalida. Escriba s o n.")
            print()
