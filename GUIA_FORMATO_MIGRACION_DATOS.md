# 📋 GUÍA DE FORMATO PARA MIGRACIÓN DE DATOS - Activos Legacy

## 🎯 Propósito
Esta guía explica el formato EXACTO que debe tener cada dato al migrar activos legacy o corregir información de activos existentes.

---

## 📅 FORMATO DE FECHAS

### ✅ Formato Correcto: `YYYY-MM-DD`

**Estructura:**
- `YYYY` = Año (4 dígitos)
- `MM` = Mes (2 dígitos, con cero inicial si es necesario)
- `DD` = Día (2 dígitos, con cero inicial si es necesario)

**Ejemplos válidos:**
```sql
'2015-03-15'  -- ✅ 15 de marzo de 2015
'2010-01-05'  -- ✅ 5 de enero de 2010
'2024-12-31'  -- ✅ 31 de diciembre de 2024
'2000-11-20'  -- ✅ 20 de noviembre de 2000
```

**Ejemplos INVÁLIDOS:**
```sql
'15/03/2015'  -- ❌ Formato DD/MM/YYYY (no permitido)
'2015-3-15'   -- ❌ Mes sin cero inicial
'15-03-2015'  -- ❌ Orden incorrecto
'2015/03/15'  -- ❌ Separador incorrecto (usar guiones -)
```

### 🔧 Conversión Desde Excel/CSV

Si tienes fechas en Excel con formato DD/MM/YYYY:

**Opción 1: Fórmula Excel**
```excel
=TEXT(A1,"YYYY-MM-DD")
```

**Opción 2: Python**
```python
from datetime import datetime

# Convertir DD/MM/YYYY a YYYY-MM-DD
fecha_original = "15/03/2015"
fecha_convertida = datetime.strptime(fecha_original, "%d/%m/%Y").strftime("%Y-%m-%d")
print(fecha_convertida)  # 2015-03-15
```

---

## 💰 FORMATO DE VALORES MONETARIOS

### ✅ Formato Correcto: `DECIMAL(15,2)`

**Estructura:**
- Hasta 15 dígitos en total
- Exactamente 2 decimales
- Sin separadores de miles
- Punto (.) como separador decimal

**Ejemplos válidos:**
```sql
125000000.00    -- ✅ $125,000,000 COP
5500000.50      -- ✅ $5,500,000.50 COP
0.00            -- ✅ Cero
999999999999.99 -- ✅ Valor máximo
```

**Ejemplos INVÁLIDOS:**
```sql
125,000,000.00  -- ❌ Separadores de miles no permitidos
125000000       -- ❌ Falta .00 (debe tener decimales)
125.000.000,00  -- ❌ Formato europeo (no permitido)
$125000000.00   -- ❌ Símbolo de moneda no permitido
```

### 🔧 Conversión Desde Excel

**Opción 1: Formatear en Excel**
```excel
=ROUND(A1,2)  -- Redondea a 2 decimales
```

**Opción 2: Python**
```python
valor_con_formato = "125,000,000.50"
valor_limpio = float(valor_con_formato.replace(",", ""))
print(f"{valor_limpio:.2f}")  # 125000000.50
```

---

## 🏷️ FORMATO DE PLACAS/CÓDIGOS

### ✅ Formato Correcto: `VARCHAR(100)`

**Reglas:**
- Máximo 100 caracteres
- Permitido: letras, números, guiones (-), guiones bajos (_)
- Sin espacios al inicio o final
- Debe ser ÚNICO (no puede repetirse)

**Ejemplos válidos:**
```sql
'AFX-001'           -- ✅
'BIO-2024-0123'     -- ✅
'EQUIPO_TIC_001'    -- ✅
'LEGACY-AFX-001'    -- ✅
```

**Ejemplos INVÁLIDOS:**
```sql
'AFX 001'           -- ⚠️ Espacio (mejor usar guión)
'  AFX-001  '       -- ❌ Espacios al inicio/final
''                  -- ❌ Vacío
NULL                -- ❌ NULL no permitido para placa
```

---

## 📊 FORMATO DE VALORES BOOLEANOS

### ✅ Formato Correcto: `TRUE` / `FALSE` o `1` / `0`

**Valores aceptados:**
```sql
TRUE    -- ✅ Verdadero
FALSE   -- ✅ Falso
1       -- ✅ Verdadero (equivalente a TRUE)
0       -- ✅ Falso (equivalente a FALSE)
```

**Valores INVÁLIDOS:**
```sql
'Si'    -- ❌
'No'    -- ❌
'Yes'   -- ❌
'true'  -- ⚠️ Funciona pero preferir TRUE en mayúsculas
NULL    -- ⚠️ Solo si el campo permite NULL
```

---

## 🔢 FORMATO DE NÚMEROS ENTEROS

### ✅ Formato Correcto: `INT`

**Reglas:**
- Solo números enteros (sin decimales)
- Rango: -2,147,483,648 a 2,147,483,647
- Sin separadores de miles

**Ejemplos válidos:**
```sql
10      -- ✅ Vida útil de 10 años
5       -- ✅ Vida útil de 5 años
120     -- ✅ 120 meses = 10 años
0       -- ✅ Cero
```

**Ejemplos INVÁLIDOS:**
```sql
10.5    -- ❌ Tiene decimales
'10'    -- ⚠️ Funciona pero mejor sin comillas
NULL    -- ⚠️ Solo si el campo permite NULL
```

---

## 📝 EJEMPLOS PRÁCTICOS DE MIGRACIÓN

### Ejemplo 1: Activo Legacy con Fecha Real de Compra

**Situación:** Tienes un monitor comprado el 15 de marzo de 2015 por $2,500,000 COP

```sql
UPDATE activos
SET
    fecha_adquisicion = '2015-03-15',           -- ✅ Formato YYYY-MM-DD
    costo_historico = 2500000.00,               -- ✅ Sin separadores, con .00
    depreciacion_acumulada_historica = 2500000.00,  -- ✅ Totalmente depreciado
    metodo_depreciacion = 'totalmente_depreciado',
    es_activo_legacy = TRUE,                    -- ✅ Es legacy
    observaciones_depreciacion = 'Fecha corregida según factura #FAC-2015-0234. Activo operativo pero totalmente depreciado.'
WHERE placa_codigo_interno = 'AFX-MON-001';
```

---

### Ejemplo 2: Activo TICs Reciente

**Situación:** Computador comprado el 5 de enero de 2022 por $3,800,000 COP

```sql
UPDATE activos
SET
    fecha_adquisicion = '2022-01-05',           -- ✅ 2022 (hace 3 años)
    costo_historico = 3800000.00,
    metodo_depreciacion = 'linea_recta',        -- ✅ Aún se deprecia
    vida_util_restante_meses = 24,              -- ✅ Le quedan 2 años (5 total - 3 transcurridos)
    es_activo_legacy = FALSE,                   -- ✅ No es legacy (compra reciente)
    observaciones_depreciacion = 'Equipo TICs con vida útil de 5 años. Comprado nuevo.'
WHERE placa_codigo_interno = 'TIC-PC-2022-001';
```

---

### Ejemplo 3: Activo Sin Fecha Conocida

**Situación:** Silla encontrada, sin documentación, uso estimado 12 años

```sql
UPDATE activos
SET
    fecha_adquisicion = NULL,                   -- ✅ NULL = fecha desconocida
    costo_historico = NULL,                     -- ✅ Costo desconocido
    depreciacion_acumulada_historica = 0.00,
    metodo_depreciacion = 'manual',             -- ✅ Manual porque no hay datos
    es_activo_legacy = TRUE,
    observaciones_depreciacion = 'Activo hallazgo sin documentación. Años de uso estimado: 12. Operativo. Costo y fecha desconocidos.'
WHERE placa_codigo_interno = 'LEGACY-SILLA-001';
```

---

### Ejemplo 4: Equipo Biomédico Parcialmente Depreciado

**Situación:** Electrocardiografo comprado 20/11/2020 por $18,500,000 COP, vida útil 10 años

```sql
UPDATE activos
SET
    fecha_adquisicion = '2020-11-20',           -- ✅ Hace ~4 años
    costo_historico = 18500000.00,
    metodo_depreciacion = 'linea_recta',
    vida_util_restante_meses = 72,              -- ✅ 6 años restantes (10 - 4)
    es_activo_legacy = TRUE,
    observaciones_depreciacion = 'Equipo biomédico según Res. 4725/2011. Vida útil: 10 años. Fecha según factura #BIO-2020-0456.'
WHERE placa_codigo_interno = 'BIO-ECG-001';
```

---

## 📤 MIGRACIÓN MASIVA DESDE CSV/EXCEL

### Formato del archivo CSV esperado:

```csv
placa_codigo_interno,fecha_adquisicion,costo_historico,depreciacion_historica,observaciones
AFX-001,2015-03-15,2500000.00,2500000.00,Totalmente depreciado
AFX-002,2018-06-20,5800000.00,0.00,Activo reciente
AFX-003,,0.00,0.00,Sin documentación
```

### Script Python para migración masiva:

```python
import pandas as pd
from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    # Leer CSV
    df = pd.read_csv('migracion_activos.csv')

    # Validar formato de fechas
    df['fecha_adquisicion'] = pd.to_datetime(
        df['fecha_adquisicion'],
        format='%Y-%m-%d',
        errors='coerce'
    )

    # Convertir a formato SQL
    df['fecha_adquisicion'] = df['fecha_adquisicion'].dt.strftime('%Y-%m-%d')

    # Migrar fila por fila
    for index, row in df.iterrows():
        query = text("""
            UPDATE activos
            SET
                fecha_adquisicion = :fecha,
                costo_historico = :costo,
                depreciacion_acumulada_historica = :depreciacion,
                es_activo_legacy = TRUE,
                observaciones_depreciacion = :observaciones
            WHERE placa_codigo_interno = :placa
        """)

        db.session.execute(query, {
            'fecha': row['fecha_adquisicion'] if pd.notna(row['fecha_adquisicion']) else None,
            'costo': float(row['costo_historico']),
            'depreciacion': float(row['depreciacion_historica']),
            'observaciones': row['observaciones'],
            'placa': row['placa_codigo_interno']
        })

    db.session.commit()
    print(f"✅ {len(df)} activos migrados exitosamente")
```

---

## ✅ CHECKLIST DE VALIDACIÓN

Antes de ejecutar la migración, verifica:

- [ ] Fechas en formato `YYYY-MM-DD`
- [ ] Valores monetarios con `.00` (dos decimales)
- [ ] Placas sin espacios al inicio/final
- [ ] Booleanos como `TRUE`/`FALSE` o `1`/`0`
- [ ] Números enteros sin decimales
- [ ] Observaciones con información útil
- [ ] Backup de la base de datos antes de migrar

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error: "Incorrect date value"
```
❌ CAUSA: Fecha en formato incorrecto
✅ SOLUCIÓN: Usar YYYY-MM-DD (ej: '2015-03-15')
```

### Error: "Data too long for column"
```
❌ CAUSA: Texto muy largo para observaciones
✅ SOLUCIÓN: Reducir texto o usar TEXT en lugar de VARCHAR
```

### Error: "Duplicate entry for key PRIMARY"
```
❌ CAUSA: Placa duplicada
✅ SOLUCIÓN: Verificar que placa_codigo_interno sea única
```

### Error: "Incorrect decimal value"
```
❌ CAUSA: Valor con formato incorrecto (ej: $125,000.00)
✅ SOLUCIÓN: Remover símbolos y separadores (ej: 125000.00)
```

---

## 📞 AYUDA ADICIONAL

Si tienes dudas sobre el formato de algún campo:

1. Consulta el script: `migrations/01_correccion_depreciacion_DETALLADO.sql`
2. Revisa la sección de cada columna (tiene ejemplos)
3. Usa el script de verificación: `verificar_bd.py`

**Recuerda:** Es mejor migrar datos en lotes pequeños y verificar que todo esté correcto antes de continuar.

---

**Última actualización:** 2025-11-25
**Versión:** 1.0
