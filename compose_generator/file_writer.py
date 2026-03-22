

def escribir_archivo(nombre_archivo, contenido):
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(dict_a_yaml(contenido))

def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


def _yaml_lines(value, indent=0):
    espacio = " " * indent

    if isinstance(value, dict):
        if not value:
            return [f"{espacio}{{}}"]

        lineas = []
        for clave, contenido in value.items():
            if isinstance(contenido, (dict, list)):
                lineas.append(f"{espacio}{clave}:")
                lineas.extend(_yaml_lines(contenido, indent + 2))
            else:
                lineas.append(f"{espacio}{clave}: {_yaml_scalar(contenido)}")
        return lineas

    if isinstance(value, list):
        if not value:
            return [f"{espacio}[]"]

        lineas = []
        for item in value:
            if isinstance(item, dict):
                lineas_item = _yaml_lines(item, indent + 2)
                prefijo = " " * (indent + 2)
                if lineas_item and lineas_item[0].startswith(prefijo):
                    lineas.append(f"{espacio}- {lineas_item[0][len(prefijo):]}")
                    lineas.extend(lineas_item[1:])
                else:
                    lineas.append(f"{espacio}-")
                    lineas.extend(lineas_item)
            elif isinstance(item, list):
                lineas.append(f"{espacio}-")
                lineas.extend(_yaml_lines(item, indent + 2))
            else:
                lineas.append(f"{espacio}- {_yaml_scalar(item)}")
        return lineas

    return [f"{espacio}{_yaml_scalar(value)}"]


def dict_a_yaml(data):
    return "\n".join(_yaml_lines(data)) + "\n"
