# Ejercicio 6 — Procesamiento por lotes (BATCH)

Como se planteó toda la estructura de capas de transporte/protocolo/aplicación en el punto anterior, aquí la solución es mas a nivel aplicación.

Se implementó el flujo de apuestas por lotes `BATCH`. El mensaje del tipo `BATCH` enviado por el cliente tiene la estructura siguiente:

```text
:)BATCH 1116:(
agency_id=1
count=25
data:
Sebastian Alejandro,Loreto,26486922,1985-08-08,8130
Dylan Ezequiel,Sberna,27155519,1994-01-07,6843
...
```

El mensaje enviado por el servidor tiene esta estructura, dependiendo de si es OK o no el batch de origen:

```text
:)OK 0:(

```

```text
:)ERROR 20:(
batch_count_mismatch
```

El acceso al archivo resultante se realiza a traves de la variable

Resumen de la implementación realizada:

- El cliente lee apuestas desde su archivo `/.data/agency-{N}.csv`, arma lotes según `batch.maxAmount` y envía payload textual con `agency_id`, `count` y sección `data:` usando Smile Protocol (`TYPE=BATCH`).
- El servidor parsea y valida el batch completo; si todas las apuestas son válidas persiste con `store_bets(...)` y responde `OK`; si alguna falla responde `ERROR` y no persiste parcial.
- Logs esperados:
  - Servidor éxito: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`
  - Servidor error: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`

Archivos relevantes:
- Cliente: [client/main.go](client/main.go), [client/common/client.go](client/common/client.go) y [client/common/application/batch_operation.go](client/common/application/batch_operation.go)
- Servidor: [server/common/application/app_server.py](server/common/application/app_server.py)
- Generador de compose: [compose_generator/compose.py](compose_generator/compose.py) (inyecta `CLI_ID` y monta `./.data/agency-N.csv` en `/.data/agency-N.csv`)

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

3. Ver los logs y buscar las entradas `apuesta_recibida`:

```bash
make docker-compose-logs
```

4. Si se desea ver mas en conciso si, al levantar las 5 imagenes se procesaron la cantidad de lineas correcta sugiero lo siguiente:

```bash
docker exec -it server sh
```

Dentro del contenedor del servidor, ejecutar esto si se busca contar el total de lineas procesadas por el servidor:

```bash
wc -l bets.csv
```

Si se quiere ver la cantidad de lineas por cliente, se puede hacer:

```bash
grep '^1' bets.csv | wc -l
```

Donde el 1 representa al id de la agencia de lotería.

Nota: Aunque específicamente no se aclara, considero que el dataset.zip se encuentra ya descomprimido en `./.data/*.csv`, con cada csv de cada agencia allí.
