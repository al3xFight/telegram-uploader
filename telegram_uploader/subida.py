"""Conexión con Telegram y subida de archivos (fragmentos en paralelo, reintentos, progreso)."""
import asyncio
import contextlib
import inspect
import mimetypes
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from telethon import TelegramClient, helpers
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.functions.upload import SaveBigFilePartRequest
from telethon.tl.types import DocumentAttributeVideo, InputFileBig

from .consola import console, log
from .constantes import (
    EXTENSIONES_VIDEO,
    MAX_REINTENTOS_ERROR,
    MAX_REINTENTOS_FLOOD,
    SESSION_NAME,
    UMBRAL_ARCHIVO_GRANDE,
)
from .i18n import t
from .medios import generar_miniatura, obtener_atributos_video
from .registro import clave_archivo, guardar_registro


def resolver_canal(valor: str):
    valor = str(valor).strip()
    if valor.lstrip("-").isdigit():
        return int(valor)
    return valor

def tamano_archivo(ruta: Path) -> int:
    """Tamaño del archivo en bytes (operación bloqueante, se ejecuta en un hilo)."""
    return ruta.stat().st_size


def leer_parte(ruta: Path, desplazamiento: int, tamano: int) -> bytes:
    """Lee un fragmento del archivo (operación bloqueante, se ejecuta en un hilo)."""
    with open(ruta, "rb") as f:
        f.seek(desplazamiento)
        return f.read(tamano)

async def upload_file_paralelo(client, ruta: Path, chunks_paralelos: int, progress_callback=None):
    file_size = await asyncio.to_thread(tamano_archivo, ruta)
    if file_size <= UMBRAL_ARCHIVO_GRANDE or chunks_paralelos <= 1:
        return await client.upload_file(str(ruta), part_size_kb=512, progress_callback=progress_callback)

    part_size = 512 * 1024
    part_count = (file_size + part_size - 1) // part_size
    file_id = helpers.generate_random_long()

    semaforo = asyncio.Semaphore(max(1, chunks_paralelos))
    subido = 0
    lock = asyncio.Lock()

    async def subir_parte(idx):
        nonlocal subido
        async with semaforo:
            parte = await asyncio.to_thread(leer_parte, ruta, idx * part_size, part_size)

            ok = await client(SaveBigFilePartRequest(file_id, idx, part_count, parte))
            if not ok:
                raise RuntimeError(f"Telegram rechazó la parte {idx}/{part_count}")

            if progress_callback:
                async with lock:
                    subido += len(parte)
                    resultado = progress_callback(subido, file_size)
                    if inspect.isawaitable(resultado):
                        await resultado

    await asyncio.gather(*(subir_parte(i) for i in range(part_count)))
    return InputFileBig(file_id, part_count, ruta.name)


@dataclass(frozen=True)
class OpcionesSubida:
    """Ajustes de comportamiento de una subida (no cambian entre archivos)."""

    borrar_local: bool = False
    dry_run: bool = False
    pausa_min: float = 3.0
    pausa_max: float = 6.0
    chunks_paralelos: int = 8
    archivos_simultaneos: int = 1


@dataclass
class ContextoSubida:
    """Recursos compartidos por todas las subidas de una ejecución."""

    client: Any
    destino: Any
    semaforo: asyncio.Semaphore
    progress: Progress
    task_global_id: Any = None


@dataclass(frozen=True)
class MetadatosArchivo:
    """Datos que se envían junto con el archivo (solo los videos los tienen)."""

    es_video: bool = False
    atributos: list | None = None
    mime_type: str | None = None
    miniatura: Path | None = None


def preparar_medios(ruta: Path) -> MetadatosArchivo:
    """Obtiene atributos, tipo MIME y miniatura si el archivo es un video."""
    if ruta.suffix.lower() not in EXTENSIONES_VIDEO:
        return MetadatosArchivo()

    atributos = None
    duracion_video = 0.0
    dims = obtener_atributos_video(ruta)
    if dims:
        ancho, alto, duracion_video = dims
        atributos = [DocumentAttributeVideo(
            duration=int(duracion_video), w=ancho, h=alto, supports_streaming=True,
        )]
    mime_type = mimetypes.guess_type(ruta.name)[0] or "video/mp4"
    miniatura = generar_miniatura(ruta, duracion_video)
    return MetadatosArchivo(True, atributos, mime_type, miniatura)


def crear_callback_progreso(ctx: ContextoSubida, task_id):
    """Devuelve la función que actualiza la barra de progreso de un archivo."""
    ultimo_progreso = 0

    def progreso(actual, total):
        nonlocal ultimo_progreso
        if actual - ultimo_progreso > 0:
            ctx.progress.update(task_id, completed=actual)
            ultimo_progreso = actual

    return progreso


def simular_subida(ctx: ContextoSubida) -> bool:
    """Modo --dry-run: no sube nada, solo avanza la barra global."""
    log.info(t("dry_run_note"))
    if ctx.task_global_id is not None:
        ctx.progress.advance(ctx.task_global_id, 1)
    return True


async def enviar_con_reintentos(ctx: ContextoSubida, opciones: OpcionesSubida, ruta: Path,
                                meta: MetadatosArchivo, progreso) -> bool:
    """Sube y envía el archivo reintentando ante FloodWait y errores de red.

    Devuelve True si se envió y False si se agotaron los reintentos o hubo un error inesperado.
    """
    intentos_flood = 0
    intentos_error = 0
    while True:
        try:
            handle = await upload_file_paralelo(ctx.client, ruta, opciones.chunks_paralelos, progreso)
            await ctx.client.send_file(
                ctx.destino,
                file=handle,
                caption=ruta.name,
                attributes=meta.atributos,
                mime_type=meta.mime_type,
                supports_streaming=meta.es_video,
                thumb=str(meta.miniatura) if meta.miniatura else None,
            )
            return True
        except FloodWaitError as e:
            intentos_flood += 1
            if intentos_flood > MAX_REINTENTOS_FLOOD:
                log.error(t("err_flood_too_many", nombre=ruta.name))
                return False
            log.warning(t("warn_flood_wait", segundos=e.seconds))
            await asyncio.sleep(e.seconds + 1)
        except (RPCError, ConnectionError, OSError) as e:
            intentos_error += 1
            if intentos_error > MAX_REINTENTOS_ERROR:
                log.error(t("err_persistent", nombre=ruta.name, error=e))
                return False
            espera = 5 * intentos_error
            log.warning(t("warn_retry", nombre=ruta.name, error=e,
                          intento=intentos_error, maximo=MAX_REINTENTOS_ERROR, espera=espera))
            await asyncio.sleep(espera)
        except Exception as e:  # noqa: BLE001 - último recurso: se registra y no aborta la cola
            log.error(t("err_unexpected", nombre=ruta.name, error=e))
            return False


async def finalizar_subida(ctx: ContextoSubida, opciones: OpcionesSubida, ruta: Path):
    """Tras una subida confirmada: avanza la barra, borra el local si se pidió y espera."""
    if ctx.task_global_id is not None:
        ctx.progress.advance(ctx.task_global_id, 1)

    log.info(t("log_done", nombre=ruta.name))

    if opciones.borrar_local:
        await asyncio.to_thread(ruta.unlink)
        log.info(t("log_deleted_local", nombre=ruta.name))

    if opciones.pausa_max > 0:
        espera = random.uniform(opciones.pausa_min, opciones.pausa_max)  # noqa: S311 - pausa anti-spam, no es criptografía
        log.info(t("log_pause", segundos=espera))
        await asyncio.sleep(espera)


async def subir_archivo(ctx: ContextoSubida, opciones: OpcionesSubida, ruta: Path):
    async with ctx.semaforo:
        tamano_bytes = await asyncio.to_thread(tamano_archivo, ruta)
        tamano_mb = tamano_bytes / (1024 * 1024)
        log.info(t("log_uploading", nombre=ruta.name, mb=tamano_mb))

        if opciones.dry_run:
            return simular_subida(ctx)

        task_id = ctx.progress.add_task(f"🎬 {ruta.name[:25].ljust(25)}", total=tamano_bytes)
        meta = preparar_medios(ruta)
        progreso = crear_callback_progreso(ctx, task_id)

        try:
            exito = await enviar_con_reintentos(ctx, opciones, ruta, meta, progreso)
        finally:
            ctx.progress.remove_task(task_id)
            if meta.miniatura:
                with contextlib.suppress(OSError):
                    meta.miniatura.unlink(missing_ok=True)

        if not exito:
            return False

        await finalizar_subida(ctx, opciones, ruta)
        return True


def crear_cliente(api_id: int, api_hash: str):
    return TelegramClient(
        SESSION_NAME, api_id, api_hash,
        connection_retries=5,
        retry_delay=1,
        request_retries=5,
        timeout=60,
        flood_sleep_threshold=60,
    )


async def resolver_destino(client, canal):
    """Busca el canal de destino; si no existe, informa y termina."""
    try:
        return await client.get_entity(resolver_canal(canal))
    except (ValueError, RPCError) as e:
        console.print(f"[red]{t('err_channel_not_found', canal=canal, error=e)}[/red]")
        console.print(t("hint_check_channel"))
        console.print(t("hint_fix_config"))
        sys.exit(1)


def crear_barra_progreso() -> Progress:
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TextColumn("[dim]Elapsed:[/dim]"),
        TimeElapsedColumn(),
        TextColumn("[dim]ETA:[/dim]"),
        TimeRemainingColumn(),
        transient=False,
        refresh_per_second=10,
    )


async def ejecutar_subidas(client, destino, pendientes: list, registro: dict,
                           opciones: OpcionesSubida) -> int:
    """Sube todos los pendientes y registra los exitosos. Devuelve cuántos se subieron."""
    semaforo = asyncio.Semaphore(max(1, opciones.archivos_simultaneos))
    lock_registro = asyncio.Lock()
    subidos_ok = 0
    progress = crear_barra_progreso()

    with progress:
        task_global_id = progress.add_task(t("progress_total_label"), total=len(pendientes))
        ctx = ContextoSubida(client, destino, semaforo, progress, task_global_id)

        async def procesar(ruta):
            nonlocal subidos_ok
            # La clave se calcula ANTES de subir: con --borrar-local el
            # archivo ya no existirá después y ruta.stat() fallaría.
            clave = clave_archivo(ruta)
            exito = await subir_archivo(ctx, opciones, ruta)
            if exito and not opciones.dry_run:
                async with lock_registro:
                    registro[clave] = {"nombre": ruta.name, "ruta_original": str(ruta)}
                    guardar_registro(registro)
                    subidos_ok += 1

        await asyncio.gather(*(procesar(ruta) for ruta in pendientes))

    return subidos_ok
