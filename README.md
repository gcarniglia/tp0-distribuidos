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
