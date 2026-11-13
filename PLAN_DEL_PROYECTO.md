# Plan del proyecto: Telegram Uploader

## 1. Visión del producto
Para personas que necesitan respaldar videos y archivos grandes en un canal privado
de Telegram, Telegram Uploader es una herramienta de línea de comandos que sube los
archivos con la cuenta personal del usuario, sin duplicar lo ya enviado y sin incluir
sus credenciales en el código ni en el repositorio. A diferencia de subir a mano, es repetible,
retoma la cola pendiente entre ejecuciones y está documentada.

## 2. Alcance
**Incluye:** subida a un canal o grupo privado, subida por fragmentos en paralelo,
miniaturas, orden cronológico, registro de subidos, interfaz en español e inglés,
simulación con `--dry-run`. 
Asistente de configuración interactivo, reintentos y manejo de los límites de Telegram, y borrado opcional del archivo local tras una subida confirmada (`--borrar-local`).
Interfaz gráfica de escritorio con Flet (versión base: configuración, inicio de sesión y subida con progreso), además de la línea de comandos.

**No incluye (límites):**
- Descargar archivos desde Telegram.
- Subir a varios destinos en una sola ejecución.
- Usar bots (usa la cuenta del usuario).

## 3. Restricciones
- Depende de Telethon y de los límites de velocidad de Telegram (`FloodWait`).
- Requiere `api_id` y `api_hash` del propio usuario.
- Python 3.10 o superior.
- Los datos sensibles nunca deben entrar al repositorio (`config.json`, `*.session`).
- Equipo de una persona: capacidad limitada.
- Tamaño máximo por archivo: el que Telegram permite a las cuentas gratuitas (2 GB).

## 4. Backlog del producto

   La fuente de verdad del backlog son los Issues del repositorio, organizados en el tablero de GitHub Projects. La siguiente tabla se genera a partir de ellos y es una instantánea del 10 de noviembre de 2026.

| Issue | Elemento | Tipo | Prioridad | Estado |
|---|---|---|---|---|
| #2 | Opción --limite N: subir como máximo N archivos por ejecución | funcion | alta | Pendiente |
| #3 | Resolver los 8 hallazgos de ruff y hacer que bloquee en CI | deuda | alta | Cerrado |
| #4 | Dividir subir_archivo (complejidad 18) | deuda | media | Cerrado |
| #5 | Simplificar menu_configuracion con una tabla de opciones | deuda | media | Cerrado |
| #6 | Reanudar subidas por fragmentos (dentro de la misma ejecución) | funcion | baja | Cerrado |
| #7 | Evitar que operaciones de archivo bloqueen el bucle asíncrono | deuda | baja | Cerrado |
| #9 | Interfaz grafica de escritorio (Flet) | funcion | alta | En curso |
| #10 | Subir a varios canales o grupos en una misma ejecucion | funcion | baja | Pospuesta |
| #11 | Soporte para grupos con temas (por verificar que la API lo permita) | funcion | baja | Pospuesta |
| #12 | Operacion desde varios equipos (definir el manejo de la sesion de Telegram) | funcion | baja | Pospuesta |

Los elementos #10 a #12 son ideas de evolución que quedan fuera del alcance actual (sección 2). Se crean sus Issues cuando se planteen con detalle, mediante el proceso de la sección 5.

### Solicitudes de cambio resueltas

| Issue | Solicitud | Decisión | Motivo |
|---|---|---|---|
| #8 | Descargar los videos desde el canal | Rechazada | Fuera del alcance: la visión del producto es subir, no descargar |
| #9 | Interfaz gráfica de escritorio | Aceptada con condiciones | Mejora la usabilidad; condiciones: separar antes la lógica de la consola y mantener la GUI como dependencia opcional |

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
| R10 | Flet cambia su API o falla entre versiones (ej.: `flet pack` roto en Windows con la 1.1.2) | 3 | 2 | 6 | Mitigar | Versión fijada con `==`; empaquetado en entorno aislado con corrección controlada y plan B con PyInstaller | `flet pack` o la GUI fallan tras actualizar |
| R11 | El inicio de sesión de la GUI expone el código o la contraseña de 2FA | 1 | 3 | 3 | Mitigar | Campos ocultos; no guardar ni registrar esos valores | Aparecen en logs o archivos |
| R12 | Un antivirus marca el `.exe` como sospechoso | 2 | 2 | 4 | Mitigar | Publicar el hash SHA-256 y la forma de ejecutar desde el código fuente | Reportes de usuarios |
| R13 | La GUI crece sin control | 2 | 2 | 4 | Mitigar | Versión base mínima; todo lo demás pasa por solicitud de cambio | Aparecen pedidos fuera de la versión base |

**Priorización:** atender primero R1, R3, R6 y R10 (exposición 6).
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

## 8. Gestión de recursos

### 8.1 Infraestructura

| Recurso | Uso en el proyecto | Costo |
|---|---|---|
| Equipo del desarrollador (Windows, Python 3.13) | Desarrollo y ejecución del programa. El programa corre de forma local; no hay servidor propio. | Equipo propio, sin costo adicional |
| GitHub (repositorio, Issues, Projects) | Código, historial de versiones, backlog y tablero Kanban | Plan gratuito |
| GitHub Actions | Integración continua: `ruff` y `pytest` en Python 3.10 y 3.12 | Incluido en el plan gratuito |
| Telegram (cuenta personal y canal privado) | Destino de las subidas; la cuenta gratuita permite archivos de hasta 2 GB | Gratuito |

El proyecto no requiere infraestructura en la nube propia: la nube es de terceros (GitHub y Telegram) y se usa en sus planes gratuitos.

### 8.2 Herramientas SaaS y licencias

**Dependencias directas** (verificadas con `pip-licenses` en un entorno limpio con solo los requisitos del proyecto):

| Herramienta | Versión | Uso | Licencia |
|---|---|---|---|
| Telethon | 1.45.0 | Cliente de la API de Telegram | MIT |
| Rich | 12.6.0 | Interfaz de consola | MIT |
| cryptg | 0.6.0 (Python 3.11 o superior) | Acelera el cifrado de las transferencias | CC0 (dominio público) |
| pytest | 9.2.0 | Pruebas automatizadas | MIT |
| ruff | 0.17.4 | Análisis estático | MIT |

La instalación en Python 3.10 usa una versión anterior de `cryptg`, cuya licencia no se verificó.

**Dependencias transitivas:** pyaes (MIT), rsa (Apache), pyasn1 (BSD-2-Clause), Pygments (BSD-2-Clause), commonmark (BSD), colorama (BSD), iniconfig (MIT), packaging (Apache-2.0 o BSD-2-Clause) y pluggy (MIT).

Todas las licencias son permisivas o de dominio público; ninguna es de copyleft, por lo que no imponen condiciones a la licencia del proyecto.

**Servicios:**

| Servicio | Uso | Plan |
|---|---|---|
| GitHub | Control de versiones, Issues, Projects y CI | Gratuito |
| Asistente de IA | Apoyo al desarrollo, bajo el proceso de `GUIA_DESARROLLO.md` | Gratuito |

El proyecto se distribuye bajo la licencia MIT (archivo `LICENSE`), compatible con las licencias de sus dependencias.

### 8.3 Talento humano

Un desarrollador, que asume todos los roles (ver sección 9). Dedicación aproximada: 9 a 12 horas por semana (3 horas por día, de 3 a 4 días). Conocimientos requeridos: Python, programación asíncrona, uso de Git y de la API de Telegram.

## 9. Estructura del equipo y roles

### 9.1 Estructura propuesta (ficticia, con fines académicos)

Equipo pequeño, multifuncional y centrado en el producto, de 4 integrantes más un representante del usuario final. El tamaño favorece el flujo continuo de Kanban y un límite de trabajo en curso (WIP) bajo.

| Rol | Responsabilidades | Dónde se refleja en el repositorio | Dedicación |
|---|---|---|---|
| Product Owner | Mantener y priorizar el backlog; decidir las solicitudes de cambio; velar por la visión y el alcance | `PLAN_DEL_PROYECTO.md`, Issues, plantilla de solicitud de cambio | Parcial |
| Tech Lead | Garantizar la arquitectura y sus invariantes; revisar los cambios; gestionar la deuda técnica y los riesgos técnicos | `ARQUITECTURA.md`, registro de riesgos | Parcial |
| Desarrollador | Implementar las funciones; escribir las pruebas antes del código; refactorizar | `telegram_uploader/`, `test/` | Completa |
| Ingeniero DevOps | Mantener la integración continua, las dependencias con versión fija y las etiquetas de versión | `.github/workflows/ci.yml`, `requirements*.txt`, etiquetas | Parcial |

**Representante del usuario final** (no integrante del equipo): valida que las funciones resuelvan la necesidad de respaldar archivos en un canal privado, y participa en la priorización mediante el Product Owner.

**Decisiones:**

| Decisión | Quién decide |
|---|---|
| Aceptar o rechazar un cambio de alcance | Product Owner |
| Aprobar un cambio de diseño que afecte las reglas de arquitectura | Tech Lead |
| Publicar una versión (etiqueta) | Tech Lead, con la verificación de DevOps (CI en verde) |

El asistente de IA no es un integrante del equipo: es una herramienta cuyas propuestas verifica y asume quien las usa (ver `GUIA_DESARROLLO.md`).

### 9.2 Situación real

El proyecto lo desarrolla **una sola persona**, que asume los cuatro roles, con una dedicación de 9 a 12 horas semanales (sección 8.3). Los roles se distinguen por los artefactos que produce cada uno (columna "Dónde se refleja"), de modo que si el equipo creciera, la responsabilidad podría repartirse sin reorganizar el repositorio.

## 10. Roadmap del producto

El roadmap ordena las entregas esperadas sin fijar fechas. Las versiones siguen el versionado semántico. Cada elemento corresponde a un Issue del backlog (sección 4).

| Etapa | Versión | Contenido | Estado |
|---|---|---|---|
| Hecho | 1.2.0 | Reestructuración: paquete modular, pruebas, análisis estático, CI, documentación y plan del proyecto | Completada |
| Hecho | 1.2.1 | Deuda técnica sin cambio de comportamiento: operaciones de archivo en hilos, `subir_archivo` dividida, `menu_configuracion` con tabla de opciones y `ruff` bloqueante en la integración continua | Completada |
| Hecho | 1.3.0 | Reanudar subidas por fragmentos dentro de la misma ejecución | Completada |
| Siguiente | 1.4.0 | Opción `--limite N` | Planificada |
| Después | A definir | Reanudar subidas entre ejecuciones y otras ideas del backlog marcadas como pospuestas, sujetas al proceso de gestión de cambios | Pospuesta |

## 11. Plan de iteraciones

El método es Kanban, que fluye de forma continua y no usa sprints de contenido fijo. Para planificar se define una **cadencia de 2 semanas**: al cierre de cada ciclo se revisa lo hecho, se actualiza el registro de riesgos y se elige lo siguiente. La capacidad estimada es de 18 a 24 horas por ciclo (9 a 12 horas semanales, sección 8.3). Se trabaja con un elemento a la vez (WIP = 1) y cada elemento cumple la definición de terminado de la sección 7.

| Ciclo | Elementos | Resultado | Estado |
|---|---|---|---|
| 1 | Operaciones bloqueantes en asyncio | Eliminados los 4 hallazgos de `ruff` de tipo ASYNC | Completado |
| 2 | Dividir `subir_archivo` y simplificar `menu_configuracion` | Eliminados los hallazgos de complejidad | Completado |
| 3 | `ruff` bloqueante en la integración continua | Cero hallazgos y CI que falla ante nuevos | Completado |
| 4 | Reanudar subidas por fragmentos (misma ejecución) | Versión 1.3.0 | Completado |
| 5 | Opción `--limite N` | Versión 1.4.0 | Planificado |

Las estimaciones son iniciales y se ajustan con la experiencia de cada ciclo. Una solicitud de cambio aceptada entra al backlog y se ubica según su prioridad, sin alterar el ciclo en curso.

## 12. Plan de comunicación

| Qué se comunica | Audiencia | Canal | Frecuencia | Responsable |
|---|---|---|---|---|
| Estado del trabajo | Equipo y docente | Tablero de GitHub Projects | Continuo | Desarrollador |
| Solicitudes de cambio y decisiones | Equipo | Issues con la plantilla de cambio | Cuando ocurren | Product Owner |
| Cambios por versión | Usuarios y equipo | `CHANGELOG.md` y etiquetas | Con cada versión | Ingeniero DevOps |
| Reglas de arquitectura | Desarrolladores | `ARQUITECTURA.md` | Cuando cambian | Tech Lead |
| Riesgos | Equipo | Registro de riesgos (sección 6) | Cada ciclo de 2 semanas | Tech Lead |
| Avances y entregas del proyecto | Docente | Informe técnico | Cada entrega | Desarrollador |

La comunicación es principalmente **asíncrona** y escrita (Issues, documentos y changelog), de modo que cualquier persona pueda incorporarse sin explicación directa. Con el equipo propuesto (sección 9.1) se sumaría una reunión síncrona breve al cierre de cada ciclo. En la situación real (un solo desarrollador) esa revisión se hace como autorrevisión y queda por escrito en los Issues.