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

## 6. Registro de riesgos

Escala: probabilidad (P) e impacto (I) de 1 a 3. Exposición = P × I.

| ID | Riesgo | P | I | Exp. | Estrategia | Respuesta / mitigación | Señal de alerta |
|----|--------|---|---|------|------------|------------------------|-----------------|
| R1 | Filtración de `api_hash` o de la sesión de Telegram al repositorio | 2 | 3 | 6 | Mitigar | `.gitignore` excluye `config.json` y `*.session`; `enmascarar()` en pantalla; revisar `git status` antes de cada commit | `git status` muestra esos archivos |
| R2 | Pérdida de archivos del usuario por `--borrar-local` | 1 | 3 | 3 | Mitigar | Invariante 1: solo se borra tras subida confirmada; prueba automatizada; `--dry-run` recomendado | Un archivo desaparece sin registro en `subidos.json` |
| R3 | Telegram limita o bloquea la cuenta por subir demasiado | 2 | 3 | 6 | Mitigar | Manejo de `FloodWait`, pausas aleatorias, paralelismo por defecto en 1 | Mensajes de espera frecuentes |
| R4 | Una actualización de Telethon rompe el programa | 2 | 2 | 4 | Mitigar | No usar funciones privadas (invariante 7); CI con pytest detecta roturas | CI en rojo tras actualizar |
| R5 | Dependencias sin versión fija hacen que el CI falle o el programa cambie sin avisar | 2 | 2 | 4 | Mitigar | Versiones fijadas con `==` en `requirements.txt` y `requirements-dev.txt`; `cryptg` varía según la versión de Python; se actualizan solo a propósito y con el CI en verde | CI rojo sin que cambie el código |
| R6 | Código incorrecto generado por IA (claves o firmas inventadas) | 3 | 2 | 6 | Mitigar | Proceso de `GUIA_DESARROLLO.md`: contexto completo, checklist de verificación, pruebas antes de aceptar | Prueba nueva falla; clave i18n inexistente |
| R7 | El proyecto depende de una sola persona | 2 | 2 | 4 | Mitigar | Documentación (`ARQUITECTURA.md`, guía, plan) y contexto generable para IA | Nadie más puede ejecutar o modificar el proyecto |
| R8 | Falta `ffmpeg` y se pierden miniaturas y orden por metadata | 2 | 1 | 2 | Aceptar | Es opcional: el programa avisa y degrada con elegancia | Aviso de entorno al iniciar |
| R9 | Telegram cambia sus reglas para cuentas de usuario o la API | 1 | 3 | 3 | Aceptar | Fuera de nuestro control; se vigila y se documenta | Cambios anunciados por Telegram o Telethon |

**Priorización:** atender primero R1, R3 y R6 (exposición 6).
**Revisión:** se revisa este registro al cerrar cada versión nueva.

## 7. Método de trabajo

El proyecto combina tres niveles:

1. **Fases (reingeniería de software):** inventario, ingeniería inversa, mantenimiento
   correctivo, reestructuración de código, reestructuración de documentación e
   ingeniería directa. Actualmente se encuentra en ingeniería directa.
2. **Gestión del trabajo (Kanban):** tablero en GitHub Projects con columnas Todo,
   In Progress y Done. Límite de trabajo en curso (WIP): una sola tarjeta en
   In Progress. Cada elemento del backlog (sección 4) tiene un Issue enlazado y el
   orden de Todo respeta la prioridad.
3. **Prácticas técnicas (Extreme Programming):** pruebas antes del código,
   refactorización continua, integración continua y cambios pequeños.

Una tarjeta pasa a Done solo cuando cumple la definición de terminado: código,
pruebas en verde, CI en verde y documentación actualizada.