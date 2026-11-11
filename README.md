# 📡 Telegram Uploader
![CI](https://github.com/al3xFight/telegram-uploader/actions/workflows/ci.yml/badge.svg)

Sube videos y otros archivos grandes a un **canal o grupo privado de Telegram** usando **tu propia
cuenta** (no un bot), mediante [Telethon](https://docs.telethon.dev/). Interfaz en español e inglés.

*English: uploads large videos and files to a private Telegram channel/group with your own account.
Run `python subir_a_telegram.py --lang en --help` for the English help.*

## Características

- Subida de **fragmentos en paralelo** para archivos grandes (más rápida).
- **Miniaturas** y atributos de video automáticos (requiere `ffmpeg`, opcional).
- **Orden cronológico** por metadata del video, por fecha en el nombre o por fecha de modificación.
- **Registro de subidos** (`subidos.json`): no repite archivos ya enviados.
- Manejo de límites de Telegram (`FloodWait`) y reintentos con espera creciente.
- Modo `--dry-run` para simular sin subir nada.
- Asistente de configuración interactivo (`--config`); no hay que editar archivos a mano.

## Requisitos

- Python 3.10 o superior
- Una cuenta de Telegram y sus credenciales de API (`api_id` y `api_hash`), gratis en
  <https://my.telegram.org/apps>
- Un canal o grupo privado de destino del que seas miembro o administrador
- `ffmpeg` instalado en el sistema (miniaturas y orden por metadata). Ver cómo instalarlo más abajo.

## Instalación

```bash
git clone <URL-de-tu-repositorio>
cd telegram-uploader
pip install -r requirements.txt
```

### Instalar ffmpeg (no se instala con pip)

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

La primera vez pregunta el idioma y abre el asistente: te pide `api_id`, `api_hash`, el canal de
destino (`@usuario` o ID numérico como `-1001234567890`) y los ajustes de velocidad. Después de iniciar
sesión con tu cuenta, la sesión queda guardada y no vuelve a pedirse.

## Ejemplos

```bash
# Subir todos los videos de una carpeta
python subir_a_telegram.py --carpeta "D:/Videos/viaje"

# Simular primero, sin subir nada
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

## Datos que genera (junto a `subir_a_telegram.py`)

| Archivo | Contenido |
|---|---|
| `config.json` | Tu configuración |
| `sesion_telegram.session` | Sesión iniciada de Telegram |
| `subidos.json` | Registro de archivos ya subidos |

## Desarrollo

```bash
pip install -r requirements-dev.txt
python -m pytest -q                                  # pruebas
ruff check telegram_uploader subir_a_telegram.py herramientas
```

- **Cómo está organizado el código y cómo agregar funciones:** [`ARQUITECTURA.md`](ARQUITECTURA.md)
> Para el procedimiento completo, con un ejemplo de punta a punta, ver `GUIA_DESARROLLO.md`.
- **Historial de versiones:** [`CHANGELOG.md`](CHANGELOG.md)
- **Pegar el proyecto a una IA:** `python herramientas/contexto
- **Visión, alcance y backlog:** [`PLAN_DEL_PROYECTO.md`](PLAN_DEL_PROYECTO.md).py`


## Solución de problemas

| Síntoma | Qué revisar |
|---|---|
| *No se pudo encontrar el canal* | Que el nombre/ID sea correcto y que tu cuenta esté unida al canal (`--config` para corregir) |
| *Telegram pide esperar N segundos* | Es el límite de subidas de Telegram; el programa espera solo |
| Sin miniaturas ni orden por metadata | Instala `ffmpeg` y verifica que esté en el `PATH` |
| Subidas lentas | Verifica que `cryptg` esté instalado (`pip show cryptg`) y sube `--chunks-paralelos` |

  ## Licencia
  MIT. Ver el archivo `LICENSE`.
