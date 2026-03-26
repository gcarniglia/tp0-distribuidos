# Ejercicio 8 — Concurrencia en servidor

Para el ej8 se extendió el servidor para aceptar y procesar conexiones en paralelo, manteniendo consistencia de estado y persistencia compartida.
Esto ya existía desarrollado en el ejercicio 7. El concepto se mantuvo presente a lo
largo de varios ejercicios. Pero fue durante el desarrollo de éste que se encontraron
algunas consideraciones que, si bien no eran relevantes para las consignas de ejercicios
previos (porque no lo pedían), sí es importante en este:

- _storage_lock es un Lock de la capa de aplicacion que se utiliza para la escritura concurrente en el archivo resultante (ejecutando store_bets sin incurrir en condiciones de carrera)
- ServerState es una clase de la capa de aplicación del servidor que se utiliza para manejar la logica del negocio de las agencias de lotería.

## Diseño implementado

### Modelo de concurrencia

- Se utiliza un modelo **thread-per-connection**: por cada conexión aceptada se crea un hilo worker que procesa mensajes de ese cliente en loop.
- El hilo principal queda liberado para seguir aceptando nuevas conexiones concurrentemente.

### Estado compartido y sincronización

- Estado de sorteo (fin de agencias y habilitación de consulta de ganadores):
  - Se mantiene en `ServerState` con `Lock + Condition`.
  - `END_AGENCY` marca agencia finalizada.
  - `GET_WINNERS` espera con `wait_for_draw()` hasta que todas las agencias hayan terminado.
- Persistencia compartida de apuestas (`bets.csv`):
  - `store_bets(...)` y `load_bets()` no son thread-safe por sí solas.
  - Se protege su acceso con lock en `AppServer` para evitar condiciones de carrera entre hilos.

### Shutdown graceful en concurrencia

- El servidor usa `_shutdown_requested` (`threading.Event`) para coordinar el ciclo de vida entre hilos.
- Al recibir `SIGTERM`:
  1. se marca shutdown y se detiene `accept()`;
  2. se envía mensaje `SHUTDOWN` a conexiones activas;
  3. se cierran sockets y se espera finalización de workers.
- Si falla el envío a un cliente, se loguea el error y se continúa con el cierre del resto.

## Archivos relevantes de ej8

- Servidor concurrente / lifecycle: [server/common/server.py](server/common/server.py)
- Estado de aplicación sincronizado: [server/common/application/state.py](server/common/application/state.py)
- Lógica de aplicación y lock de persistencia: [server/common/application/app_server.py](server/common/application/app_server.py)

## Validación sugerida

1. Regenerar compose y levantar entorno:

```bash
./generar-compose.sh docker-compose-dev.yaml 5
make docker-image
make docker-compose-up
```

2. Verificar en logs que el servidor acepta conexiones de múltiples clientes y procesa mensajes intercalados:

```bash
make docker-compose-logs
```

3. Detener con shutdown de compose y verificar cierre ordenado:

```bash
make docker-compose-down
```

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
