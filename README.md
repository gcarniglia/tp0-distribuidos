# Ejercicio 1 — Generador de Docker Compose

## Cambios realizados

- Se añadió el script `generar-compose.sh` en la raíz del proyecto. Este script genera un archivo de Docker Compose con una cantidad configurable de clientes.
- Los nombres de los containers generados siguen la convención `client1`, `client2`, ..., `clientN`.
- El script permite mantener una plantilla de servicios y producir un `docker-compose` específico para pruebas con múltiples clientes sin editar manualmente el YAML.

---

## Detalles del script `generar-compose.sh`

- Ubicación: raíz del repositorio (`./generar-compose.sh`).
- Uso: `./generar-compose.sh <archivo-salida> <cantidad-de-clientes>`.
- Ejemplo: `./generar-compose.sh docker-compose-dev.yaml 5` generará un compose con 5 clientes llamados `client1`..`client5`.
-- Implementación: el script llama al generador `compose_generator` incluido en el repo (se invoca como `python3 -m compose_generator <archivo-salida> <cantidad>`). El generador produce un YAML válido incluyendo servicios `server` y múltiples `clientX` con los montajes/variables necesarias.

---

## Requisitos y convenciones

- El `docker-compose` generado mantiene los volúmenes y redes del proyecto base.
- Los clientes generados usan la misma imagen y configuración base, diferenciándose por nombre y variables de entorno.
- El script es idempotente: sobreescribe el archivo de salida si ya existe (advertir al usuario antes de sobrescribir si lo desea).

---

## Ejecución

Generar un compose con 5 clientes:

```bash
./generar-compose.sh docker-compose-dev.yaml 5
```

Arrancar el entorno generado:

```bash
make docker-compose-up
```

Ver logs del compose:

```bash
make docker-compose-logs
```

Detener y limpiar:

```bash
make docker-compose-down
```
