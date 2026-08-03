# 🎯 PLAN DE ACCIÓN - Sistema JeroSmart Activos

**Basado en:** Análisis Completo del Sistema (ANALISIS_COMPLETO_SISTEMA.md)
**Fecha inicio:** 2025-11-25
**Responsable:** Equipo de Desarrollo + David (Admin)

---

## ⚡ PASO 0: CORRECCIÓN INMEDIATA (AHORA MISMO - 5 minutos)

### ✅ Tarea 0.1: Agregar columna `updated_by` faltante

**Problema:** Error al eliminar activos duplicados
**Comando:**
```powershell
cd "C:\Users\david\JEROSMART ACTIVOS"
.\venv\Scripts\python.exe agregar_columna_updated_by.py
```

**Verificación:**
```powershell
.\venv\Scripts\python.exe verificar_bd.py
```

**Resultado esperado:**
```
✅ La columna 'updated_by' YA EXISTE en la tabla.
```

**Prueba final:**
- Intenta eliminar un activo duplicado desde la interfaz web
- Debería funcionar sin errores

---

## 🔴 FASE 1: CORRECCIONES CRÍTICAS (Prioridad MÁXIMA - 1-2 días)

### ✅ Tarea 1.1: Migración de sistema de depreciación

**Script:** `migrations/01_correccion_depreciacion.sql`

**Ejecución:**
```powershell
# Opción A: Desde PowerShell con MySQL CLI
cd "C:\Users\david\JEROSMART ACTIVOS"
mysql -u root -p jerosmart_activos < migrations\01_correccion_depreciacion.sql

# Opción B: Desde MySQL Workbench
# 1. Abrir MySQL Workbench
# 2. Conectar a jerosmart_activos
# 3. File → Open SQL Script
# 4. Seleccionar: migrations\01_correccion_depreciacion.sql
# 5. Ejecutar (⚡ botón)
```

**Qué hace:**
- ✅ Agrega campo `fecha_adquisicion` (fecha real de compra)
- ✅ Agrega campo `depreciacion_acumulada_historica` (para activos migrados)
- ✅ Agrega campo `es_activo_legacy` (marca activos migrados)
- ✅ Agrega campo `metodo_depreciacion` (línea recta, manual, totalmente depreciado)
- ✅ Crea vista `vista_activos_valoracion` (cálculos correctos)
- ✅ Marca automáticamente activos con más de 10 años como totalmente depreciados

**Verificación:**
```sql
-- Ejecutar en MySQL:
SELECT
    metodo_depreciacion,
    COUNT(*) as cantidad,
    SUM(valor_comercial) as valor_total,
    SUM(depreciacion_acumulada_historica) as depreciacion_total
FROM activos
GROUP BY metodo_depreciacion;
```

**Resultado esperado:**
```
+---------------------------+----------+---------------+----------------------+
| metodo_depreciacion       | cantidad | valor_total   | depreciacion_total   |
+---------------------------+----------+---------------+----------------------+
| linea_recta              | ~5000    | $XX,XXX,XXX   | $0                   |
| totalmente_depreciado     | ~1629    | $XX,XXX,XXX   | $XX,XXX,XXX          |
+---------------------------+----------+---------------+----------------------+
```

---

### ✅ Tarea 1.2: Sistema de ingreso rápido para activos legacy

**Script:** `migrations/02_sistema_ingreso_rapido_legacy.sql`

**Ejecución:**
```powershell
mysql -u root -p jerosmart_activos < migrations\02_sistema_ingreso_rapido_legacy.sql
```

**Qué hace:**
- ✅ Crea tabla `activos_legacy_temporal` (hallazgos en campo)
- ✅ Crea tabla `activos_legacy_historial` (auditoría de investigaciones)
- ✅ Crea vistas para gestión (pendientes, aprobados)
- ✅ Crea stored procedure `sp_incorporar_activo_legacy()` (incorporación automática)
- ✅ Crea triggers para auditoría de cambios de estado

**Verificación:**
```sql
-- Verificar tablas creadas:
SHOW TABLES LIKE 'activos_legacy%';

-- Verificar stored procedure:
SHOW PROCEDURE STATUS WHERE Db = 'jerosmart_activos' AND Name LIKE '%legacy%';

-- Ver vistas creadas:
SELECT * FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = 'jerosmart_activos' AND TABLE_NAME LIKE 'vista_activos_legacy%';
```

---

### ✅ Tarea 1.3: Actualizar modelo Python para nuevos campos

**Archivo:** `app/models.py`

**Cambios necesarios en la clase `Activo`:**
```python
# Agregar después de la línea 129 (después de created_at):
fecha_adquisicion = db.Column(db.DateTime, nullable=True)
depreciacion_acumulada_historica = db.Column(db.Float, default=0.0)
es_activo_legacy = db.Column(db.Boolean, default=False)
metodo_depreciacion = db.Column(db.String(50), default='linea_recta')
valor_residual = db.Column(db.Float, default=0.0)
vida_util_restante_meses = db.Column(db.Integer, nullable=True)
observaciones_depreciacion = db.Column(db.Text, nullable=True)
```
IMPORT SQL (CONSOLE.MD)
 DNS = 00.8965 (CONSOLE.LOG) 
 
**Modificar propiedad `depreciacion_acumulada` (línea 186):**
```python
@property
def depreciacion_acumulada(self):
    """
    Calcula la depreciación acumulada usando el método configurado.
    """
    # Si tiene depreciación manual/histórica, usarla
    if self.metodo_depreciacion == 'manual' or self.metodo_depreciacion == 'totalmente_depreciado':
        return self.depreciacion_acumulada_historica or 0

    # Si no tiene fecha de adquisición, usar histórica
    if not self.fecha_adquisicion:
        return self.depreciacion_acumulada_historica or 0

    # Calcular depreciación por línea recta
    if self.metodo_depreciacion == 'linea_recta':
        if not self.valor_comercial:
            return 0

        vida_util_anios = 10  # Default

        # TICs: 5 años
        if self.clase_id == 3:
            vida_util_anios = 5

        # Biomédico: obtener de JSON o default 10
        elif self.clase_id == 1:
            try:
                attrs = self.atributos_dinamicos_json or {}
                vida_util_anios = int(attrs.get('vida_util', 10))
            except (TypeError, ValueError):
                vida_util_anios = 10

        # Calcular años transcurridos desde adquisición real
        anios_transcurridos = (datetime.now() - self.fecha_adquisicion).days / 365.25

        if anios_transcurridos <= 0:
            return 0

        depreciacion_anual = self.valor_comercial / vida_util_anios
        depreciacion_total = depreciacion_anual * anios_transcurridos

        return min(depreciacion_total, self.valor_comercial)

    return self.depreciacion_acumulada_historica or 0
```

**Verificación:**
```bash
# Reiniciar aplicación Flask
# Ctrl+C para detener
# Volver a ejecutar: python run.py
```

---

## 🟠 FASE 2: FUNCIONALIDADES NUEVAS (Alta prioridad - 3-5 días)

### ✅ Tarea 2.1: Crear formulario de ingreso rápido legacy

**Nuevo archivo:** `app/templates/ingreso_rapido_legacy.html`

**Ruta Flask:** `app/activos/routes.py`
```python
@activos_bp.route('/ingreso-rapido-legacy', methods=['GET', 'POST'])
@login_required
def ingreso_rapido_legacy():
    """Formulario simplificado para registrar activos legacy encontrados"""
    if request.method == 'POST':
        # Validar campos mínimos
        placa = request.form.get('placa_codigo_interno')
        nombre = request.form.get('nombre_activo')
        ubicacion = request.form.get('ubicacion')

        if not all([placa, nombre, ubicacion]):
            flash('Placa, nombre y ubicación son obligatorios', 'danger')
            return redirect(url_for('activos.ingreso_rapido_legacy'))

        # Verificar que placa no exista
        existe = db.session.scalar(
            select(func.count()).select_from(Activo).where(Activo.placa_codigo_interno == placa)
        )
        if existe > 0:
            flash(f'Ya existe un activo con la placa {placa}', 'danger')
            return redirect(url_for('activos.ingreso_rapido_legacy'))

        # Insertar en tabla temporal
        try:
            query = text("""
                INSERT INTO activos_legacy_temporal (
                    placa_codigo_interno, nombre_activo, marca, modelo, serie,
                    ubicacion, estado_fisico, anios_uso_estimado,
                    valor_estimado_actual, fecha_hallazgo,
                    encontrado_por_usuario_id, notas_hallazgo,
                    requiere_investigacion, estado_incorporacion
                ) VALUES (
                    :placa, :nombre, :marca, :modelo, :serie,
                    :ubicacion, :estado_fisico, :anios_uso,
                    :valor_estimado, CURDATE(),
                    :usuario_id, :notas,
                    TRUE, 'pendiente'
                )
            """)

            db.session.execute(query, {
                'placa': placa,
                'nombre': nombre,
                'marca': request.form.get('marca'),
                'modelo': request.form.get('modelo'),
                'serie': request.form.get('serie'),
                'ubicacion': ubicacion,
                'estado_fisico': request.form.get('estado_fisico', 'Desconocido'),
                'anios_uso': request.form.get('anios_uso_estimado'),
                'valor_estimado': request.form.get('valor_estimado', 0),
                'usuario_id': current_user.id,
                'notas': request.form.get('notas_hallazgo')
            })
            db.session.commit()

            flash(f'Activo {placa} registrado para investigación', 'success')
            return redirect(url_for('activos.lista_legacy_pendientes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar activo: {e}', 'danger')
            return redirect(url_for('activos.ingreso_rapido_legacy'))

    # GET: Mostrar formulario
    clases = db.session.scalars(select(ClaseActivo).order_by(ClaseActivo.nombre_clase)).all()
    return render_template('ingreso_rapido_legacy.html', clases=clases)
```

**Template básico:**
```html
{% extends "base.html" %}

{% block title %}Ingreso Rápido - Activo Legacy{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>🔍 Ingreso Rápido - Activo No Registrado</h2>
    <p class="text-muted">
        Usa este formulario para registrar rápidamente activos encontrados que no están en el sistema.
    </p>

    <form method="POST" class="card p-4">
        {{ form.csrf_token }}

        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Placa/Código *</label>
                <input type="text" name="placa_codigo_interno" class="form-control" required>
            </div>
            <div class="col-md-6 mb-3">
                <label class="form-label">Nombre del Activo *</label>
                <input type="text" name="nombre_activo" class="form-control" required>
            </div>
        </div>

        <div class="row">
            <div class="col-md-4 mb-3">
                <label class="form-label">Marca</label>
                <input type="text" name="marca" class="form-control">
            </div>
            <div class="col-md-4 mb-3">
                <label class="form-label">Modelo</label>
                <input type="text" name="modelo" class="form-control">
            </div>
            <div class="col-md-4 mb-3">
                <label class="form-label">Serie</label>
                <input type="text" name="serie" class="form-control">
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label">Ubicación *</label>
            <input type="text" name="ubicacion" class="form-control"
                   placeholder="Ej: UCI Piso 3 - Sala 302" required>
        </div>

        <div class="row">
            <div class="col-md-6 mb-3">
                <label class="form-label">Estado Físico</label>
                <select name="estado_fisico" class="form-control">
                    <option value="Operativo">Operativo</option>
                    <option value="Requiere Mantenimiento">Requiere Mantenimiento</option>
                    <option value="Inoperativo">Inoperativo</option>
                    <option value="Desconocido">Desconocido</option>
                </select>
            </div>
            <div class="col-md-6 mb-3">
                <label class="form-label">Años de Uso Estimado</label>
                <input type="number" name="anios_uso_estimado" class="form-control"
                       min="0" max="50">
            </div>
        </div>

        <div class="mb-3">
            <label class="form-label">Notas del Hallazgo</label>
            <textarea name="notas_hallazgo" class="form-control" rows="3"
                      placeholder="Describe dónde y cómo encontraste este activo"></textarea>
        </div>

        <button type="submit" class="btn btn-success">
            <i class="fas fa-save"></i> Guardar para Investigación
        </button>
        <a href="{{ url_for('activos.ver_activos') }}" class="btn btn-secondary">Cancelar</a>
    </form>
</div>
{% endblock %}
```

---

### ✅ Tarea 2.2: Panel de gestión de activos en investigación

**Ruta Flask:**
```python
@activos_bp.route('/legacy-pendientes')
@login_required
def lista_legacy_pendientes():
    """Lista de activos legacy pendientes de investigación"""
    query = text("""
        SELECT * FROM vista_activos_legacy_pendientes
        ORDER BY dias_sin_investigar DESC
    """)
    activos = db.session.execute(query).fetchall()
    return render_template('lista_legacy_pendientes.html', activos=activos)
```

---

### ✅ Tarea 2.3: Función de incorporación definitiva

**Ruta Flask:**
```python
@activos_bp.route('/legacy/<int:legacy_id>/incorporar', methods=['POST'])
@login_required
@role_required('Admin', 'Gestor')
def incorporar_activo_legacy(legacy_id):
    """Incorpora un activo legacy aprobado a la tabla definitiva"""
    try:
        # Llamar stored procedure
        query = text("""
            CALL sp_incorporar_activo_legacy(:legacy_id, :usuario_id, @activo_id, @mensaje)
        """)
        db.session.execute(query, {'legacy_id': legacy_id, 'usuario_id': current_user.id})

        # Obtener resultados
        resultado = db.session.execute(text("SELECT @activo_id AS activo_id, @mensaje AS mensaje")).fetchone()

        flash(resultado.mensaje, 'success' if 'exitosamente' in resultado.mensaje else 'danger')
        return redirect(url_for('activos.ver_activos'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al incorporar activo: {e}', 'danger')
        return redirect(url_for('activos.lista_legacy_pendientes'))
```

---

## 🟡 FASE 3: OPTIMIZACIONES (Prioridad media - 1 semana)

### ✅ Tarea 3.1: Índices de rendimiento

**Ejecutar:**
```sql
-- Índices para búsquedas frecuentes
CREATE INDEX idx_activos_estado_conciliacion ON activos(estado_conciliacion, fecha_ultima_verificacion);
CREATE INDEX idx_activos_funcionario_estado ON activos(funcionario_id, estado);
CREATE INDEX idx_activos_valor_comercial ON activos(valor_comercial DESC);

-- Índices para reportes
CREATE INDEX idx_movimientos_fecha_tipo ON movimientos(fecha, tipo_movimiento);
CREATE INDEX idx_activo_historico_timestamp ON activo_historico(timestamp DESC);
```

---

### ✅ Tarea 3.2: Decidir sobre sistema EAV

**MI RECOMENDACIÓN: Eliminar EAV** (0 registros en uso)

**Opción A: Eliminar sistema EAV (RECOMENDADO)**
```sql
-- Backup por si acaso
mysqldump jerosmart_activos categoria_activo atributo_definicion atributo_valor > backup_eav.sql

-- Eliminar tablas
DROP TABLE atributo_valor;
DROP TABLE atributo_definicion;
DROP TABLE categoria_activo;
```

**Luego en `app/models.py`:**
- Eliminar clases: `CategoriaActivo`, `AtributoDefinicion`, `AtributoValor`
- Usar solo `atributos_dinamicos_json` (ya funciona)

**Ventajas:**
- ✅ Menos complejidad
- ✅ Más rápido (JSON nativo en MySQL 8.0)
- ✅ Elimina el error actual de `updated_by`
- ✅ No necesitas migrar datos (0 registros)

---

## 🟢 FASE 4: REPORTES Y ANÁLISIS (Baja prioridad - 1 semana)

### ✅ Tarea 4.1: Reporte de valoración contable

**Stored Procedure:**
```sql
DELIMITER $$
CREATE PROCEDURE sp_reporte_balance_activos(IN p_fecha_corte DATE)
BEGIN
    SELECT
        c.nombre_clase,
        COUNT(a.id) AS cantidad_activos,
        SUM(a.valor_comercial) AS costo_historico,
        SUM(v.depreciacion_acumulada) AS depreciacion_acumulada,
        SUM(v.valor_libros) AS valor_en_libros,
        ROUND(SUM(v.depreciacion_acumulada) / SUM(a.valor_comercial) * 100, 2) AS porcentaje_depreciacion
    FROM activos a
    JOIN vista_activos_valoracion v ON a.id = v.id
    LEFT JOIN clases_activo c ON a.clase_id = c.id
    WHERE a.created_at <= p_fecha_corte
    GROUP BY c.id, c.nombre_clase WITH ROLLUP
    ORDER BY costo_historico DESC;
END$$
DELIMITER ;
```

---

## 📝 CHECKLIST DE PROGRESO

### INMEDIATO ✅
- [ ] Agregar columna `updated_by`
- [ ] Verificar que se puede eliminar activos

### FASE 1 - CRÍTICO 🔴
- [ ] Ejecutar migración depreciación
- [ ] Ejecutar migración sistema legacy
- [ ] Actualizar models.py con nuevos campos
- [ ] Probar cálculos de depreciación

### FASE 2 - FUNCIONALIDADES 🟠
- [ ] Crear formulario ingreso rápido
- [ ] Crear panel de gestión legacy
- [ ] Implementar función de incorporación
- [ ] Probar flujo completo

### FASE 3 - OPTIMIZACIÓN 🟡
- [ ] Crear índices
- [ ] Decidir sobre EAV (eliminar recomendado)
- [ ] Limpiar código si se elimina EAV

### FASE 4 - REPORTES 🟢
- [ ] Crear stored procedures de reportes
- [ ] Dashboard de valoración
- [ ] Reportes de conciliación

---

## 🎓 CAPACITACIÓN REQUERIDA

### Para Usuarios:
1. Uso del formulario de ingreso rápido
2. Interpretación de estados de activos legacy
3. Proceso de investigación

### Para Administradores:
1. Aprobación de activos legacy
2. Incorporación definitiva
3. Generación de reportes contables

---

## 📞 SOPORTE Y DUDAS

**Problemas comunes:**

1. **Error al ejecutar SQL:** Verificar permisos de usuario MySQL
2. **Columna `updated_by` no se crea:** Ejecutar script manualmente en Workbench
3. **Formulario no guarda:** Verificar CSRF token

**Contacto:** Documentar dudas en el archivo `DUDAS_Y_SOLUCIONES.md`

---

**Última actualización:** 2025-11-25
**Estado:** Plan listo para ejecución
