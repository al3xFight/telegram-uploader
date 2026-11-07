"""Búsqueda de archivos, orden cronológico y utilidades de video (ffprobe/ffmpeg)."""
import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .consola import log
from .constantes import EXTENSIONES_VIDEO


def encontrar_archivos(carpeta: Path, solo_videos: bool):
    for ruta in carpeta.rglob("*"):
        if ruta.is_file():
            if solo_videos and ruta.suffix.lower() not in EXTENSIONES_VIDEO:
                continue
            yield ruta


FILENAME_DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})[_-](\d{2})-(\d{2})-(\d{2})")


FFPROBE_DISPONIBLE = shutil.which("ffprobe") is not None


FFMPEG_DISPONIBLE = shutil.which("ffmpeg") is not None


def _get_video_creation_time(ruta: Path):
    if not FFPROBE_DISPONIBLE:
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags=creation_time",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(ruta),
    ]
    try:
        result = subprocess.run(  # noqa: S603 - lista fija, sin shell
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, check=False)
        value = result.stdout.strip()
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (subprocess.SubprocessError, OSError, ValueError):
        return None


def obtener_timestamp_orden(ruta: Path) -> float:
    if ruta.suffix.lower() in EXTENSIONES_VIDEO:
        ts = _get_video_creation_time(ruta)
        if ts is not None:
            return ts

    match = FILENAME_DATE_PATTERN.search(ruta.name)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second).timestamp()
        except ValueError:
            pass

    return ruta.stat().st_mtime


def obtener_atributos_video(ruta: Path):
    if not FFPROBE_DISPONIBLE:
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json",
        str(ruta),
    ]
    try:
        result = subprocess.run(  # noqa: S603 - lista fija, sin shell
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, check=False)
        data = json.loads(result.stdout)
        stream = (data.get("streams") or [{}])[0]
        width = int(stream.get("width", 0) or 0)
        height = int(stream.get("height", 0) or 0)
        duration = float((data.get("format") or {}).get("duration", 0) or 0)
        if width and height:
            return width, height, duration
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        log.debug("ffprobe no pudo leer %s: %s", ruta.name, e)
    return None


def generar_miniatura(ruta: Path, duracion: float = 0.0):
    if not FFMPEG_DISPONIBLE:
        return None

    momento = min(1.0, duracion / 2) if duracion > 0 else 0.5
    fd, destino_str = tempfile.mkstemp(suffix=".jpg", prefix="thumb_")
    os.close(fd)
    destino = Path(destino_str)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(momento),
        "-i", str(ruta),
        "-frames:v", "1",
        "-vf", "scale=320:-2",
        "-q:v", "4",
        str(destino),
    ]
    try:
        result = subprocess.run(  # noqa: S603 - lista fija, sin shell
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
        if result.returncode == 0 and destino.exists() and destino.stat().st_size > 0:
            return destino
    except (subprocess.SubprocessError, OSError) as e:
        log.debug("ffmpeg no pudo generar miniatura de %s: %s", ruta.name, e)

    with contextlib.suppress(OSError):
        destino.unlink(missing_ok=True)
    return None
