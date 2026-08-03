# Decisión: atributos dinámicos de activos (TASK-15)

**Fecha:** 2026-08-03
**Estado:** vigente

## El problema

Conviven dos sistemas para los atributos que varían según la clase de activo:

| | Campo JSON | EAV (FASE 2.1) |
|---|---|---|
| Dónde | `activos.atributos_dinamicos_json` | `categoria_activo`, `atributo_definicion`, `atributo_valor` |
| Quién escribe | los wizards de `activos/` y `activos_v2/` | nadie |
| Quién lee | toda la interfaz y los PDF | nada en producción |
| Validación | diccionario en el código | tipada y en base de datos |
| Consultable en SQL | limitado | sí, con índices |

Es decir: **el EAV está construido pero no se usa**. Ningún formulario escribe en
él y ninguna vista lo lee. El único punto de contacto era el trigger de último
mantenimiento, que escribía en ambos.

## Decisión

**Se mantiene el campo JSON como sistema vigente. El EAV queda en reposo.**

Motivos:

1. **Es el que sostiene la operación.** Los 8 activos existentes, los wizards y
   las actas PDF dependen del JSON. Cambiar de sistema obliga a reescribir los
   formularios, las vistas de detalle y las plantillas.
2. **El volumen no lo justifica.** El EAV rinde cuando hay que filtrar y ordenar
   por atributos arbitrarios sobre muchos registros. Con un inventario de este
   tamaño, MySQL 8 resuelve bien las consultas sobre columnas JSON.
3. **Un sistema a medias es peor que cualquiera de los dos.** Mientras
   coexistían, el trigger escribía en ambos y era imposible saber cuál era la
   fuente de verdad.

## Qué se hizo

- El trigger de último mantenimiento **ya no escribe en el EAV**: solo actualiza
  el JSON, con SQL Core y sin commits anidados (ver TASK-07).
- Las definiciones de atributos tienen **una sola fuente**:
  `app/activos_v2/atributos_dinamicos.py`. Antes estaban duplicadas en tres
  sitios con contenidos distintos (ver TASK-14).
- Las tablas del EAV **se conservan** (vacías). No se borran porque las
  migraciones que las crearon forman parte del historial de Alembic y
  eliminarlas no aporta nada.

## Si en el futuro se decide migrar al EAV

Existe `scripts/migrar_json_a_eav.py`. Antes de usarlo haría falta:

1. Poblar `categoria_activo` y `atributo_definicion` a partir de
   `app/activos_v2/atributos_dinamicos.py`.
2. Ejecutar el script sobre una copia de la base y validar el resultado.
3. Reescribir los wizards para que escriban vía `Activo.set_atributo_valor()`.
4. Actualizar las vistas de detalle y las plantillas PDF.
5. Dejar el JSON solo como lectura durante una temporada de transición.

Mientras eso no ocurra, **no se debe escribir en el EAV**: hacerlo a medias
reintroduce el problema que esta decisión resuelve.
