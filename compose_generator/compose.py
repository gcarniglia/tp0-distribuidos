from compose_generator.constants import PATH_CONFIG_CLIENTE, PATH_CONFIG_SERVER
from compose_generator.file_writer import escribir_archivo


def generar_compose(nombre_archivo, cantidad_clientes):
    data = construir_datos_compose(cantidad_clientes)
    escribir_archivo(nombre_archivo, data)



def construir_datos_compose(cantidad_clientes):
    data = {
        #"name": "tp0",
        "services": {
            "server": {
                "container_name": "server",
                "image": "server:latest",
                "entrypoint": "python3 /main.py",
                "environment": ["PYTHONUNBUFFERED=1"],
                "networks": ["testing_net"],
                "volumes": [f"{PATH_CONFIG_SERVER}:/config.ini"]
            }
        },
        "networks": {
            "testing_net": {
                "ipam": {
                    "driver": "default",
                    "config": [{"subnet": "172.25.125.0/24"}],
                }
            }
        },
    }

    for i in range(1, cantidad_clientes + 1):
        data["services"][f"client{i}"] = {
            "container_name": f"client{i}",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": [f"CLI_ID={i}"],
            "networks": ["testing_net"],
            "depends_on": ["server"],
            "volumes": [f"{PATH_CONFIG_CLIENTE}:/config.yaml"]
        }

    return data
