# Frontend — Componentes React de JeroSmart Activos

Aquí vive el código fuente de los componentes React. Se compila con **Vite** a
un bundle que Flask sirve como archivo estático.

## Por qué existe esta carpeta

Antes, la plantilla `add_activo.html` descargaba el archivo `.jsx` en crudo, lo
transpilaba **en el navegador** con Babel Standalone y lo ejecutaba con `eval()`.
Eso tenía tres problemas:

1. **Frágil.** El preset se pedía como `presets: ['react']`, sin fijar el runtime
   de JSX. Cuando Babel cambió su valor por defecto a `automatic`, la salida pasó
   a empezar con `import ... from "react/jsx-runtime"`, y un `import` de módulo ES
   no se puede ejecutar con `eval()`. El wizard dejó de cargar **sin que nadie
   tocara el código**, porque el `<script>` pedía la última versión del CDN.
2. **Lento.** Se descargaban ~3 MB (Babel Standalone) y se transpilaban 38 kB de
   JSX en cada carga de página, antes de poder pintar nada.
3. **Dependiente de terceros.** Sin conexión a `unpkg.com`, el formulario no
   abría.

Compilado, el bundle pesa **164 kB** (52 kB con gzip), incluye React y no
depende de ningún CDN.

## Uso

Instalar dependencias (solo la primera vez):

```bash
cd frontend && npm install
```

Compilar tras modificar cualquier archivo de `src/`:

```bash
cd frontend && npm run build
```

Recompilar automáticamente al guardar, útil mientras se desarrolla:

```bash
cd frontend && npm run watch
```

## Estructura

| Ruta | Descripción |
|---|---|
| `src/wizard-activos.jsx` | Punto de entrada. Monta el wizard en `#asset-wizard-root` leyendo `data-mode` y `data-asset-json`. |
| `src/AssetWizard.jsx` | Componente del wizard de alta y edición de activos. |
| `../app/static/dist/` | Salida compilada. **Se versiona en git** para que desplegar no requiera Node. |

## Notas importantes

- **El bundle compilado se versiona.** Si editas `src/` y no ejecutas
  `npm run build`, tus cambios no llegarán a la aplicación. Acuérdate de incluir
  `app/static/dist/` en el commit.
- La plantilla referencia el bundle con el helper `static_v()` de Flask, que
  añade `?v=<fecha-de-modificación>` para invalidar la caché del navegador tras
  cada build.
- Los endpoints que consume el wizard (`/activos/api/clases`,
  `/proveedores/api/lista`, `/funcionarios/api/lista`) requieren sesión iniciada
  y responden `401` con JSON si expiró.
