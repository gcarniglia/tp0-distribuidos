# Ejercicio 7 — Cierre por agencia y consulta de ganadores

Como se planteó toda la estructura de capas de transporte/protocolo/aplicación en los puntos anteriores, aquí la solución es principalmente de aplicación y sincronización.

Se implementó el flujo completo de cierre de carga por agencia (`END_AGENCY`) y consulta de ganadores (`GET_WINNERS`).
El mensaje `END_AGENCY` enviado por el cliente tiene la estructura siguiente:

```text
:)END_AGENCY 11:(
agency_id=1
```

El mensaje `GET_WINNERS` enviado por el cliente tiene la estructura siguiente:

```text
:)GET_WINNERS 11:(
agency_id=1
```

Luego del sorteo, el mensaje `WINNERS` enviado por el servidor tiene esta estructura:

```text
:)WINNERS 49:(
agency_id=1
count=3
data:
26486922
27155519
30111222
```

En los casos de acuse estándar, el servidor responde:

```text
:)OK 0:(

```

Si se solicita GET_WINNERS, y todavía no se realizó el sorteo, se dejará esperando a este cliente hasta que ocurra el sorteo. Esto no implica bloquear el servidor puesto que hay un sistema de multithreading ya implementado (que de todas maneras, se mejoró en el ej8)

Si el cliente no tiene ganadores de lotería, se responde con el mensaje WINNERS igualmente:

```text
:)WINNERS 20:(
agency_id=3
count=0
```

Como consideración importante, se separó la lógica de negocio de la agencia de lotería de la del servidor (`ServerState`).

Resumen de la implementación realizada:

- El cliente, al terminar de enviar todos sus batches, envía `END_AGENCY`, luego consulta `GET_WINNERS`, parsea la respuesta `WINNERS` y loguea: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.
- El servidor registra agencias finalizadas con estado compartido sincronizado (`Lock + Condition`) y recién habilita el sorteo cuando finalizan todas las agencias esperadas.
- Al completarse todas las agencias, el servidor loguea: `action: sorteo | result: success`.
- Para `GET_WINNERS`, el servidor espera a que el sorteo esté habilitado, usa `load_bets(...)` + `has_won(...)`, y responde solo los DNIs ganadores de la agencia consultante (sin broadcast global).

Archivos relevantes:
- Cliente: [client/common/client.go](client/common/client.go) y [client/common/application/winners_operation.go](client/common/application/winners_operation.go)
- Servidor: [server/common/application/app_server.py](server/common/application/app_server.py) y [server/common/application/state.py](server/common/application/state.py)
- Entry point servidor: [server/main.py](server/main.py)
- Generador de compose: [compose_generator/compose.py](compose_generator/compose.py) (inyecta `SERVER_TOTAL_AGENCIES` y `CLI_ID`)

Ejecución:

1. Regenerar compose con 5 agencias:

```bash
./generar-compose.sh docker-compose-dev.yaml 5
```

2. Reconstruir imágenes y levantar el compose:

```bash
make docker-image
make docker-compose-up
```

3. Ver los logs y buscar las entradas `sorteo` y `consulta_ganadores`:

```bash
make docker-compose-logs
```

Nota: Se asume el dataset de agencias disponible en `./.data/dataset/agency-N.csv` para cada cliente, montado en `/.data/agency-N.csv` dentro del contenedor.