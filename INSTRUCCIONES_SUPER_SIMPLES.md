# 🎮 INSTRUCCIONES SÚPER SIMPLES - Para Ejecutar los Scripts

## 🎯 ¿Qué vamos a hacer?

Vamos a "alimentar" la base de datos con nuevos campos para que calcule bien la depreciación de los activos viejos.

Es como cuando instalas un DLC (contenido descargable) en un videojuego - agregas nuevas funciones sin perder el progreso.

---

## 🛠️ OPCIÓN 1: Usar MySQL Workbench (MÁS FÁCIL) ⭐

### Paso 1: Abrir MySQL Workbench

1. **Busca en el menú inicio de Windows:**
   - Escribe: `MySQL Workbench`
   - Haz clic en el icono (es azul con un delfín)

2. **Si no lo tienes instalado:**
   - No hay problema, ve a la **OPCIÓN 2** más abajo

---

### Paso 2: Conectarte a tu Base de Datos

```
┌─────────────────────────────────────────┐
│     MySQL Workbench - Connections       │
├─────────────────────────────────────────┤
│                                          │
│  📦 Local instance MySQL80              │
│     (localhost:3306)                    │
│                                          │
│     [Clic aquí para conectar]  ←─────   │
│                                          │
└─────────────────────────────────────────┘
```

1. Haz clic en tu conexión (probablemente se llama "Local instance MySQL80")
2. Te pedirá tu contraseña: `JeroNimoDaviLex9824.`
3. Dale Enter

---

### Paso 3: Abrir el Script SQL

```
┌──────────────────────────────────────────────┐
│  File   Edit   View   Query               │
├──────────────────────────────────────────────┤
│                                              │
│  File → Open SQL Script...                  │
│         └─ [Clic aquí]  ←─────────          │
│                                              │
└──────────────────────────────────────────────┘
```

1. En el menú de arriba, haz clic en **File**
2. Luego en **Open SQL Script...** (Abrir Script SQL)
3. Se abre una ventana de archivos

---

### Paso 4: Buscar el Archivo

```
📁 Esta PC
  └─ 💾 Disco Local (C:)
      └─ 👤 Users
          └─ 👤 david
              └─ 📁 JEROSMART ACTIVOS
                  └─ 📁 migrations
                      └─ 📄 01_correccion_depreciacion_DETALLADO.sql  ← ESTE
```

1. Navega hasta: `C:\Users\david\JEROSMART ACTIVOS\migrations`
2. Selecciona el archivo: `01_correccion_depreciacion_DETALLADO.sql`
3. Haz clic en **Abrir**

---

### Paso 5: Ejecutar el Script

```
┌──────────────────────────────────────────────────────┐
│  [⚡ Ejecutar] [▶️ Ejecutar Todo]  [💾 Guardar]      │  ← Esta es la barra de herramientas
├──────────────────────────────────────────────────────┤
│                                                      │
│  -- ========================================         │
│  -- MIGRACIÓN: Corrección del sistema de            │
│  -- depreciación para activos legacy                │
│  -- ========================================         │
│                                                      │
│  (El código SQL aparece aquí)                       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

1. **Busca el icono del RAYO ⚡** en la barra de herramientas (arriba)
2. **Haz clic en el rayo** (o presiona Ctrl+Shift+Enter)
3. **Espera** - verás mensajes apareciendo abajo

---

### Paso 6: Verificar que Funcionó

```
┌──────────────────────────────────────────────┐
│  Output                                      │
├──────────────────────────────────────────────┤
│  ✅ Agregando columna: fecha_adquisicion... │
│  ✅ Agregando columna: costo_historico...   │
│  ✅ Marcados 6629 activos como legacy       │
│  ✅ Vista creada exitosamente               │
│                                              │
│  🎉 MIGRACIÓN FINALIZADA CORRECTAMENTE      │
└──────────────────────────────────────────────┘
```

**Si ves mensajes con ✅ (checks verdes):** ¡TODO BIEN! Ya terminaste.

**Si ves mensajes con ❌ (X rojas):** Copia el mensaje de error y me lo pasas.

---

## 🖥️ OPCIÓN 2: Usar la Línea de Comandos (Si no tienes Workbench)

### Paso 1: Abrir PowerShell

1. Presiona la **tecla Windows** (⊞ Win)
2. Escribe: `PowerShell`
3. Haz clic derecho en **Windows PowerShell**
4. Selecciona: **Ejecutar como administrador**

---

### Paso 2: Ir a la Carpeta del Proyecto

Copia y pega este comando exactamente como está:

```powershell
cd "C:\Users\david\JEROSMART ACTIVOS"
```

Presiona **Enter**

---

### Paso 3: Ejecutar el Script de MySQL

Copia y pega este comando:

```powershell
mysql -u root -p jerosmart_activos < migrations\01_correccion_depreciacion_DETALLADO.sql
```

Presiona **Enter**

**Te pedirá la contraseña:**
```
Enter password:
```

Escribe: `JeroNimoDaviLex9824.`
Presiona **Enter**

**NOTA:** La contraseña NO se ve mientras escribes (es normal)

---

### Paso 4: Verificar que Funcionó

**Si todo está bien, verás:**
```
paso
-------
Agregando columna: fecha_adquisicion...
Agregando columna: costo_historico...
...
✅ Marcados 6629 activos como legacy
🎉 MIGRACIÓN FINALIZADA CORRECTAMENTE
```

**Si hay error:**
Cópiame todo lo que salga en rojo y te ayudo.

---

## 🆘 ¿Qué Pasa Si Sale Algo Mal?

### Error 1: "mysql: command not found"

**Significa:** MySQL no está en el PATH (Windows no sabe dónde está mysql.exe)

**Solución Fácil:**
1. Busca donde está instalado MySQL (usualmente: `C:\Program Files\MySQL\MySQL Server 8.0\bin`)
2. Usa la ruta completa:

```powershell
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p jerosmart_activos < migrations\01_correccion_depreciacion_DETALLADO.sql
```

---

### Error 2: "Access denied for user 'root'"

**Significa:** La contraseña está mal

**Solución:**
- Verifica que la contraseña sea: `JeroNimoDaviLex9824.` (con el punto al final)
- O me dices cuál es tu contraseña real de MySQL

---

### Error 3: "Unknown database 'jerosmart_activos'"

**Significa:** La base de datos no existe con ese nombre

**Solución:**
1. Averigua el nombre real de tu base de datos
2. Dime cuál es y te corrijo el comando

---

## ✅ CHECKLIST VISUAL

Marca con una ✅ cuando completes cada paso:

- [ ] **Paso 1:** Abrir MySQL Workbench o PowerShell
- [ ] **Paso 2:** Conectarte a la base de datos
- [ ] **Paso 3:** Abrir/Ejecutar el script `01_correccion_depreciacion_DETALLADO.sql`
- [ ] **Paso 4:** Ver mensaje de éxito (✅)
- [ ] **Paso 5:** Hacer lo mismo con `02_sistema_ingreso_rapido_legacy.sql`

---

## 📸 ¿Cómo Sé Que Funcionó?

### Prueba 1: Verificar Columnas Nuevas

Abre MySQL Workbench y ejecuta esto:

```sql
SHOW COLUMNS FROM activos;
```

**Deberías ver estas columnas nuevas:**
- ✅ fecha_adquisicion
- ✅ fecha_alta_sistema
- ✅ costo_historico
- ✅ depreciacion_acumulada_historica
- ✅ es_activo_legacy

---

### Prueba 2: Ver Activos con Nueva Info

```sql
SELECT
    placa_codigo_interno,
    nombre_activo,
    fecha_adquisicion,
    costo_historico,
    es_activo_legacy
FROM activos
LIMIT 10;
```

**Deberías ver:**
- Las fechas en formato `2024-11-20`
- Los costos en formato `125000000.00`
- `es_activo_legacy` = 1 (TRUE) para todos

---

### Prueba 3: Ver la Vista Nueva

```sql
SELECT * FROM vista_activos_valoracion LIMIT 5;
```

**Deberías ver:**
- Una tabla con muchas columnas
- Cálculos de depreciación correctos

---

## 🎮 ANALOGÍA GAMER

Esto es como cuando actualizas un videojuego:

1. **Script SQL** = Archivo de actualización (.patch)
2. **MySQL Workbench** = Steam/Epic Games Launcher
3. **Ejecutar script** = Presionar "Instalar actualización"
4. **Base de datos** = Tu juego guardado

El script **NO BORRA NADA**, solo **AGREGA** nuevas funciones.

---

## 🆘 SI NADA FUNCIONA

**Contáctame y envíame:**

1. Una captura de pantalla del error
2. El texto completo del error (copiado)
3. Tu versión de MySQL (ejecuta: `mysql --version`)

**O podemos hacer una videollamada y lo hacemos juntos en 10 minutos.**

---

## 🎯 ¿CUÁNDO HACER CADA SCRIPT?

| Script | ¿Cuándo? | ¿Qué hace? |
|--------|----------|------------|
| `agregar_columna_updated_by.py` | **AHORA** | Corrige el error de eliminar activos |
| `01_correccion_depreciacion_DETALLADO.sql` | **HOY** | Agrega campos para depreciación correcta |
| `02_sistema_ingreso_rapido_legacy.sql` | **MAÑANA** | Crea sistema para activos "fantasma" |

---

## 🎓 RECUERDA

- 📝 **Haz backup ANTES** (mejor prevenir)
- 🐢 **Ve despacio** (no hay prisa)
- ❓ **Pregunta si algo no entiendes**
- 🎯 **Un paso a la vez**

---

**¿Listo para empezar? Comienza por la OPCIÓN 1 (MySQL Workbench) o la OPCIÓN 2 (PowerShell).**

**¿Tienes dudas? Pregúntame y te explico mejor.** 😊
