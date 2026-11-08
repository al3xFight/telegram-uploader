# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

## [1.2.0] - 2026-11-07

### Corregido
- `--borrar-local` ya no provoca `FileNotFoundError` ni interrumpe la cola: la clave del archivo
  se calcula antes de subirlo.

### Añadido
- Pruebas automatizadas con `pytest` (38 pruebas, con un cliente de Telegram simulado).
- Análisis estático con `ruff` y su configuración (`ruff.toml`).
- Documentación: `README.md`, `ARQUITECTURA.md` y este registro de cambios.
- `herramientas/contexto.py`: genera el contexto del proyecto para pegar a un asistente de IA.
- Ejecución como paquete: `python -m telegram_uploader`.
- `requirements.txt` y `requirements-dev.txt`.

### Cambiado
- El código se reorganizó del archivo único al paquete `telegram_uploader` (8 módulos).
- `subir_archivo` pasó de 11 parámetros a 3 (`ContextoSubida`, `OpcionesSubida`, `ruta`).
- El idioma se gestiona con la clase `Traductor`; se eliminó la variable global.
- `main()` se dividió en funciones de una sola responsabilidad.
- Las excepciones silenciadas se reemplazaron por excepciones específicas y registro de depuración.
- Se dejó de usar una función privada de Telethon (`helpers._maybe_await`).

### Seguridad
- `.gitignore` excluye `config.json`, los archivos de sesión de Telegram y `subidos.json`.

## [1.1.0] - línea base

Código original, conservado sin modificaciones en `referencia/subir_a_telegram.original.py`
(etiqueta de git `v1.1.0-original`).
