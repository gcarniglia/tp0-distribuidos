# Ejercicio 3 — Validación del echo server

## Cambios realizados

- Se agregó el script de validación `validar-echo-server.sh` en la raíz del proyecto.
- El script arranca el entorno con Docker Compose si es necesario, crea un contenedor efímero que ejecuta `netcat` dentro de la misma red del compose y valida que el servidor responda con el mismo mensaje enviado (echo).
- Si la validación es exitosa el script imprime: `action: test_echo_server | result: success`; en caso contrario: `action: test_echo_server | result: fail`.

---

## Detalles del script `validar-echo-server.sh`

- Ubicación: raíz del repositorio (`./validar-echo-server.sh`).
- Requisitos: Docker y Docker Compose en la máquina _host_. No es necesario instalar `netcat` en el host.
- Comportamiento:
  - Se conecta a la red interna creada por Docker Compose.
  - Inicia un contenedor temporal que ejecuta `nc` apuntando al servicio `server` por nombre de host y puerto configurado.
  - Envía un string de prueba y espera recibir exactamente el mismo string.
  - Sale con código 0 en success y distinto de 0 en fail.

---

## Resumen funcional

- Servidor: echo server (responde con el mismo payload recibido). El servidor continúa corriendo dentro del compose.
- Cliente: no es requerido para la validación; la prueba usa `netcat` desde un contenedor de validación.

---

## Ejecución

Arrancar el entorno de desarrollo:

```bash
make docker-compose-up
```

Ejecutar la validación del echo server (script incluido):

```bash
./validar-echo-server.sh
```

Ver logs del compose:

```bash
make docker-compose-logs
```

Detener y limpiar:

```bash
make docker-compose-down
```
