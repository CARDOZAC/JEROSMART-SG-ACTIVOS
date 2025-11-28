# 🚨 SOLUCIONES RÁPIDAS A ERRORES COMUNES

## Error que acabas de tener ✅ SOLUCIONADO

### Error Code: 1064 - Syntax error en CREATE INDEX

**Mensaje completo:**
```
Error Code: 1064. You have an error in your SQL syntax;
check the manual that corresponds to your MySQL server version for
the right syntax to use near 'IF NOT EXISTS idx_activos_fecha_adquisicion'
```

**¿Qué significa?**
Tu versión de MySQL no soporta `IF NOT EXISTS` en los índices.

**✅ SOLUCIÓN:**
Ya lo arreglé en el archivo. Ahora tienes dos opciones:

#### Opción 1: Volver a Ejecutar el Script Completo (FÁCIL)

1. En MySQL Workbench, cierra la pestaña actual
2. Vuelve a abrir el script: `File → Open SQL Script`
3. Selecciona: `migrations/01_correccion_depreciacion_DETALLADO.sql`
4. Ejecuta de nuevo (⚡ rayo)

**Si sale error "Duplicate column":** ¡Está bien! Significa que esa parte ya se ejecutó. Continúa.

#### Opción 2: Ejecutar Solo la Parte de Índices (RÁPIDO)

Copia y pega esto en MySQL Workbench:

```sql
-- Crear índices (ignorar si ya existen)
CREATE INDEX idx_activos_fecha_adquisicion ON activos(fecha_adquisicion);
CREATE INDEX idx_activos_es_legacy ON activos(es_activo_legacy);
CREATE INDEX idx_activos_metodo_depreciacion ON activos(metodo_depreciacion);
CREATE INDEX idx_activos_depreciacion_reporte ON activos(es_activo_legacy, metodo_depreciacion, fecha_adquisicion);

SELECT 'Índices creados exitosamente' AS resultado;
```

**Si sale error "Duplicate key name":** ¡Perfecto! Los índices ya existen. Ignóralo.

---

## 📋 OTROS ERRORES COMUNES

### Error 1: Stored Procedure con LEAVE sin etiqueta

**Mensaje completo:**
```
Error Code: 1064. You have an error in your SQL syntax;
check the manual that corresponds to your MySQL server version for
the right syntax to use near ';
     END IF;' at line 29
```

**¿Qué significa?**
El procedimiento almacenado usa `LEAVE` pero el bloque BEGIN no tiene una etiqueta.

**✅ SOLUCIÓN:**
Ya lo arreglé en el archivo. El bloque BEGIN ahora tiene la etiqueta `proc_label:`.

```sql
-- ANTES (ERROR):
BEGIN
    ...
    LEAVE;  ← Error: no hay etiqueta
END

-- DESPUÉS (CORRECTO):
proc_label: BEGIN
    ...
    LEAVE proc_label;  ← Correcto
END
```

**¿Qué hacer?**
1. Vuelve a abrir el script: `migrations/02_sistema_ingreso_rapido_legacy.sql`
2. Ejecuta el script completo de nuevo (⚡ rayo)
3. Ahora el stored procedure se creará sin errores

---

### Error 1B: Error de sintaxis en CREATE INDEX (múltiples statements)

**Mensaje completo:**
```
Error Code: 1064. You have an error in your SQL syntax;
check the manual that corresponds to your MySQL server version for
the right syntax to use near 'CREATE INDEX idx_activos_metodo_depreciacion ON activos(metodo_depreciacion)' at line 2
```

**¿Qué significa?**
MySQL Workbench está intentando ejecutar dos sentencias CREATE INDEX juntas.

**✅ SOLUCIÓN - OPCIÓN 1 (Ejecutar comandos uno por uno):**
En lugar de ejecutar todo el script con el rayo ⚡, ejecuta los CREATE INDEX uno por uno:

1. Selecciona SOLO este texto:
```sql
CREATE INDEX idx_activos_fecha_adquisicion ON activos(fecha_adquisicion);
```
2. Presiona Ctrl+Enter (o el icono del rayo pequeño)
3. Espera a que termine
4. Repite con el siguiente:
```sql
CREATE INDEX idx_activos_es_legacy ON activos(es_activo_legacy);
```
5. Y así con cada uno

**✅ SOLUCIÓN - OPCIÓN 2 (Usar el script corregido de índices):**
Copia y pega esto directamente en MySQL Workbench:

```sql
-- Crear índices uno por uno
CREATE INDEX idx_activos_fecha_adquisicion ON activos(fecha_adquisicion);

CREATE INDEX idx_activos_es_legacy ON activos(es_activo_legacy);

CREATE INDEX idx_activos_metodo_depreciacion ON activos(metodo_depreciacion);

CREATE INDEX idx_activos_depreciacion_reporte ON activos(es_activo_legacy, metodo_depreciacion, fecha_adquisicion);

SELECT 'Todos los índices creados exitosamente' AS resultado;
```

Ejecuta todo eso con el rayo ⚡.

**Si sale error "Duplicate key name":** Ignóralo, significa que el índice ya existe.

---

### Error 2: "Duplicate column name 'fecha_adquisicion'"

**Qué significa:** La columna ya existe (ya ejecutaste el script antes)

**¿Es malo?** ❌ NO, significa que ya está hecho

**Qué hacer:**
1. Ignora el error
2. Continúa ejecutando el resto del script
3. O salta a la siguiente sección

---

### Error 2: "Unknown column 'fecha_adquisicion' in 'where clause'"

**Qué significa:** Intentas usar una columna que no existe todavía

**¿Por qué pasa?** Ejecutaste solo una parte del script

**Solución:**
1. Ejecuta TODO el script desde el principio
2. O verifica que las columnas se crearon:
   ```sql
   SHOW COLUMNS FROM activos;
   ```

---

### Error 3: "Duplicate key name 'idx_activos_fecha_adquisicion'"

**Qué significa:** El índice ya existe

**¿Es malo?** ❌ NO, ya está creado

**Qué hacer:** Ignóralo y continúa

---

### Error 4: "Access denied for user 'root'@'localhost'"

**Qué significa:** Contraseña incorrecta

**Solución:**
1. Verifica tu contraseña en: `C:\Users\david\JEROSMART ACTIVOS\.env`
2. La línea debe decir: `DB_PASSWORD=JeroNimoDaviLex9824.`
3. Usa esa contraseña en MySQL Workbench

---

### Error 5: "Unknown database 'jerosmart_activos'"

**Qué significa:** La base de datos no existe con ese nombre

**Solución:**
1. Ve a MySQL Workbench
2. En el panel izquierdo, busca el nombre real de tu base de datos
3. Edita el script, línea 8:
   ```sql
   USE jerosmart_activos;  ← Cambia esto por el nombre correcto
   ```

---

### Error 6: "Can't connect to MySQL server"

**Qué significa:** MySQL no está corriendo

**Solución:**
1. Abre **Servicios de Windows** (busca "services.msc")
2. Busca: "MySQL80" o "MySQL"
3. Clic derecho → **Iniciar**

---

## 🔍 VERIFICAR SI TODO FUNCIONÓ

Después de ejecutar el script, corre esto en MySQL Workbench:

```sql
-- Ver columnas nuevas
SHOW COLUMNS FROM activos LIKE '%fecha%';
SHOW COLUMNS FROM activos LIKE '%costo%';
SHOW COLUMNS FROM activos LIKE '%legacy%';

-- Ver índices creados
SHOW INDEX FROM activos WHERE Key_name LIKE 'idx_activos%';

-- Ver cuántos activos se marcaron
SELECT
    COUNT(*) AS total_activos,
    SUM(es_activo_legacy) AS activos_legacy,
    SUM(metodo_depreciacion = 'totalmente_depreciado') AS totalmente_depreciados
FROM activos;
```

**Resultado esperado:**
```
+---------------+----------------+-------------------------+
| total_activos | activos_legacy | totalmente_depreciados  |
+---------------+----------------+-------------------------+
| 6629          | 6629           | ~1629                   |
+---------------+----------------+-------------------------+
```

---

## 📝 CHECKLIST DE VERIFICACIÓN

Marca cada uno cuando lo verifiques:

- [ ] Las columnas `fecha_adquisicion`, `costo_historico`, `es_activo_legacy` existen
- [ ] Los índices `idx_activos_fecha_adquisicion`, etc. están creados
- [ ] Todos los activos tienen `es_activo_legacy = 1`
- [ ] Los activos viejos están marcados como `totalmente_depreciado`
- [ ] La vista `vista_activos_valoracion` existe
- [ ] Puedes hacer SELECT en la vista sin error

---

## 🎯 SI DESPUÉS DE TODO SIGUE SIN FUNCIONAR

**Haz esto:**

1. **Exporta el log completo del error:**
   - En MySQL Workbench, copia TODO el texto del área de "Output"
   - Pégalo en un archivo de texto
   - Envíamelo

2. **Verifica tu versión de MySQL:**
   ```sql
   SELECT VERSION();
   ```
   Dime qué versión te sale (ej: "8.0.35")

3. **Envíame el estado actual:**
   ```sql
   SHOW COLUMNS FROM activos;
   ```
   Copia el resultado completo

4. **O simplemente dime:**
   - ¿En qué línea se detuvo?
   - ¿Qué mensaje de error exacto viste?
   - ¿Ya ejecutaste alguna parte antes?

---

## 💡 TIPS PARA EVITAR ERRORES

### Tip 1: Ejecuta el Script Completo de Una Vez
❌ No lo ejecutes línea por línea
✅ Selecciona TODO (Ctrl+A) y ejecuta (⚡)

### Tip 2: Si Algo Falla, No Pares
✅ Muchos errores son "informativos" (ej: columna ya existe)
✅ Deja que el script termine de ejecutarse

### Tip 3: Haz Backup Antes (Opcional pero Recomendado)
```sql
-- Exportar backup simple
mysqldump -u root -p jerosmart_activos > backup_antes_migracion.sql
```

### Tip 4: Si Tienes Miedo, Prueba en una Tabla de Prueba
```sql
-- Crear copia de la tabla activos
CREATE TABLE activos_backup LIKE activos;
INSERT INTO activos_backup SELECT * FROM activos;

-- Ahora puedes experimentar sin miedo
```

---

## 🆘 CONTACTO RÁPIDO

Si nada de esto funciona, contáctame con:

1. ✅ Captura de pantalla del error
2. ✅ Resultado de: `SELECT VERSION();`
3. ✅ Línea exacta donde falló

Y te ayudo en menos de 5 minutos. 😊

---

**Última actualización:** 2025-11-25
**Para:** David (Error de sintaxis de índices resuelto)
