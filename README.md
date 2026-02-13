# Keylogger Educativo Seguro

Proyecto educativo para practicar arquitectura Python, cifrado local y manejo de logs con consentimiento explícito.

No implementa captura global de teclado ni monitoreo oculto. Solo registra texto que tú ingresas manualmente.

## Qué hace

- Registra entradas de texto en modo interactivo o por comando único.
- Cifra cada registro en local con AES-GCM.
- Guarda en `logs/keystrokes.enc`.
- Permite leer, exportar, rotar y limpiar logs.

## Qué no hace

- No captura teclas del sistema operativo.
- No se ejecuta en segundo plano para espiar.
- No envía datos por red.

## Requisitos

- Python 3.10 o superior.
- Dependencias de `requirements.txt`.

## Instalación rápida

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup.py
```

## Uso diario

Flujo recomendado para usarlo todo el tiempo sin perder control:

1. Verifica entorno:
```bash
python setup.py
```

2. Revisa sistema y estado:
```bash
python main.py --info
python main.py --stats
python main.py --doctor
python main.py --key-info
python main.py --list-logs
python main.py --verify
```

3. Registra datos:
```bash
python main.py
```

4. Revisa lo registrado:
```bash
python main.py --read --limit 30
```

5. Exporta cuando necesites análisis:
```bash
python main.py --export-json exports/logs.json --limit 500
python main.py --export-csv exports/logs.csv --limit 500
```

6. Mantenimiento periódico:
```bash
python main.py --rotate
python main.py --cleanup
```

## Referencia de comandos

- `python main.py`
  - Modo interactivo. Escribe texto y termina con `salir`, `exit` o `quit`.

- `python main.py --once "texto"`
  - Guarda una entrada y finaliza.

- `python main.py --info`
  - Muestra información del sistema en JSON.

- `python main.py --stats`
  - Muestra estado del almacenamiento: archivo, tamaño y cantidad de rotados.

- `python main.py --read --limit N`
  - Muestra entradas descifradas (últimas `N`).

- `python main.py --tail`
  - Muestra entradas nuevas en tiempo real (solo log actual).

- `python main.py --tail --tail-from-start`
  - Igual que `--tail`, pero comienza desde el inicio.

- `python main.py --read --read-all --limit N`
  - Lee el log actual y también los rotados.

- `python main.py --read --query TEXTO`
  - Filtra por coincidencia en `message`.

- `python main.py --read --since ISO --until ISO`
  - Filtra por rango de fechas usando timestamp ISO8601.

- `python main.py --read --redact-hardware`
  - Oculta `hardware_id` en la salida.

- `python main.py --export-json RUTA --limit N`
  - Exporta entradas descifradas a JSON.

- `python main.py --export-csv RUTA --limit N`
  - Exporta entradas descifradas a CSV.

- `python main.py --rotate`
  - Fuerza rotación del log actual.

- `python main.py --cleanup`
  - Elimina logs rotados vencidos según `config/settings.py`.

- `python main.py --list-logs`
  - Lista el log actual y los rotados.

- `python main.py --verify`
  - Cuenta líneas válidas/ inválidas por archivo.

- `python main.py --clear --yes`
  - Vacía el log actual.

- `python main.py --doctor`
  - Diagnóstico de entorno y permisos de rutas.

- `python main.py --key-info`
  - Muestra huella de la clave (fingerprint) sin exponer su contenido.

- `python main.py --import-json RUTA --limit N`
  - Importa entradas desde un JSON (lista de objetos con `timestamp`, `platform`, `hardware_id`, `message`).

- `python main.py --import-csv RUTA --limit N`
  - Importa entradas desde un CSV con columnas `timestamp`, `platform`, `hardware_id`, `message`.

- `python main.py --version`
  - Muestra versión de la aplicación.

## Ejemplos prácticos

Registrar una nota rápida:

```bash
python main.py --once "prueba de cifrado local"
```

Leer últimas 10 entradas:

```bash
python main.py --read --limit 10
```

Exportar últimas 100 entradas a CSV:

```bash
python main.py --export-csv exports/ultimo_corte.csv --limit 100
```

Importar desde JSON:

```bash
python main.py --import-json exports/logs.json --limit 100
```

## Estructura del proyecto

- `main.py`: CLI principal.
- `setup.py`: validación inicial de estructura y dependencias.
- `config/settings.py`: parámetros globales.
- `src/keylogger/`: lógica principal de registro manual.
- `src/crypto/`: cifrado y descifrado.
- `src/storage/`: persistencia, lectura y exportación.
- `src/utils/`: utilidades de sistema e ID de hardware.
- `logs/`: archivos cifrados.

## Formato de cada registro

Cada línea descifrada sigue este formato:

`timestamp|platform|hardware_id|message`

## Configuración útil

Edita `config/settings.py` para ajustar:

- `MAX_LOG_SIZE`: tamaño máximo antes de rotación.
- `CLEANUP_DAYS`: días de retención de logs rotados.
- `DEFAULT_READ_LIMIT`: límite por defecto al leer.
- `MAX_EXPORT_ROWS`: máximo permitido al exportar.

## Solución de problemas

- Error `ModuleNotFoundError: No module named 'Crypto'`:
```bash
pip install -r requirements.txt
```

- `--read` no muestra entradas:
  - Verifica que hayas registrado datos antes (`--once` o modo interactivo).
  - Revisa `python main.py --stats` para confirmar tamaño mayor a 0.

- Entradas antiguas no se descifran:
  - Puede haber líneas con clave previa. El lector omite líneas inválidas para no romper la salida completa.

## Seguridad local

- Clave local en `config/.key`.
- Cifrado AES-GCM por registro.
- Sin transmisión de red.
- Agrega `config/.key` y logs al control de acceso del sistema si compartes equipo.

## Licencia

MIT.
