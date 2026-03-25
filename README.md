# Ejercicio 2 — Configuración montada por volúmenes (sin rebuild)

## Cambios realizados

- Se modificaron las definiciones de despliegue para montar los archivos de configuración desde el host hacia los containers de forma que cambios en configuración no requieran reconstruir las imágenes.
- Archivos de configuración principales montados:
  - `server/config.ini` → configuraciones del servidor Python
  - `client/config.yaml` → configuraciones del cliente Go
- Con esto, editar `server/config.ini` o `client/config.yaml` en el proyecto aplica los cambios al reiniciar el servicio dentro del compose, sin necesidad de `docker build`.

---

## Detalles técnicos

- Montajes: los servicios `server` y `client` usan volúmenes para montar los archivos de configuración del host en las rutas que las aplicaciones esperan dentro del container (por ejemplo `/app/config.ini` o `/app/config.yaml`).
- Ejemplo resumido de montaje en `docker-compose`:

  - `volumes:`
    - `./server/config.ini:/app/config.ini:ro`
    - `./client/config.yaml:/app/config.yaml:ro`

- Lectura en caliente: para aplicar cambios de configuración basta con reiniciar el servicio (`docker compose restart <service>`), no hace falta reconstruir la imagen si sólo cambian parámetros.
- Permisos: los archivos montados deben ser legibles por el usuario que ejecuta la aplicación dentro del container.

---

## Buenas prácticas para desarrollo

- Mantener los archivos de configuración fuente (`server/config.ini`, `client/config.yaml`) en el árbol del proyecto para facilitar edición y versionado.
- Reiniciar únicamente el servicio afectado cuando sea posible:

```bash
docker compose restart server
```

o

```bash
docker compose restart client
```

- Si se realizan cambios en dependencias o en los `Dockerfile` (código compilado, librerías), entonces será necesario reconstruir la imagen con `make docker-image` o `docker compose build`.

---

## Alcance y limitaciones

- Alcance: permite ajustar parámetros (timeouts, logging, límites de payload, variables de entorno) sin rebuild.
- Limitación: cambios en binarios, dependencias o rutas internas requieren reconstrucción de imágenes.

---

## Ejecución y flujo recomendado

1. Arrancar el entorno de desarrollo:

```bash
make docker-compose-up
```

2. Editar la configuración en el host, por ejemplo `server/config.ini`.

3. Aplicar cambios reiniciando sólo el servicio necesario:

```bash
docker compose restart server
```

4. Ver logs:

```bash
make docker-compose-logs
```

5. Detener y limpiar:

```bash
make docker-compose-down
```
