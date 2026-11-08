# Guía de desarrollo: cómo agregar funciones al proyecto

Esta guía explica cómo agregar una función nueva sin romper nada, con o sin
asistente de IA. Léela completa antes de tocar código.

## 1. Principios

1. **La IA propone, las pruebas verifican, el desarrollador decide.**
   Ningún cambio se acepta sin entenderlo y sin pruebas en verde.
2. **Un cambio, un commit.** Si algo se rompe, sabes cuál fue.
3. **Primero la prueba, después el código.** La prueba define qué significa "funciona".
4. **Se respetan las reglas de ARQUITECTURA.md** (dependencias entre módulos e
   invariantes, por ejemplo: `clave_archivo` se calcula antes de subir).
5. **Todo texto visible va en `i18n.py`, en español e inglés.**

## 2. Antes de empezar

```bash
git status                                   # árbol limpio
python -m pytest -q                          # todo en verde (anota cuántas)
ruff check telegram_uploader subir_a_telegram.py herramientas --statistics   # anota los hallazgos
python herramientas/contexto.py --mapa       # ubica dónde tocar
git checkout -b feature/nombre-de-la-funcion
```

Si algo ya falla antes de empezar, no avances: arréglalo primero.

## 3. Receta general (en este orden)

| # | Paso | Dónde |
|---|------|-------|
| 1 | Describir la funcionalidad en una frase y definir el comportamiento esperado, incluidos los casos de error | tu cuaderno |
| 2 | Ubicar los módulos afectados con el mapa | `contexto.py --mapa` |
| 3 | Escribir la prueba que falla (debe fallar, eso confirma que prueba algo) | `test/` |
| 4 | Agregar los textos nuevos (ES y EN, mismas claves) | `i18n.py` |
| 5 | Agregar el argumento o la clave de configuración | `cli.py` / `config.py` |
| 6 | Agregar la lógica | el módulo que le corresponda |
| 7 | Correr pruebas y ruff | terminal |
| 8 | Actualizar documentación: README (uso), ARQUITECTURA (si cambia estructura o reglas), CHANGELOG, versión en `constantes.py` | docs |
| 9 | Commit, tag y push | git |
| 10 | Anotar en la bitácora de IA (si usaste IA) qué propuso, qué verificaste y qué corregiste | informe |

### Regla de versión (versionado semántico)
- Función nueva sin romper lo existente: **minor** (1.2.0 → 1.3.0).
- Corrección de un error: **patch** (1.2.0 → 1.2.1).
- Cambio que rompe el uso anterior: **major** (2.0.0).

## 4. Ejemplo completo: `--limite N` (subir como máximo N archivos)

Comportamiento: `--limite 2` sube máximo 2 archivos pendientes; si N es menor que 1,
el programa avisa y termina con error. Sin `--limite`, nada cambia.

### 4.1 Prueba primero (`test/test_flujo_completo.py`, al final)

```python
def test_limite_sube_como_maximo_n_archivos(tmp_path, monkeypatch):
    archivo = _preparar(tmp_path, monkeypatch, "--limite", "2")
    for nombre in ("b.txt", "c.txt", "d.txt"):
        (archivo.parent / nombre).write_text("x")

    asyncio.run(app.main())

    assert len(ClienteFalso.subidas) == 2
```

y en `test/test_validaciones.py`:

```python
def test_limite_menor_que_1_termina_con_error(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, "--limite", "0")
    with pytest.raises(SystemExit) as salida:
        asyncio.run(app.main())
    assert salida.value.code == 1
```

Ejecuta `python -m pytest -q`: estas dos deben **fallar** (la opción no existe aún).
Si `_preparar` o `ClienteFalso` difieren de lo que usa este ejemplo, ajusta a su
código real.

### 4.2 Textos (`i18n.py`), misma clave en `es` y `en`

En `STRINGS["es"]`:
```python
"arg_limite_help": "Sube como máximo N archivos en esta ejecución.",
"err_limite_min1": "❌ --limite debe ser al menos 1",
"log_limit_applied": "🔢 Límite activo: se subirán como máximo {n} archivo(s) en esta ejecución.",
```
En `STRINGS["en"]`:
```python
"arg_limite_help": "Upload at most N files in this run.",
"err_limite_min1": "❌ --limite must be at least 1",
"log_limit_applied": "🔢 Limit active: at most {n} file(s) will be uploaded in this run.",
```

### 4.3 Argumento (`cli.py`, función `construir_parser`)

Junto a los demás `add_argument`:
```python
parser.add_argument("--limite", type=int, default=None, metavar="N", help=t("arg_limite_help"))
```

### 4.4 Validación (`resolver_ajustes`), junto a las otras validaciones

```python
if args.limite is not None and args.limite < 1:
    console.print(f"[red]{t('err_limite_min1')}[/red]")
    sys.exit(1)
```
Y en `test/test_funciones_nuevas.py`, función `_args`, agrega `limite=None` al
diccionario `base` (si no, `resolver_ajustes` falla con `AttributeError`).

### 4.5 Lógica (`main`, justo después de los `log.info` de archivos encontrados/pendientes)

```python
if args.limite is not None:
    pendientes = pendientes[:args.limite]
    log.info(t("log_limit_applied", n=args.limite))
```
Debe ir **antes** de `if not pendientes:` y de crear el cliente, para que el total
de `log_finished` sea el real.

### 4.6 Verificar

```bash
python -m pytest -q
ruff check telegram_uploader subir_a_telegram.py herramientas --statistics
python subir_a_telegram.py --lang es --help      # debe aparecer --limite
```

### 4.7 Documentación y versión
- `constantes.py`: `VERSION = "1.3.0"`
- `CHANGELOG.md`: nueva sección `1.3.0` con "Agregado: opción `--limite N`".
- `README.md`: agrega `--limite` a la tabla de opciones.
- `ARQUITECTURA.md`: agrega la receta "quiero limitar archivos por ejecución → toco cli, i18n".

### 4.8 Commit

```bash
git add -A && git status
git commit -m "Agrega --limite N: sube como maximo N archivos por ejecucion"
git tag v1.3.0
git push && git push --tags
```

## 5. Recetas rápidas

**Nuevo ajuste guardado en la configuración (ej. `timeout`)**
`CONFIG_DEFAULTS` (config.py) → pedirlo en el asistente y el menú → textos ES/EN →
campo en `OpcionesSubida` (si es un número o interruptor) → leerlo en `resolver_ajustes` →
prueba → documentación.

**Nuevo texto o mensaje**
Clave en ES y EN con el mismo nombre → usar `t("clave")`. Nunca escribir texto fijo en el código.

**Nuevo módulo**
Decide de quién depende (solo hacia "abajo": constantes y consola son la base; evita
imports circulares) → agrégalo a ARQUITECTURA.md (una prueba lo exige) → pruebas propias.

**Cambio en la subida**
Lee primero las reglas no negociables de ARQUITECTURA.md: nunca borrar el archivo
antes de confirmar la subida, nunca registrar un fallo como subido.

## 6. Cómo pedirle un cambio a una IA (sin que se salte nada)

Pasos:
1. Genera el contexto: `python herramientas/contexto.py` (o `--modulos cli --con-pruebas`).
2. Pégalo completo, **y luego** pega esta petición:

```text
Actúa como ingeniero de software del proyecto cuyo contexto te pasé.
Quiero agregar: <DESCRIPCIÓN EN UNA FRASE>.
Comportamiento esperado: <CASOS NORMALES Y DE ERROR>.

Reglas obligatorias:
- Sigue la receta de GUIA_DESARROLLO.md sección 3, en orden, sin omitir ningún paso.
- Usa SOLO nombres de funciones, claves de i18n y firmas que existan en el contexto.
  Si necesitas algo que no veo, dímelo; no lo inventes.
- Sigue las convenciones: claves arg_*_help, err_*, log_*; textos en español e inglés.
- No violes las reglas de ARQUITECTURA.md ni la regla de dependencias entre módulos.
- Un solo cambio, sin refactorizar nada más.

Formato de respuesta, paso a paso:
1. Lista de archivos a tocar y por qué.
2. La prueba que debe fallar primero.
3. Para cada archivo: "busca esto" y "reemplázalo por esto" (o "agrega después de esto").
4. Pruebas existentes que necesiten actualizarse (helpers, fixtures).
5. Cambios en versión, CHANGELOG, README y ARQUITECTURA.
6. Comandos de verificación y el resultado esperado.
7. Mensaje de commit.
Antes de escribir código, dime qué dudas tienes sobre el comportamiento.
```

## 7. Cómo verificar lo que propone la IA (checklist)

- [ ] ¿Todas las funciones, claves y firmas que usa existen? (búscalas con el buscador del editor)
- [ ] ¿Las claves nuevas siguen la convención y están en ES y EN?
- [ ] ¿Los casos de error avisan, en vez de ignorarse en silencio?
- [ ] ¿Respeta las reglas de ARQUITECTURA.md?
- [ ] ¿Actualiza pruebas, versión, CHANGELOG y README?
- [ ] ¿Puedo explicar cada línea sin mirar la respuesta? Si no, no se acepta.
- [ ] ¿pytest en verde y ruff sin hallazgos nuevos?

## 8. Errores comunes
- Inventar claves de texto o firmas que no existen.
- Invertir condiciones (`args.todo` en vez de `not args.todo`).
- Olvidar actualizar los helpers de las pruebas.
- Olvidar la versión o el CHANGELOG (la prueba de documentación falla).
- Mezclar varios cambios en un mismo commit.