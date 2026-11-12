# 📡 Telegram Uploader

![CI](https://github.com/al3xFight/telegram-uploader/actions/workflows/ci.yml/badge.svg)

**Sube tus videos y archivos grandes a un canal privado de Telegram, de forma automática.**
Usa tu propia cuenta (no un bot), así que puedes subir archivos de hasta **2 GB** sin pagar Telegram
Premium. Interfaz en español e inglés.

*English: uploads large videos and files to a private Telegram channel/group using your own account.
Run `python subir_a_telegram.py --lang en --help` for the English help.*

## ¿Para qué sirve?

Si usas un canal privado de Telegram como tu nube personal, subir los archivos a mano es lento y
repetitivo. Este programa lo hace por ti:

- Sube **toda una carpeta** de una vez, en orden cronológico.
- **No repite** lo que ya subiste: recuerda los archivos enviados entre ejecuciones.
- Respeta los **límites de Telegram**: espera entre subidas y reintenta solo si hay un error.
- Funciona desde la terminal; no hay que editar archivos a mano.
- Si se corta la conexión a mitad de un archivo grande, **retoma desde donde quedó** en lugar de empezar de nuevo (dentro de la misma ejecución).

## Antes de empezar

Necesitas:

1. **Python 3.10 o superior.**
2. **Una cuenta de Telegram** y un **canal o grupo privado** de destino, del que seas miembro o
   administrador.
3. **Tus credenciales de API** (`api_id` y `api_hash`). Son gratuitas y se piden una sola vez:
   1. Entra a <https://my.telegram.org/apps> e inicia sesión con tu número de teléfono.
   2. Crea una aplicación (el nombre y la descripción pueden ser los que quieras).
   3. Copia el `api_id` y el `api_hash` que te muestra. **No los compartas con nadie.**
4. **`ffmpeg`** (opcional, recomendado): genera miniaturas de los videos y permite ordenarlos por su
   fecha real. Sin él, el programa funciona igual, pero sin miniaturas.

## Instalación

```bash
git clone https://github.com/al3xFight/telegram-uploader.git
cd telegram-uploader
pip install -r requirements.txt
```

### Instalar ffmpeg (opcional, no se instala con pip)

| Sistema | Comando |
|---|---|
| Windows | `winget install Gyan.FFmpeg` (reinicia la terminal después) |
| macOS | `brew install ffmpeg` |
| Linux (Debian/Ubuntu) | `sudo apt install ffmpeg` |

Comprueba que funciona con `ffmpeg -version`.

## Primer uso

```bash
python subir_a_telegram.py
```

La primera vez, el programa:

1. Te pregunta el **idioma**.
2. Abre el **asistente de configuración**: te pide tu `api_id`, tu `api_hash` y el canal de destino
   (`@usuario` o ID numérico como `-1001234567890`), además de los ajustes de velocidad.
3. Inicia sesión en Telegram con tu cuenta (te pedirá tu teléfono y el código que Telegram te envía).

La sesión queda guardada y no vuelve a pedirse. Después, el programa te pregunta qué carpeta subir.

## Uso diario

```bash
# Subir todos los videos de una carpeta
python subir_a_telegram.py --carpeta "D:/Videos/viaje"

# Simular primero, sin subir nada (recomendado la primera vez)
python subir_a_telegram.py --carpeta "D:/Videos/viaje" --dry-run

# Subir todo tipo de archivos y borrar el original tras cada subida exitosa
python subir_a_telegram.py --carpeta "D:/Respaldo" --todo --borrar-local

# Cambiar la configuración guardada
python subir_a_telegram.py --config
```

## Opciones

| Opción | Qué hace |
|---|---|
| `--config` | Abre el menú de configuración y sale, sin subir nada |
| `--carpeta RUTA` | Carpeta con los archivos a subir (si no se indica, la pregunta) |
| `--todo` | Sube todos los archivos, no solo videos |
| `--borrar-local` | Elimina el archivo local **solo después** de subirlo con éxito |
| `--paralelo N` | Archivos subidos a la vez (por defecto 1, mantiene el orden estricto) |
| `--chunks-paralelos N` | Fragmentos en paralelo por archivo, solo para esta ejecución |
| `--pausa-min S` / `--pausa-max S` | Pausa aleatoria entre subidas en segundos (anti-spam) |
| `--dry-run` | Simula la ejecución |
| `--debug` | Muestra más registros de diagnóstico |
| `--lang es\|en` | Fuerza el idioma solo para esta ejecución |
| `--version` | Muestra la versión |

También puedes definir `TG_API_ID`, `TG_API_HASH` y `TG_CANAL` como **variables de entorno**; tienen
prioridad sobre el archivo de configuración.

## ⚠️ Seguridad

- `config.json` guarda tu `api_hash` en **texto plano** y `sesion_telegram.session` equivale a tener tu
  cuenta de Telegram abierta. **Nunca los subas a un repositorio ni los compartas.** El `.gitignore`
  incluido ya los excluye.
- Si sospechas que se filtraron, cierra esa sesión desde *Telegram → Ajustes → Dispositivos*.
- `--borrar-local` es opcional y solo actúa tras una subida confirmada, pero **elimina archivos de
  verdad**: prueba antes con `--dry-run`.

## Solución de problemas

| Síntoma | Qué revisar |
|---|---|
| *No se pudo encontrar el canal* | Que el nombre/ID sea correcto y que tu cuenta esté unida al canal (`--config` para corregir) |
| *Telegram pide esperar N segundos* | Es el límite de subidas de Telegram; el programa espera solo |
| Sin miniaturas ni orden por metadata | Instala `ffmpeg` y verifica que esté en el `PATH` |
| Subidas lentas | Verifica que `cryptg` esté instalado (`pip show cryptg`) y sube `--chunks-paralelos` |
| Se cortó la conexión a mitad de un archivo | El programa reintenta solo y retoma desde el último fragmento subido; verás el aviso `Reanudando…` |

## Qué no hace

- No descarga archivos desde Telegram.
- No tiene interfaz gráfica.
- Sube a un solo destino por ejecución.
- No usa bots: siempre opera con tu cuenta.
- No retoma una subida si cierras el programa: al volver a ejecutarlo, el archivo se sube desde cero.

## Archivos que crea

Se guardan junto a `subir_a_telegram.py`:

| Archivo | Contenido |
|---|---|
| `config.json` | Tu configuración |
| `sesion_telegram.session` | Sesión iniciada de Telegram |
| `subidos.json` | Registro de archivos ya subidos |

## Para desarrolladores

¿Quieres entender el código o agregar funciones?

- **Cómo está organizado y sus reglas:** [`ARQUITECTURA.md`](ARQUITECTURA.md)
- **Guía paso a paso para agregar una función:** [`GUIA_DESARROLLO.md`](GUIA_DESARROLLO.md)
- **Visión, alcance y backlog:** [`PLAN_DEL_PROYECTO.md`](PLAN_DEL_PROYECTO.md)
- **Historial de versiones:** [`CHANGELOG.md`](CHANGELOG.md)

```bash
pip install -r requirements-dev.txt
python -m pytest -q                                  # pruebas
ruff check telegram_uploader subir_a_telegram.py herramientas
```

## Licencia

MIT. Ver el archivo `LICENSE`.