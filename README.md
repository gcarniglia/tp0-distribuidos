# Ejercicio 4 — Cierre Graceful

## Objetivo

Implementar cierre ordenado ante `SIGTERM` y preservar el cierre correcto de recursos (sockets, files, hilos).

---

## Cambios realizados

Durante la realización del ejercicio 4, y en vistas de lo que se me venía encima, tome la iniciativa
de plantear un protocolo directamente. Mi protocolo se llama *Smile Protocol*.

Luego, este protocolo se implemento para el echo server, y se agregaron los mensajes `SHUTDOWN`, cuyo objetivo es notificar desde el servidor al cliente (o viceversa) del final de la comunicación.

---

## Smile Protocol

Consiste de un header y un payload.

- Header: `:)<TYPE> <LEN>:(\n`. "Arranca con una sonrisa" `:)` y lo finaliza "triste" `:(`
- Payload: variable según mensaje, pero su longitud es conocida a traves del header

Estructura final: `:)<TYPE> <LEN>:(\n<payload>`.

Se implementaron mensajes efectivos ya: `SHUTDOWN`, `ECHO`, `OK`, `ERROR`.

---

### Smile Protocol aplicado al SHUTDOWN: Cliente

- Manejo de `SIGTERM` en `client/common/client.go`.
- Envía `SHUTDOWN` unilateral antes de cerrar la conexión (`app_client.SendShutdown`), sin esperar ACK del servidor.
- Uso de `WriteAll`/`ReadExactly` y lectura incremental de header para evitar short write/read.
- Logs relevantes: `action: receive_shutdown`, `action: loop_finished | result: success | client_id: X`.

### Smile Protocol aplicado al SHUTDOWN: Servidor

- Handler de `SIGTERM` en `server/common/server.py` que marca `shutdown_requested` y cierra el listener.
- Worker por conexión (thread) que procesa frames y atiende `SHUTDOWN` recibido como cierre protocolar.
- En apagado envía `SHUTDOWN` a conexiones activas a los clientes, cierra conexiones y espera (`join`) a los workers.
- Manejo de payloads demasiado grandes (responde `ERROR` y descarta `LEN` bytes) y errores de protocolo.
- Si la conexión termina por EOF sin `SHUTDOWN`, se registra como cierre no protocolar.
- Logs relevantes: `action: accept_connections`, `action: receive_message`, `action: shutdown_received`, `action: sigterm_received`, `action: close_listener`, `action: close_connection`, `action: join_worker`.

## Flujo de apagado (implementado)

1. Proceso recibe `SIGTERM`.
2. Servidor: marca `shutdown_requested`, cierra listener, envía `SHUTDOWN` a conexiones activas, cierra conexiones y espera a que terminen los threads.
3. Cliente: detecta la señal, envía `SHUTDOWN` unilateral, cierra socket y finaliza; registra `loop_finished`.

---

## Manejo de errores (implementado)

- Si `LEN > 8192`: servidor lanza `PayloadTooLargeError`, responde `ERROR` y descarta `LEN` bytes.
- Header inválido o `LEN` mal formado: servidor responde `ERROR` y cierra la conexión cuando corresponde.
- Short read/write evitados con `ReadExactly` / `WriteAll`.

---

## Logs relevantes

- Cliente:
  - `action: receive_message | result: success | client_id: X | msg: ...`
  - `action: receive_shutdown | result: success | client_id: X`
  - `action: sigterm_received | result: success | client_id: X`
  - `action: send_shutdown | result: success | mode: unilateral | client_id: X`
  - `action: close_connection | result: success | client_id: X`
  - `action: loop_finished | result: success | client_id: X`

- Servidor:
  - `action: accept_connections | result: in_progress / success | ip: ...`
  - `action: receive_message | result: success | ip: ... | msg: ...`
  - `action: shutdown_received | result: success | ip: ...`
  - `action: sigterm_received | result: success`
  - `action: close_listener | result: in_progress / success`
  - `action: close_connection | result: in_progress / success | ip: ... | reason: ...`
  - `action: join_worker | result: in_progress / success / timeout`

---

## Consideraciones técnicas

- Límite de payload: 8192 bytes.
- Lectura incremental de header: `ReadUntilHeaderTerminator` / `read_until_header_terminator`.
- Configs montadas por volumen (`./server/config.ini`, `./client/config.yaml`) para evitar rebuild al cambiar parámetros.

---

## Ejecución

```bash
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

Prueba rápida de echo (usa la red interna, no requiere nc en host):

```bash
./validar-echo-server.sh
```


# ANEXO: Smile Protocol

Aquí se explica **cómo se intercambian mensajes** entre cliente y servidor en la implementación actual del TP0 (ya finalizado)

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
