/**
 * Punto de entrada del wizard de activos.
 *
 * Sustituye al esquema anterior de descargar el .jsx, transpilarlo con Babel
 * Standalone en el navegador y ejecutarlo con eval(). Aquí React, ReactDOM y
 * el componente se compilan juntos en un único bundle, por lo que la página
 * no depende de ningún CDN ni de una transpilación en tiempo de ejecución.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import AssetWizard from './AssetWizard.jsx';

const ID_CONTENEDOR = 'asset-wizard-root';

/** Muestra un aviso visible en lugar de dejar la página en blanco. */
function mostrarError(contenedor, detalle) {
  console.error('Error al inicializar el wizard de activos:', detalle);
  if (!contenedor) return;

  const pre = document.createElement('pre');
  pre.style.cssText =
    'text-align:left;background:var(--ios-bg-tertiary);border:1px solid var(--ios-separator);' +
    'border-radius:8px;padding:.75rem;font-size:.8rem;white-space:pre-wrap;overflow-x:auto;';
  pre.textContent = String(detalle);

  const caja = document.createElement('div');
  caja.className = 'ios-card';
  caja.style.cssText = 'padding:2rem;text-align:center;max-width:560px;margin:2rem auto;';
  caja.innerHTML =
    '<i class="bi bi-exclamation-triangle" style="font-size:2.5rem;color:var(--ios-orange);"></i>' +
    '<h2 style="font-size:1.2rem;font-weight:600;margin:1rem 0 .5rem;">No se pudo cargar el formulario</h2>' +
    '<p style="color:var(--ios-label-secondary);font-size:.95rem;margin-bottom:1.25rem;">' +
    'Recarga la página. Si el problema persiste, reporta este detalle al administrador:</p>';
  caja.appendChild(pre);

  contenedor.innerHTML = '';
  contenedor.appendChild(caja);
}

function montar() {
  const contenedor = document.getElementById(ID_CONTENEDOR);
  if (!contenedor) {
    console.error(`No se encontró el contenedor #${ID_CONTENEDOR}.`);
    return;
  }

  try {
    const modo = contenedor.dataset.mode || 'create';
    let datosActivo = null;

    if (modo === 'edit' && contenedor.dataset.assetJson) {
      try {
        datosActivo = JSON.parse(contenedor.dataset.assetJson);
      } catch (e) {
        // Un JSON corrupto no debe impedir abrir el formulario: se registra
        // y el wizard arranca vacío.
        console.error('Error al parsear los datos del activo:', e);
      }
    }

    createRoot(contenedor).render(
      <AssetWizard mode={modo} assetData={datosActivo} />
    );
  } catch (error) {
    mostrarError(contenedor, error && error.message ? error.message : error);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', montar);
} else {
  montar();
}
