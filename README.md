# Ejercicio 5 — Apuestas (BET)

Como se planteó toda la estructura de capas de transporte/protocolo/aplicación en el punto anterior, aquí la solución es mas a nivel aplicación.

Se implementó el flujo de apuesta individual `BET`. El mensaje del tipo `BET` enviado por el cliente tiene la estructura siguiente:

```text
:)BET 102:(
agency_id=1
nombre=Santiago Lionel
apellido=Lorca
documento=30904465
nacimiento=1999-03-17
numero=7574
```

El mensaje enviado por el servidor tiene esta estructura, dependiendo de si es OK o no el mensaje de origen:

```text
:)OK 0:(

```

```text
:)ERROR 27:(
missing_bet_field_documento
```

Resumen de la implementación realizada:

- El cliente envía una apuesta serializada en texto (`key=value` por línea) usando el Smile Protocol(`TYPE=BET`).
- El servidor parsea la apuesta, valida campos, persiste con la función `store_bets(...)` provista y responde `OK` o `ERROR`.
- Logs esperados:
  - Cliente: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`
  - Servidor: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`

Archivos relevantes:
- Cliente: [client/main.go](client/main.go) y [client/common/application/bet_operation.go](client/common/application/bet_operation.go)
- Servidor: [server/common/application/app_server.py](server/common/application/app_server.py)
- Generador de compose: [compose_generator/compose.py](compose_generator/compose.py) (inyecta variables de apuesta por cliente)

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

3. Ver los logs y buscar las entradas `apuesta_enviada` / `apuesta_almacenada`:

```bash
make docker-compose-logs
```
4. Para visualizar el archivo resultante bets.csv se puede hacerlo ejecutando:

```bash
docker exec -it server sh
```

Y luego dentro del contenedor ejecutar:

```bash
cat bets.csv
```

Para visualizar la ejecución de las apuestas de las 5 agencias de lotería procesadas.


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
