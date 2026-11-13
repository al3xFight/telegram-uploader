# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

## [1.3.1] - 2026-11-13

### Añadido
- `ErrorDeUso` (`errores.py`): la lógica lanza excepciones con la clave del texto en lugar de usar `sys.exit`.
- `ReporteProgreso` (`progreso.py`): interfaz con la que la lógica informa el avance de las subidas.
- `servicio.py`: flujo completo de subida (`Solicitud`, `CallbacksLogin`, `ResultadoSubida`), que acepta funciones propias para el inicio de sesión de Telegram.
- 12 pruebas nuevas (63 en total).

### Cambiado
- Separación de la lógica y la consola, sin cambio visible para quien usa la línea de comandos: `subida.py` ya no usa `rich` y `cli.py` pasa a ser un cliente del servicio. Es el requisito previo de la interfaz gráfica (#9).

## [1.3.0] - 2026-11-12

### Añadido
- Reanudación de subidas por fragmentos dentro de la misma ejecución: si un intento falla, el reintento envía solo los fragmentos que faltan, con el mismo identificador de archivo, y la barra de progreso arranca en lo ya subido.
- Mensajes en español e inglés al reanudar y cuando Telegram ya no conserva los fragmentos.
- 6 pruebas nuevas (51 en total), incluida una que comprueba que los fragmentos enviados reproducen el archivo original.

### Cambiado
- Si un fragmento falla, se cancelan los pendientes en lugar de dejarlos subiéndose en segundo plano.
- Si Telegram ya no conserva fragmentos de un archivo, la subida se reinicia desde cero con un identificador nuevo.

## [1.2.1] - 2026-11-10

### Cambiado
- Las operaciones de archivo (tamaño, lectura de fragmentos y borrado local) se ejecutan en hilos con `asyncio.to_thread` y ya no bloquean el bucle asíncrono.
- `subir_archivo` se dividió en funciones de una sola responsabilidad (`preparar_medios`, `crear_callback_progreso`, `simular_subida`, `enviar_con_reintentos` y `finalizar_subida`).
- `menu_configuracion` usa una tabla de opciones (`EDICIONES`) en lugar de ramas encadenadas.
- `ruff` bloquea la integración continua; los hallazgos pasaron de 8 a 0.

### Añadido
- 7 pruebas nuevas (45 en total).

## [1.2.0] - 2026-11-07

### Añadido
- Pruebas automatizadas con `pytest`: 38 pruebas, con un cliente de Telegram simulado.
- Documentación: `README.md`, `ARQUITECTURA.md` y este registro de cambios.
- `herramientas/contexto.py`: genera el contexto del proyecto para pegar a un asistente de IA.
- Ejecución como paquete: `python -m telegram_uploader`.
- `requirements-dev.txt`.
- Integración continua con GitHub Actions (ruff y pytest en Python 3.10 y 3.12).
- Versiones fijas de dependencias; `cryptg` incluido según la versión de Python.
- `PLAN_DEL_PROYECTO.md`: visión, alcance, restricciones, backlog, registro de riesgos y método de trabajo.
- `GUIA_DESARROLLO.md`: guía para agregar funciones, con apoyo de IA.
- Plantilla de solicitud de cambio (`.github/ISSUE_TEMPLATE/`).
- Licencia MIT (`LICENSE`).

### Cambiado
- La documentación indica cómo instalar ffmpeg.

### Seguridad
- `.gitignore` ampliado para excluir también archivos de contexto y de trabajo.

## [1.1.6] - 2026-11-07

### Cambiado
- El código se reorganizó del archivo único al paquete `telegram_uploader` (8 módulos), con reglas de dependencia entre módulos.
- `main()` se dividió en funciones de una sola responsabilidad.
- Advertencias de ruff: de 19 a 8 (la configuración se ajustó en este paso: `E501` ignorado en `i18n.py` y reglas relajadas en pruebas).

## [1.1.5] - 2026-11-07
(incluye la etiqueta `v1.1.4`, que apunta al mismo commit)

### Cambiado
- El idioma se gestiona con la clase `Traductor`; se eliminó la variable global.
- Advertencias de ruff: de 29 a 24.

## [1.1.3] - 2026-11-07

### Cambiado
- `subir_archivo` pasó de 11 parámetros a 3 (`ContextoSubida`, `OpcionesSubida`, `ruta`).
- Advertencias de ruff: de 31 a 29.

## [1.1.2] - 2026-11-07

### Cambiado
- Se atendieron hallazgos de `ruff`: de 53 a 31 advertencias.
- Las excepciones silenciadas se reemplazaron por excepciones específicas y registro de depuración.
- Se dejó de usar una función privada de Telethon (`helpers._maybe_await`).

## [1.1.1] - 2026-11-07

### Corregido
- `--borrar-local` ya no provoca `FileNotFoundError` ni interrumpe la cola: la clave del archivo
  se calcula