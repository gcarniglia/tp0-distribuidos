from compose_generator.constants import DEFAULT_BETS, PATH_CONFIG_CLIENTE, PATH_CONFIG_SERVER
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
                "environment": [
                    "PYTHONUNBUFFERED=1",
                    f"SERVER_TOTAL_AGENCIES={cantidad_clientes}",
                ],
                "networks": ["testing_net"],
                "volumes": [f"{PATH_CONFIG_SERVER}:/config.ini"]
            },
            "tester": {
                "image": "busybox:latest",
                "networks": ["testing_net"],
                "entrypoint": "/bin/sh"
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
        default_bet = DEFAULT_BETS[(i - 1) % len(DEFAULT_BETS)]
        client_environment = [
            f"CLI_ID={i}",
            f"NOMBRE={default_bet['NOMBRE']}",
            f"APELLIDO={default_bet['APELLIDO']}",
            f"DOCUMENTO={default_bet['DOCUMENTO']}",
            f"NACIMIENTO={default_bet['NACIMIENTO']}",
            f"NUMERO={default_bet['NUMERO']}",
        ]

        data["services"][f"client{i}"] = {
            "container_name": f"client{i}",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": client_environment,
            "networks": ["testing_net"],
            "depends_on": ["server"],
            "volumes": [f"{PATH_CONFIG_CLIENTE}:/config.yaml"]
        }

    return data
