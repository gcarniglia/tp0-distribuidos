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
