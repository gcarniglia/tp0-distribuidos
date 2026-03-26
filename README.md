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
