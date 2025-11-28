# 📊 ANÁLISIS COMPLETO DEL SISTEMA DE ACTIVOS FIJOS - JeroSmart

**Fecha:** 2025-11-25
**Analista:** Claude (Emulando Consultor Senior de Activos Fijos)
**Cliente:** Clínica - Sistema JeroSmart Activos
**Base de Datos:** MySQL 8.0 - `jerosmart_activos`

---

## 📋 RESUMEN EJECUTIVO

### Situación Actual
- **Total de activos registrados:** 6,629
- **Funcionarios:** 633
- **Proveedores:** En base de datos
- **Movimientos registrados:** 3
- **Sistema:** Flask + SQLAlchemy ORM + MySQL
- **Problemática principal:** Activos "fantasma" operativos sin depreciación por 10+ años

### Hallazgos Críticos
1. ⚠️ **0 registros en `atributo_valor`** - Sistema EAV sin usar
2. ⚠️ **Falta columna `updated_by`** - Auditoría incompleta
3. ⚠️ **Activos legacy sin trazabilidad** - Migración desde sistema anterior
4. ✅ **Sistema de conciliación física implementado** - Buena práctica
5. ✅ **Auditoría histórica (`activo_historico`)** - Cumple NIIF

---

## 🗄️ ANÁLISIS DETALLADO DE LA ESTRUCTURA DE BASE DE DATOS

### 1. DIAGRAMA CONCEPTUAL DE ENTIDADES

```
┌─────────────────────────────────────────────────────────────────┐
│                     MÓDULO CORE - ACTIVOS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐         ┌──────────────┐                      │
│  │  Usuarios   │────────▶│  Activos     │◀──────┐              │
│  │  (2 regs)   │ audita  │  (6,629)     │       │              │
│  └─────────────┘         └──────┬───────┘       │              │
│                                 │                │              │
│                    ┌────────────┼────────────────┘              │
│                    │            │                               │
│         ┌──────────▼─┐   ┌─────▼──────────┐                   │
│         │ Funcionarios│   │ ClaseActivo    │                   │
│         │  (633 regs) │   │ (Biomédico,    │                   │
│         └─────────────┘   │  TICs, etc)    │                   │
│                            └────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              MÓDULO EAV - ATRIBUTOS DINÁMICOS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌────────────────────┐              │
│  │ CategoriaActivo  │─────▶│ AtributoDefinicion │              │
│  │   (5 categorías) │  1:N │    (10 atributos)  │              │
│  └──────────────────┘      └─────────┬──────────┘              │
│           │                           │                          │
│           │ 1:N                       │ 1:N                      │
│           ▼                           ▼                          │
│    ┌──────────┐              ┌────────────────┐                │
│    │  Activos │─────────────▶│ AtributoValor  │                │
│    └──────────┘      1:N     │  (0 registros) │ ⚠️ SIN USAR    │
│                               └────────────────┘                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│           MÓDULO MOVIMIENTOS Y TRAZABILIDAD                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐       ┌──────────────────┐                 │
│  │  Movimientos   │──────▶│ MovimientoActivo │                 │
│  │   (3 regs)     │  1:N  │                  │                 │
│  └────────┬───────┘       └──────────────────┘                 │
│           │                                                      │
│    ┌──────┴─────────┬──────────────┬────────────┐             │
│    ▼                ▼              ▼            ▼              │
│ DetalleEntrega  DetalleTraslado  DetalleES  DetallePazSalvo    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              MÓDULO AUDITORÍA Y CUMPLIMIENTO                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐        ┌────────────────────┐            │
│  │ ActivoHistorico  │───────▶│  Activos           │            │
│  │ (Trazabilidad    │  N:1   │  (estado_          │            │
│  │  legal completa) │        │   conciliacion)    │            │
│  └──────────────────┘        └────────────────────┘            │
│          ✅ NIIF                    ✅ Anti-Fantasma            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 ANÁLISIS POR MÓDULO

### **MÓDULO 1: GESTIÓN CORE DE ACTIVOS**

#### Tabla: `activos` (6,629 registros)

**Campos Críticos:**
```sql
- id, placa_codigo_interno (PK/UK) ✅
- nombre_activo, marca, modelo, serie ✅
- valor_comercial, estado ✅
- created_at (fecha de ingreso) ✅
- tipo_propiedad (Propio/Ajeno/Comodato) ✅
- clase_id → ClaseActivo ✅
- funcionario_id → Responsable ✅
- categoria_id → CategoriaActivo (EAV) ⚠️ Subutilizado
```

**FASE 1.1: Sistema Anti-Activos Fantasma** ✅
```sql
- estado_conciliacion (Verificado/Pendiente/No Encontrado)
- fecha_ultima_verificacion
- usuario_ultima_verificacion_id
- notas_verificacion
```

**HALLAZGO CRÍTICO #1:**
```
⚠️ Campo `created_at` usado como "fecha de ingreso" para depreciación
   PROBLEMA: Activos migrados tienen created_at = fecha de migración,
             NO la fecha real de adquisición.

   IMPACTO: Cálculo de depreciación INCORRECTO para 6,629 activos legacy.
```

**RECOMENDACIÓN #1:**
```sql
ALTER TABLE activos
ADD COLUMN fecha_adquisicion DATE NULL COMMENT 'Fecha real de compra/adquisición',
ADD COLUMN fecha_alta_sistema DATE NULL COMMENT 'Fecha de registro en sistema',
ADD COLUMN es_activo_legacy BOOLEAN DEFAULT FALSE COMMENT 'Migrado de sistema anterior',
ADD COLUMN depreciacion_manual DECIMAL(15,2) NULL COMMENT 'Depreciación acumulada al migrar';
```

---

#### Tabla: `activo_historico` (Auditoría NIIF) ✅

**Fortalezas:**
- ✅ Registra TODOS los cambios (campo_modificado, valor_anterior, valor_nuevo)
- ✅ Captura usuario_id, timestamp, ip_address, user_agent
- ✅ Tipos de operación: CREATE, UPDATE, DELETE, VERIFICACION
- ✅ Índices compuestos para consultas eficientes

**HALLAZGO CRÍTICO #2:**
```
⚠️ SQLAlchemy Events (triggers en Python) para auditoría
   PROBLEMA: Si se ejecuta SQL directo, la auditoría NO se registra.
   RIESGO: Pérdida de trazabilidad legal si hay operaciones manuales.
```

**RECOMENDACIÓN #2:**
```sql
-- Crear TRIGGERS MySQL nativos como respaldo
DELIMITER $$
CREATE TRIGGER activos_after_update
AFTER UPDATE ON activos
FOR EACH ROW
BEGIN
    IF OLD.estado != NEW.estado THEN
        INSERT INTO activo_historico
        (activo_id, campo_modificado, valor_anterior, valor_nuevo,
         tipo_operacion, timestamp)
        VALUES
        (NEW.id, 'estado', OLD.estado, NEW.estado, 'UPDATE_MANUAL', NOW());
    END IF;
END$$
DELIMITER ;
```

---

### **MÓDULO 2: SISTEMA EAV (Entity-Attribute-Value)**

#### Tabla: `categoria_activo` (5 categorías)
```
Categorías definidas:
1. Equipos Biomédicos
2. Electroindustrial
3. TICs (Tecnología de Información)
4. Muebles y Enseres
5. (Otra categoría)
```

#### Tabla: `atributo_definicion` (10 atributos)
```
Atributos personalizados por categoría (Ej: voltaje, procesador, vida_útil)
```

#### Tabla: `atributo_valor` ⚠️ **0 REGISTROS**

**HALLAZGO CRÍTICO #3:**
```
⚠️ Sistema EAV implementado pero NO UTILIZADO
   - 10 definiciones de atributos creadas
   - 0 valores asignados a activos
   - Columna `updated_by` faltante (causa del error actual)

   CAUSA PROBABLE: Migración incompleta desde SQLite a MySQL
```

**PROBLEMA DETECTADO:**
```python
# En models.py, línea 1330
updated_by = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

# MySQL no tiene esta columna → Error al eliminar activos
# Activos con atributos_valores relacionados fallan al cargar
```

**RECOMENDACIÓN #3:**
```
OPCIÓN A: Migrar a EAV completo (largo plazo)
  - Migrar atributos_dinamicos_json → atributo_valor
  - Aprovechar búsquedas tipadas y validaciones
  - Mejor para reportes analíticos

OPCIÓN B: Deprecar EAV, usar solo JSON (corto plazo) ⭐ RECOMENDADO
  - Eliminar tablas EAV sin usar
  - Usar atributos_dinamicos_json (ya implementado)
  - MySQL 8.0 soporta JSON nativo con índices
  - Más rápido para tu caso de uso
```

---

### **MÓDULO 3: MOVIMIENTOS Y TRAZABILIDAD**

#### Tabla: `movimientos` (3 registros)

**Tipos implementados:**
1. **Entrega** → `detalles_entrega`
2. **Traslado** → `detalles_traslado`
3. **Entrada/Salida** → `detalles_entrada_salida`
4. **Paz y Salvo** → `detalles_paz_salvo`

**HALLAZGO CRÍTICO #4:**
```
⚠️ Solo 3 movimientos registrados vs 6,629 activos
   PROBLEMA: Activos migrados no tienen historial de movimientos.
   IMPACTO: No se puede rastrear ubicación/responsable histórico.
```

**FORTALEZAS:**
- ✅ Sistema de aprobación multinivel (estado_aprobacion, aprobado_por_id)
- ✅ Borradores (estado_completitud: 'borrador', 'completo')
- ✅ Snapshot contable (valor_comercial_momento, valor_libros_momento)
- ✅ Firmas digitales con metadatos legales (ip_address, timestamp, hash)

---

### **MÓDULO 4: DEPRECIACIÓN Y VALORACIÓN CONTABLE**

**Implementación actual (models.py, líneas 186-221):**

```python
@property
def depreciacion_acumulada(self):
    """Método de línea recta"""
    vida_util_anios = 10  # Default
    if self.clase_id == 1:  # Biomédico
        vida_util_anios = self.atributos_dinamicos_json.get('vida_util', 10)
    elif self.clase_id == 3:  # TICs
        vida_util_anios = 5

    fecha_compra = self.created_at  # ⚠️ PROBLEMA AQUÍ
    anios_transcurridos = (datetime.now() - fecha_compra).days / 365.25

    depreciacion_anual = self.valor_comercial / vida_util_anios
    depreciacion_total = depreciacion_anual * anios_transcurridos
    return min(depreciacion_total, self.valor_comercial)
```

**HALLAZGO CRÍTICO #5:**
```
⚠️ CÁLCULO DE DEPRECIACIÓN INCORRECTO PARA ACTIVOS LEGACY

Ejemplo real de tu caso:
  - Activo comprado en 2010 (15 años atrás)
  - Migrado al sistema en 2024
  - created_at = 2024 → Sistema calcula depreciación desde 2024
  - RESULTADO: Activo aparece "nuevo" cuando en realidad está 100% depreciado

IMPACTO FINANCIERO:
  - Balance general con sobrevaluación de activos
  - Incumplimiento NIIF (valoración incorrecta)
  - Imposibilidad de generar reportes contables confiables
```

**RECOMENDACIÓN #5 (CRÍTICA):**
```sql
-- 1. Agregar campos para manejo correcto de depreciación
ALTER TABLE activos
ADD COLUMN fecha_adquisicion DATE NULL,
ADD COLUMN depreciacion_acumulada_historica DECIMAL(15,2) DEFAULT 0,
ADD COLUMN valor_residual DECIMAL(15,2) DEFAULT 0,
ADD COLUMN metodo_depreciacion ENUM('linea_recta', 'unidades_produccion', 'saldos_decrecientes', 'manual') DEFAULT 'linea_recta',
ADD COLUMN vida_util_restante_meses INT NULL;

-- 2. Para activos legacy (sin fecha de adquisición conocida)
UPDATE activos
SET fecha_adquisicion = created_at,
    es_activo_legacy = TRUE
WHERE created_at < '2024-01-01';  -- Ajustar fecha según tu migración

-- 3. Para activos totalmente depreciados pero operativos
UPDATE activos
SET depreciacion_acumulada_historica = valor_comercial,
    valor_residual = 0,
    vida_util_restante_meses = 0,
    observaciones = CONCAT(observaciones, ' | ACTIVO TOTALMENTE DEPRECIADO - OPERATIVO')
WHERE TIMESTAMPDIFF(YEAR, created_at, NOW()) >= 10;
```

---

## 🏥 ANÁLISIS ESPECÍFICO PARA CLÍNICA

### Cumplimiento Normativo

#### ✅ Fortalezas:
1. **NIIF para PYMES Sección 17** (Propiedad, Planta y Equipo)
   - Registro de valor_comercial (costo inicial)
   - Cálculo de depreciación
   - Valor en libros

2. **Resolución 4725/2011 MinSalud** (Equipos Biomédicos)
   - Campo `clasificacion_riesgo` (I, IIa, IIb, III)
   - Campo `registro_invima`
   - Hoja de vida biomédica (tabla `hojas_vida_biomedicos`)

3. **Ley 527/1999 y Decreto 2364/2012** (Firma Electrónica)
   - Firmas con timestamp, IP, user_agent
   - Hash de documento para no-repudiación
   - Consentimiento legal registrado

#### ⚠️ Brechas:
1. **Inventario Físico Anual** (NIIF)
   - Sistema `estado_conciliacion` existe ✅
   - Pero: ¿Proceso definido? ¿Frecuencia? ¿Responsables?

2. **Mantenimiento de Equipos Biomédicos** (Res. 4725)
   - Tabla `mantenimientos` existe ✅
   - Pero: ¿0 registros en `atributo_valor` para periodicidad?

3. **Trazabilidad de Calibración**
   - Campo `requiere_calibracion` en JSON
   - Pero: ¿Dónde se registran las calibraciones realizadas?

---

## 💡 PROBLEMÁTICA: ACTIVOS "FANTASMA" OPERATIVOS

### Descripción del Problema

```
Tu caso específico:
- Activos operativos desde hace 10+ años
- Depreciación completa (100%)
- No están en ERP de la clínica
- No están en tus registros actuales
- Necesitas agregarlos fácilmente
```

### Solución Propuesta: **MODO INGRESO RÁPIDO PARA ACTIVOS LEGACY**

#### Tabla nueva: `activos_legacy_temporal`

```sql
CREATE TABLE activos_legacy_temporal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa_codigo_interno VARCHAR(100) UNIQUE NOT NULL,
    nombre_activo VARCHAR(200) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    serie VARCHAR(100),
    ubicacion VARCHAR(200),

    -- Campos específicos para legacy
    estado_fisico ENUM('Operativo', 'Requiere Mantenimiento', 'Inoperativo') DEFAULT 'Operativo',
    anios_uso_estimado INT COMMENT 'Años aproximados de uso',
    valor_estimado_actual DECIMAL(15,2) DEFAULT 0,

    -- Flags de investigación
    requiere_investigacion BOOLEAN DEFAULT TRUE,
    fecha_hallazgo DATE NOT NULL,
    usuario_registro_id INT,
    notas_investigacion TEXT,

    -- Estado de incorporación
    estado_incorporacion ENUM('pendiente', 'investigando', 'aprobado', 'rechazado') DEFAULT 'pendiente',
    fecha_aprobacion_incorporacion DATE NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_registro_id) REFERENCES usuarios(id),
    INDEX idx_estado_incorporacion (estado_incorporacion),
    INDEX idx_requiere_investigacion (requiere_investigacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### Flujo de trabajo:

```
1. HALLAZGO
   ├─ Usuario encuentra activo no registrado
   └─ Ingreso rápido → activos_legacy_temporal
       └─ Campos mínimos: placa, nombre, ubicación

2. INVESTIGACIÓN
   ├─ Buscar en ERP histórico
   ├─ Consultar factura/orden de compra
   ├─ Validar con responsable de área
   └─ Actualizar notas_investigacion

3. APROBACIÓN
   ├─ Jefe de activos fijos revisa
   ├─ Si aprobado:
   │   └─ Migrar a tabla `activos` definitiva
   │       ├─ fecha_adquisicion = estimada
   │       ├─ depreciacion_acumulada_historica = valor_estimado
   │       ├─ es_activo_legacy = TRUE
   │       └─ valor_comercial = valor_estimado + depreciacion
   └─ Si rechazado: marcar para baja

4. INCORPORACIÓN DEFINITIVA
   └─ Activo ya está en sistema principal con trazabilidad completa
```

---

## 🔧 ORM (SQLAlchemy) vs SQL CRUDO - ANÁLISIS PROFESIONAL

### Mi Opinión Directa: **MANTENER SQLAlchemy ORM** ⭐

#### ¿Por qué?

```
MySQL sí soporta SQL crudo, PERO tu sistema tiene:
  ✅ 28 tablas interrelacionadas
  ✅ Relaciones complejas (1:1, 1:N, N:M)
  ✅ Triggers en Python (event listeners)
  ✅ Validaciones de negocio
  ✅ Sistema de auditoría automático

Reescribir todo en SQL crudo = 300+ horas de trabajo
```

### Comparación Detallada

| Aspecto | SQLAlchemy ORM ✅ | SQL Crudo |
|---------|-------------------|-----------|
| **Productividad** | Alta (menos líneas de código) | Baja (verbose) |
| **Seguridad** | Protección contra SQL Injection | Requiere sanitización manual |
| **Mantenibilidad** | Alta (cambios en modelos se propagan) | Baja (cambiar 100+ queries) |
| **Rendimiento** | 95% casos aceptable | 5% más rápido en queries complejas |
| **Portabilidad** | Soporta MySQL, PostgreSQL, SQLite | Queries específicas por DB |
| **Curva de aprendizaje** | Ya está implementado | Tu equipo debe aprender SQL avanzado |
| **Auditoría automática** | Event listeners funcionan ✅ | Tienes que crear triggers MySQL |

### Casos donde SQL crudo SÍ es mejor:

```python
# 1. Reportes pesados con agregaciones complejas
# MALO con ORM:
activos = Activo.query.join(Funcionario).join(ClaseActivo).filter(...).all()
for activo in activos:  # ⚠️ N+1 queries
    calculos...

# BUENO con SQL:
query = """
SELECT
    a.id, a.nombre_activo, a.valor_comercial,
    a.valor_comercial - (a.valor_comercial * TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW()) / 10) AS valor_libros,
    f.nombres, f.apellidos,
    c.nombre_clase
FROM activos a
LEFT JOIN funcionarios f ON a.funcionario_id = f.id
LEFT JOIN clases_activo c ON a.clase_id = c.id
WHERE a.estado_conciliacion = 'Verificado'
"""
resultados = db.session.execute(text(query)).fetchall()
```

```python
# 2. Operaciones masivas (bulk updates)
# MALO con ORM:
for activo in activos:
    activo.estado = 'Verificado'
db.session.commit()  # ⚠️ 1000 UPDATE statements

# BUENO con SQL:
db.session.execute(text("""
    UPDATE activos
    SET estado_conciliacion = 'Verificado',
        fecha_ultima_verificacion = NOW()
    WHERE id IN :ids
"""), {'ids': [1,2,3,...,1000]})
```

### **MI RECOMENDACIÓN: ENFOQUE HÍBRIDO** ⭐⭐⭐

```python
# Use ORM for:
✅ CRUD operations (Create, Read, Update, Delete)
✅ Business logic
✅ Relationships and joins
✅ Validations
✅ Auditoría automática

# Use SQL crudo for:
✅ Reportes complejos
✅ Operaciones masivas (bulk)
✅ Migraciones de datos
✅ Análisis de depreciación masiva
✅ Stored procedures (si los necesitas)
```

---

## 📝 PLAN DE ACCIÓN DETALLADO

### FASE 1: CORRECCIONES CRÍTICAS (1-2 días)

#### ✅ **Tarea 1.1: Agregar columna `updated_by` a MySQL**
```bash
python agregar_columna_updated_by.py
```

#### ✅ **Tarea 1.2: Agregar campos para manejo correcto de depreciación**
```sql
-- Script: migracion_depreciacion_correcta.sql
ALTER TABLE activos
ADD COLUMN fecha_adquisicion DATE NULL AFTER created_at,
ADD COLUMN depreciacion_acumulada_historica DECIMAL(15,2) DEFAULT 0 AFTER valor_comercial,
ADD COLUMN es_activo_legacy BOOLEAN DEFAULT FALSE AFTER tipo_propiedad,
ADD COLUMN observaciones_depreciacion TEXT NULL;

-- Inicializar valores para activos existentes
UPDATE activos
SET fecha_adquisicion = created_at,
    es_activo_legacy = TRUE
WHERE created_at < '2024-01-01';
```

#### ✅ **Tarea 1.3: Crear tabla de ingreso rápido para activos legacy**
```sql
-- Ejecutar script SQL completo de activos_legacy_temporal (ver arriba)
```

---

### FASE 2: OPTIMIZACIONES DE ESTRUCTURA (3-5 días)

#### **Tarea 2.1: Decisión sobre sistema EAV**

**OPCIÓN A: Eliminar EAV (RECOMENDADO para tu caso)**
```sql
-- 1. Backup de seguridad
mysqldump jerosmart_activos categoria_activo atributo_definicion atributo_valor > backup_eav.sql

-- 2. Eliminar tablas sin usar
DROP TABLE atributo_valor;
DROP TABLE atributo_definicion;
DROP TABLE categoria_activo;

-- 3. Limpiar modelos en models.py (eliminar clases EAV)

-- 4. Usar solo atributos_dinamicos_json con índices JSON
CREATE INDEX idx_atributos_registro_invima
ON activos((CAST(atributos_dinamicos_json->>'$.registro_invima' AS CHAR(100))));
```

**OPCIÓN B: Activar EAV completamente**
```python
# Migrar datos de JSON → EAV
# Script: migrar_json_a_eav.py
# (Solo si realmente necesitas búsquedas tipadas complejas)
```

#### **Tarea 2.2: Crear índices estratégicos**
```sql
-- Para búsquedas frecuentes
CREATE INDEX idx_activos_estado_conciliacion ON activos(estado_conciliacion, fecha_ultima_verificacion);
CREATE INDEX idx_activos_funcionario_estado ON activos(funcionario_id, estado);
CREATE INDEX idx_activos_valor_comercial ON activos(valor_comercial DESC);
CREATE INDEX idx_activos_fecha_adquisicion ON activos(fecha_adquisicion);

-- Para reportes contables
CREATE INDEX idx_movimientos_fecha_tipo ON movimientos(fecha, tipo_movimiento);
CREATE INDEX idx_activo_historico_timestamp ON activo_historico(timestamp DESC);
```

#### **Tarea 2.3: Crear vistas materializadas para reportes frecuentes**
```sql
CREATE VIEW vista_activos_valoracion AS
SELECT
    a.id,
    a.placa_codigo_interno,
    a.nombre_activo,
    a.valor_comercial,
    a.depreciacion_acumulada_historica,
    CASE
        WHEN a.fecha_adquisicion IS NULL THEN 0
        ELSE a.valor_comercial -
             (a.valor_comercial * LEAST(TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, NOW()) / 10, 1))
    END AS valor_libros_calculado,
    a.estado,
    a.es_activo_legacy,
    f.nombres AS responsable_nombres,
    f.apellidos AS responsable_apellidos,
    c.nombre_clase AS clase
FROM activos a
LEFT JOIN funcionarios f ON a.funcionario_id = f.id
LEFT JOIN clases_activo c ON a.clase_id = c.id;
```

---

### FASE 3: FUNCIONALIDADES NUEVAS (1 semana)

#### **Tarea 3.1: Pantalla de ingreso rápido de activos legacy**

**Mockup del formulario:**
```
┌─────────────────────────────────────────────────────────┐
│  🔍 INGRESO RÁPIDO - ACTIVO NO REGISTRADO             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Placa/Código:  [__________________]  (REQUERIDO)      │
│  Nombre:        [__________________]  (REQUERIDO)      │
│  Marca:         [__________________]                    │
│  Modelo:        [__________________]                    │
│  Serie:         [__________________]                    │
│  Ubicación:     [__________________]  (REQUERIDO)      │
│                                                          │
│  Estado físico: ( ) Operativo                           │
│                 ( ) Requiere Mantenimiento              │
│                 ( ) Inoperativo                         │
│                                                          │
│  Años de uso estimado: [___] años                       │
│                                                          │
│  Notas de hallazgo:                                     │
│  [____________________________________________]          │
│  [____________________________________________]          │
│                                                          │
│  ☐ Este activo requiere investigación adicional        │
│                                                          │
│  [GUARDAR PARA INVESTIGACIÓN]  [CANCELAR]              │
└─────────────────────────────────────────────────────────┘
```

**Endpoint Flask:**
```python
@activos_bp.route('/ingreso-rapido-legacy', methods=['GET', 'POST'])
@login_required
def ingreso_rapido_legacy():
    if request.method == 'POST':
        # Validar solo campos mínimos
        # Insertar en activos_legacy_temporal
        # Flash success
        # Redirect a lista de activos pendientes investigación
    return render_template('ingreso_rapido_legacy.html')
```

#### **Tarea 3.2: Panel de gestión de activos en investigación**

```
┌─────────────────────────────────────────────────────────┐
│  📋 ACTIVOS EN INVESTIGACIÓN                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Pendientes: 23  |  En Investigación: 8  |  Aprobados: 5│
│                                                          │
│  ┌────────────────────────────────────────────────────┐│
│  │ Placa: AFX-001  │  Hallado: 2025-11-20            ││
│  │ Nombre: Monitor de Signos Vitales                 ││
│  │ Estado: En Investigación                           ││
│  │                                                     ││
│  │ [VER DETALLES]  [APROBAR]  [RECHAZAR]             ││
│  └────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### **Tarea 3.3: Script de incorporación definitiva**
```python
# Script: incorporar_activo_legacy.py
def incorporar_activo_temporal_a_definitivo(activo_temp_id, datos_adicionales):
    """
    Migra activo desde activos_legacy_temporal → activos
    Con cálculo correcto de depreciación histórica
    """
    # 1. Obtener datos temporales
    # 2. Calcular depreciación acumulada histórica
    # 3. Crear registro en tabla activos
    # 4. Registrar en activo_historico
    # 5. Marcar temporal como 'incorporado'
```

---

### FASE 4: MEJORAS DE RENDIMIENTO Y REPORTES (1 semana)

#### **Tarea 4.1: Stored Procedures para reportes contables**

```sql
DELIMITER $$
CREATE PROCEDURE sp_reporte_valoracion_activos(
    IN p_fecha_corte DATE,
    IN p_clase_id INT
)
BEGIN
    SELECT
        c.nombre_clase,
        COUNT(a.id) AS total_activos,
        SUM(a.valor_comercial) AS valor_original_total,
        SUM(CASE
            WHEN a.fecha_adquisicion IS NOT NULL THEN
                a.valor_comercial - (a.valor_comercial *
                    LEAST(TIMESTAMPDIFF(YEAR, a.fecha_adquisicion, p_fecha_corte) / 10, 1))
            ELSE
                a.valor_comercial - a.depreciacion_acumulada_historica
        END) AS valor_libros_total,
        SUM(a.depreciacion_acumulada_historica) AS depreciacion_acumulada_total
    FROM activos a
    JOIN clases_activo c ON a.clase_id = c.id
    WHERE (p_clase_id IS NULL OR a.clase_id = p_clase_id)
        AND a.created_at <= p_fecha_corte
    GROUP BY c.id, c.nombre_clase
    ORDER BY valor_original_total DESC;
END$$
DELIMITER ;

-- Uso desde Python:
# db.session.execute(text("CALL sp_reporte_valoracion_activos(:fecha, :clase)"),
#                    {"fecha": "2025-12-31", "clase": None})
```

#### **Tarea 4.2: Dashboard de conciliación física**

```python
# Métricas clave:
- % activos verificados vs pendientes
- Activos "No Encontrados" (alertas)
- Días desde última verificación por ubicación
- Top 10 ubicaciones con más activos sin verificar
```

---

### FASE 5: DOCUMENTACIÓN Y CAPACITACIÓN (3 días)

#### **Tarea 5.1: Manual de procedimientos**
- Ingreso de activos nuevos (compra)
- Ingreso de activos legacy encontrados
- Proceso de investigación
- Conciliación física anual
- Generación de reportes contables

#### **Tarea 5.2: Capacitación a usuarios**
- Uso del sistema de ingreso rápido
- Interpretación de estados de conciliación
- Generación de reportes

---

## 🎯 RESUMEN DE DECISIONES CLAVE

### **DECISIÓN #1: ¿ORM o SQL Crudo?**
**RESPUESTA: Híbrido con predominio ORM (80% ORM / 20% SQL)**

**Justificación:**
- ✅ Código ya existe y funciona
- ✅ Equipo familiarizado con SQLAlchemy
- ✅ Auditoría automática con event listeners
- ✅ SQL crudo solo para reportes pesados

---

### **DECISIÓN #2: ¿Mantener o eliminar sistema EAV?**
**RESPUESTA: Eliminar EAV, usar solo JSON**

**Justificación:**
- 0 registros en `atributo_valor` → No se usa
- MySQL 8.0 soporta JSON con índices eficientes
- Menos complejidad = menos errores
- Campo `atributos_dinamicos_json` ya implementado y funcional

---

### **DECISIÓN #3: ¿Cómo manejar activos legacy?**
**RESPUESTA: Tabla temporal + flujo de investigación**

**Justificación:**
- No contaminar tabla principal con datos incompletos
- Permitir ingreso rápido en campo
- Proceso de validación antes de incorporación definitiva
- Trazabilidad de hallazgos

---

## 📊 MÉTRICAS DE ÉXITO

### Corto Plazo (1 mes)
- ✅ 0 errores al eliminar activos
- ✅ 100% activos legacy con `fecha_adquisicion` definida
- ✅ Sistema de ingreso rápido operativo
- ✅ Al menos 50 activos legacy incorporados

### Mediano Plazo (3 meses)
- ✅ 80% activos con `estado_conciliacion = 'Verificado'`
- ✅ Reportes contables con valoración correcta
- ✅ Tiempo promedio de investigación < 5 días
- ✅ 0 activos duplicados

### Largo Plazo (6 meses)
- ✅ 100% activos verificados
- ✅ Auditoría NIIF completa
- ✅ Integración con ERP de la clínica
- ✅ Dashboard de KPIs operativo

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Pérdida de datos en migración | Media | Alto | Backups antes de cada cambio |
| Resistencia al cambio (usuarios) | Alta | Medio | Capacitación + formularios simples |
| Inconsistencia en datos legacy | Alta | Alto | Proceso de investigación obligatorio |
| Sobrecarga de sistema con 6K+ activos | Baja | Medio | Índices + queries optimizadas |

---

## 💰 ESTIMACIÓN DE ESFUERZO

| Fase | Días | Prioridad |
|------|------|-----------|
| Fase 1: Correcciones críticas | 1-2 | 🔴 CRÍTICO |
| Fase 2: Optimizaciones estructura | 3-5 | 🟠 ALTA |
| Fase 3: Funcionalidades nuevas | 5-7 | 🟡 MEDIA |
| Fase 4: Reportes y rendimiento | 5-7 | 🟢 BAJA |
| Fase 5: Documentación | 2-3 | 🟢 BAJA |
| **TOTAL** | **16-24 días** | |

---

## 📞 SIGUIENTE PASO INMEDIATO

```bash
# 1. Ejecutar migración pendiente
python agregar_columna_updated_by.py

# 2. Verificar que funcione
python verificar_bd.py

# 3. Probar eliminar activo duplicado
# (Ya debería funcionar sin errores)
```

---

**Documento generado por:** Claude (Análisis Profesional)
**Fecha:** 2025-11-25
**Versión:** 1.0
**Estado:** Para revisión y aprobación
