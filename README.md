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

El acceso al archivo resultante (en `store_bets()`) se realiza a traves de la variable `self._storage_lock` de la capa de aplicación del servidor.

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

# ANEXO: Smile Protocol

Aquí se explica **cómo se intercambian mensajes** entre cliente y servidor en la implementación actual del TP0

---

## 1) Estructura del mensaje

Todo mensaje viaja como un paquete. El mismo contendrá un header (que comienza "feliz" `:)` y termina "triste" `:(`) y luego un payload en bytes, con un formato según el tipo de mensaje:

```text
:)<TYPE> <LEN>:(\n<PAYLOAD>
```

Donde:

- `TYPE`: tipo de mensaje (`BET`, `BATCH`, `END_AGENCY`, `GET_WINNERS`, `WINNERS`, `OK`, `ERROR`, `SHUTDOWN`, `ECHO`).
- `LEN`: cantidad de bytes exacta de `PAYLOAD`.
- Límite de payload: `8192` bytes (8Kb).

### Ejemplo real de mensaje

```text
:)ECHO 12:(
Hola Mundo!!
```

(El payload tiene 12 bytes).

---

## 2) Patrón de intercambio

Para casi todos los mensajes de aplicación, el flujo es request/response:

1. Cliente codifica mensaje y lo envía.
2. Servidor decodifica, valida y ejecuta lógica.
3. Servidor responde con:
   - `OK` (éxito), o
   - `ERROR` (fallo de formato/negocio), o
   - `WINNERS` (respuesta específica de consulta), o
   - `SHUTDOWN` (apagado de la conexión con ese cliente).

La conexión es **persistente** durante la sesión del cliente.

---

## 3) Dinámica por tipo de mensaje

## `BET`

- Cliente envía una apuesta.
- Payload esperado:

```text
agency_id=<ID>
nombre=<NOMBRE>
apellido=<APELLIDO>
documento=<DNI>
nacimiento=<YYYY-MM-DD>
numero=<NUMERO>
```

- Si el batch es válido: servidor persiste todo y responde `OK`.
- Si hay inconsistencia (ej. formato inválido): responde `ERROR`.

### Ejemplo

**Request**

```text
:)BATCH 88:(
agency_id=1
count=2
data:
Ana,Perez,123,1990-01-01,7574
Luis,Gomez,456,1988-02-02,1111
```


## `BATCH`

- Cliente envía apuestas por lotes.
- Payload esperado:

```text
agency_id=<ID>
count=<N>
data:
nombre,apellido,documento,nacimiento,numero
...
```

- Si el batch es válido: servidor persiste todo y responde `OK`.
- Si hay inconsistencia (ej. `count` no coincide, formato inválido): responde `ERROR`.

### Ejemplo

**Request**

```text
:)BATCH 88:(
agency_id=1
count=2
data:
Ana,Perez,123,1990-01-01,7574
Luis,Gomez,456,1988-02-02,1111
```

**Response (éxito)**

```text
:)OK 0:(
```

---

## `END_AGENCY`

- Cliente notifica que terminó de enviar apuestas de su agencia.
- Payload:

```text
agency_id=<ID>
```

- Respuesta: `OK`.
- Cuando el servidor recibe `END_AGENCY` de todas las agencias esperadas (`total_agencies`), marca sorteo completado y despierta consultas bloqueadas.

---

## `GET_WINNERS` y `WINNERS`

- Cliente consulta ganadores de su agencia.
- Payload:

```text
agency_id=<ID>
```

- Si el sorteo **todavía no está completo**, el servidor bloquea esta request para este cliente hasta que finalicen todas las agencias.
- Respuesta exitosa: `WINNERS` con cantidad y DNIs.

### Ejemplo de respuesta

```text
:)WINNERS 36:(
agency_id=1
count=2
data:
30904465
28000111
```

Si no hay ganadores:

```text
agency_id=1
count=0
data:
```

---

## `SHUTDOWN`

Hay dos usos distintos:

1. **Cliente -> servidor**: shutdown unilateral de esa conexión.
   - El servidor cierra esa conexión y **no envía respuesta**.

2. **Servidor -> clientes** (al apagar por SIGTERM):
   - Envía `SHUTDOWN` a conexiones activas y luego cierra.
   - El cliente, al recibir `SHUTDOWN`, corta su loop en forma graceful.

---

## `ECHO`

- Mensaje de prueba/simple round-trip.
- Request: `ECHO` con texto.
- Response típica: `OK` con el mismo payload.

---

## 4) Secuencia típica de una agencia

```text
Cliente                           Servidor
   | --- BATCH -----------------> |
   | <--------- OK -------------- |
   | --- BATCH -----------------> |
   | <--------- OK/ERROR -------- |
   | --- END_AGENCY ------------> |
   | <--------- OK -------------- |
   | --- GET_WINNERS -----------> |  (puede esperar)
   | <------- WINNERS ----------- |
   | --- SHUTDOWN --------------> |  (cierre de esa conexión)
```

---

## 5) Casos borde importantes

1. **Header inválido** (`:)`/`:(\n` mal formados, partes faltantes)
   - Servidor responde `ERROR` y cierra conexión.

2. **`TYPE` desconocido o inválido**
   - Falla el parseo del tipo.
   - Servidor responde `ERROR` y cierra conexión.

3. **`LEN` inválido** (no numérico o negativo)
   - Servidor responde `ERROR` y cierra conexión.

4. **Payload mayor a 8192 bytes**
   - En recepción del servidor: responde `ERROR`, descarta exactamente `LEN` bytes y continúa.
   - En codificación local (cliente/servidor): se rechaza antes de enviar.

5. **Header demasiado largo (>4096 bytes)**
   - Se considera error de protocolo.
   - Servidor responde `ERROR` y cierra conexión.

6. **`BATCH` inconsistente** (`count` != cantidad de líneas `data`, CSV mal formado, campos vacíos)
   - Servidor responde `ERROR` (sin éxito parcial del lote).

7. **`GET_WINNERS` antes de completar sorteo global**
   - La request queda bloqueada hasta que todas las agencias envíen `END_AGENCY`.

8. **EOF inesperado durante header/payload**
   - Se trata como cierre abrupto o mensaje truncado.
   - Se cierra conexión.

9. **`END_AGENCY` repetido para la misma agencia**
   - Se maneja con conjunto interno (`set`), no vuelve a incrementar el conteo global.

---
