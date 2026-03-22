
from sys import argv

CANTIDAD_PARAMETROS = 2
NOMBRE_SUBSCRIPT = "compose_generator"

def generar_compose(nombre_archivo, cantidad_clientes):
    # Definición fija del servidor
    contenido = """services:
                server:
                    container_name: server
                    image: server:latest
                    entrypoint: python3 /main.py
                    environment:
                    - PYTHONUNBUFFERED=1
                    - LOGGING_LEVEL=DEBUG
                    networks:
                    - testing_net
                """

    # Generar dinámicamente los clientes
    for i in range(1, cantidad_clientes + 1):
        contenido += f"""
        client{i}:
            container_name: client{i}
            image: client:latest
            entrypoint: /client
            environment:
            - CLI_ID={i}
            - CLI_LOG_LEVEL=DEBUG
            networks:
            - testing_net
            depends_on:
            - server
        """

    # Definición de la red
    contenido += """
        networks:
        testing_net:
            ipam:
            driver: default
            config:
                - subnet: 172.25.125.0/24
        """

    # Escribir el contenido en el archivo
    with open(nombre_archivo, 'w') as archivo:
        archivo.write(contenido)

def validate_parameters(argv):
    if len(argv) != CANTIDAD_PARAMETROS+1:
        print(f"Uso: python3 {NOMBRE_SUBSCRIPT}.py <nombre_archivo> <cantidad_clientes>")
        exit(1)

    _,nombre_archivo,cantidad_clientes = argv

    if not nombre_archivo.endswith('.yaml'):
        print("El nombre del archivo debe terminar con .yaml")
        exit(2)
    
    if not cantidad_clientes.isdigit() or int(cantidad_clientes) <= 0:
        print("La cantidad de clientes debe ser un número entero positivo")
        exit(2)
    

def main(argv):
    validate_parameters(argv)

    _,nombre_archivo,cantidad_clientes = argv

    # Generar el archivo Docker Compose
    generar_compose(nombre_archivo, int(cantidad_clientes))




if __name__ == "__main__":
    main(argv)