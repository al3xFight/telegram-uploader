# Plan del proyecto: Telegram Uploader

## 1. Visión del producto
Para personas que necesitan respaldar videos y archivos grandes en un canal privado
de Telegram, Telegram Uploader es una herramienta de línea de comandos que sube los
archivos con la cuenta personal del usuario, sin duplicar lo ya enviado y sin exponer
sus credenciales. A diferencia de subir a mano, es repetible, reanudable entre
ejecuciones y está documentada.

## 2. Alcance
**Incluye:** subida a un canal o grupo privado, subida por fragmentos en paralelo,
miniaturas, orden cronológico, registro de subidos, interfaz en español e inglés,
simulación con `--dry-run`.

**No incluye (límites):**
- Descargar archivos desde Telegram.
- Interfaz gráfica.
- Subir a varios destinos en una sola ejecución.
- Usar bots (usa la cuenta del usuario).

## 3. Restricciones
- Depende de Telethon y de los límites de velocidad de Telegram (`FloodWait`).
- Requiere `api_id` y `api_hash` del propio usuario.
- Python 3.10 o superior.
- Los datos sensibles nunca deben entrar al repositorio (`config.json`, `*.session`).
- Equipo de una persona: capacidad limitada.

## 4. Product backlog (ordenado por prioridad)

| # | Elemento | Tipo | Prioridad |
|---|----------|------|-----------|
| 1 | Opción `--limite N` (subir como máximo N archivos por ejecución) | Función | Alta |
| 2 | Resolver los 8 hallazgos de `ruff` y hacer que bloquee en CI | Deuda técnica | Alta |
| 3 | Dividir `subir_archivo` (complejidad 18) | Deuda técnica | Media |
| 4 | Simplificar `menu_configuracion` con una tabla de opciones | Deuda técnica | Media |
| 5 | Reanudar subidas por fragmentos | Función | Baja |
| 6 | Evitar que operaciones de archivo bloqueen el bucle asíncrono | Deuda técnica | Baja |

## 5. Gestión de solicitudes de cambio
1. Se registra la petición como un elemento nuevo del backlog (qué, por qué).
2. Se evalúa: ¿entra en el alcance? ¿respeta las invariantes de `ARQUITECTURA.md`?
3. Se le asigna prioridad y se ubica en el backlog.
4. Si se acepta, se implementa con `GUIA_DESARROLLO.md` (prueba, código, documentación, versión).
5. Se registra el resultado en `CHANGELOG.md`.