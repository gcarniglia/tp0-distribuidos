from .constants import CANTIDAD_PARAMETROS, COMANDO_USO


def validate_parameters(argv):
    if len(argv) != CANTIDAD_PARAMETROS + 1:
        print(f"Uso: {COMANDO_USO} <nombre_archivo> <cantidad_clientes>")
        exit(1)

    _, nombre_archivo, cantidad_clientes = argv

    if not nombre_archivo.endswith(".yaml"):
        print("El nombre del archivo debe terminar con .yaml")
        exit(2)

    if not cantidad_clientes.isdigit() or int(cantidad_clientes) < 0:
        print("La cantidad de clientes debe ser un número entero positivo")
        exit(2)
