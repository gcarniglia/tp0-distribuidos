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
