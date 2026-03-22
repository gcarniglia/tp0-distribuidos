from sys import argv
from compose_generator.compose import generar_compose
from .validators import validate_parameters

def main(cli_args=None):
    argumentos = argv if cli_args is None else cli_args
    validate_parameters(argumentos)
    _, nombre_archivo, cantidad_clientes = argumentos
    generar_compose(nombre_archivo, int(cantidad_clientes))


if __name__ == "__main__":
    main()