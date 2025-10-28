// /static/js/firmas.js
// Maneja el wizard de firmas: dibujo (mouse/touch), guardado, re-firmar y progreso

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const dataEl = document.getElementById('signature-data');
    if (!dataEl) return;

    const rolesRequeridos = JSON.parse(dataEl.dataset.roles || '[]');
    const firmasGuardadas = JSON.parse(dataEl.dataset.firmas || '{}');
    const postUrl = dataEl.dataset.postUrl;              // p.ej. /movimiento/123/firmar
    const deleteBase = dataEl.dataset.deleteBase;        // p.ej. /movimiento/123/firmar
    const totalSteps = parseInt(dataEl.dataset.totalSteps || rolesRequeridos.length, 10);

    let currentStep = 0;

    const prevBtn = document.getElementById('wizard-prev-btn');
    const nextBtn = document.getElementById('wizard-next-btn');

    function qsAll(sel){return Array.from(document.querySelectorAll(sel));}
    function paneByIndex(idx){return document.querySelector(`.wizard-pane[data-pane-id="${idx}"]`);}

    function showStep(stepIndex) {
      currentStep = stepIndex;

      // panes
      qsAll('.wizard-pane').forEach(p => p.classList.remove('active'));
      const activePane = paneByIndex(stepIndex);
      if (activePane) activePane.classList.add('active');

      // Si es un paso de firma, montar contenido (pad o imagen)
      if (stepIndex < totalSteps) {
        const rol = rolesRequeridos[stepIndex];
        const contentContainer = document.getElementById(`content-${rol}`);
        if (contentContainer && contentContainer.innerHTML.trim() === '') {
          initializeStepContent(rol);
        }
        // Redimensionar canvas tras volver visible el pane
        if (contentContainer && typeof contentContainer.resizeCanvas === 'function') {
          requestAnimationFrame(() => contentContainer.resizeCanvas());
        }
      }

      // barra de progreso
      const stepsEls = qsAll('.wizard-progress-bar .step');
      stepsEls.forEach((stepEl, i) => {
        stepEl.classList.remove('active', 'completed');
        const icon = stepEl.querySelector('.icon');
        if (i < stepIndex) {
          stepEl.classList.add('completed');
          if (icon) icon.innerHTML = '<i class="bi bi-check"></i>';
        } else if (i === stepIndex) {
          stepEl.classList.add('active');
          if (icon && i < totalSteps) icon.innerHTML = '<i class="bi bi-pencil"></i>';
        } else {
          if (icon && i < totalSteps) icon.innerHTML = '<i class="bi bi-pencil"></i>';
        }
      });

      prevBtn.disabled = stepIndex === 0;
      nextBtn.style.display = stepIndex >= totalSteps ? 'none' : 'inline-flex';
    }

    function initializeStepContent(rol) {
      if (firmasGuardadas && firmasGuardadas[rol]) {
        renderSignedView(rol, firmasGuardadas[rol]);
      } else {
        renderSignaturePad(rol);
      }
    }

    function renderSignaturePad(rol) {
      const content = document.getElementById(`content-${rol}`);
      if (!content) return;

      content.innerHTML = `
        <div class="signature-pad-container mb-2"><canvas></canvas></div>
        <div class="text-end">
          <button type="button" class="btn btn-sm btn-link text-muted clear-signature">Limpiar</button>
        </div>
      `;

      const canvas = content.querySelector('canvas');
      const pad = new SignaturePad(canvas, { backgroundColor: 'rgb(248, 249, 250)' });

      // Fix de DPI y tamaño real del contenedor
      function resizeCanvas() {
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        const container = canvas.parentElement;
        const w = container.offsetWidth;
        const h = container.offsetHeight;
        if (w > 0 && h > 0) {
          canvas.width = w * ratio;
          canvas.height = h * ratio;
          const ctx = canvas.getContext('2d');
          ctx.scale(ratio, ratio);
          // al redimensionar, limpiamos para evitar distorsiones
          pad.clear();
        }
      }

      // Ajustes de interacción en móviles (evitar scroll mientras se firma)
      const container = content.querySelector('.signature-pad-container');
      container.addEventListener('touchstart', (e) => { e.preventDefault(); }, { passive: false });
      container.addEventListener('touchmove',  (e) => { e.preventDefault(); }, { passive: false });

      window.addEventListener('resize', resizeCanvas);
      // primera preparación; usar rAF para garantizar layout listo
      requestAnimationFrame(resizeCanvas);

      const clearBtn = content.querySelector('.clear-signature');
      if (clearBtn) clearBtn.addEventListener('click', () => pad.clear());

      // guardar referencias para el step
      content.signaturePadInstance = pad;
      content.resizeCanvas = resizeCanvas;
    }

    function renderSignedView(rol, imageUrl) {
      const content = document.getElementById(`content-${rol}`);
      if (!content) return;

      content.innerHTML = `
        <div class="signature-image-container">
          <img src="${imageUrl}" alt="Firma de ${rol}" class="signature-image">
          <button class="btn btn-sm btn-outline-danger mt-2 resign-btn" data-rol="${rol}">
            <i class="bi bi-trash3 me-1"></i>Re-firmar
          </button>
        </div>
      `;

      const btn = content.querySelector('.resign-btn');
      if (btn) btn.addEventListener('click', handleResign);
    }

    function handleNext() {
      if (currentStep >= totalSteps) return;

      const rol = rolesRequeridos[currentStep];
      const content = document.getElementById(`content-${rol}`);
      if (!content) return;

      // ya firmada: pasar
      if (firmasGuardadas && firmasGuardadas[rol]) {
        showStep(currentStep + 1);
        return;
      }

      const pad = content.signaturePadInstance;
      if (!pad || pad.isEmpty()) {
        const box = content.querySelector('.signature-pad-container');
        if (box) box.classList.add('is-invalid');
        return;
      }

      nextBtn.disabled = true;
      nextBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

      const dataURL = pad.toDataURL('image/png');
      fetch(postUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ rol_firma: rol, signature: dataURL })
      })
      .then(r => r.json())
      .then(data => {
        if (data && data.success) {
          // backend retorna image_url (servida por /uploads/…)
          firmasGuardadas[rol] = data.image_url;
          showStep(currentStep + 1);
        } else {
          console.error('Error al guardar firma:', data && data.message);
          alert('Hubo un error al guardar la firma. Inténtalo de nuevo.');
        }
      })
      .catch(err => {
        console.error('Error fetch firma:', err);
        alert('No se pudo contactar el servidor.');
      })
      .finally(() => {
        nextBtn.disabled = false;
        nextBtn.innerHTML = 'Siguiente<i class="bi bi-arrow-right ms-1"></i>';
      });
    }

    function handleResign(e) {
      const btn = e.currentTarget;
      const rol = btn.dataset.rol;
      if (!rol) return;

      if (!confirm(`¿Borrar la firma de '${rol.replaceAll('_',' ')}' y re-firmar?`)) return;

      fetch(`${deleteBase}/${encodeURIComponent(rol)}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
          if (data && data.success) {
            delete firmasGuardadas[rol];
            const content = document.getElementById(`content-${rol}`);
            if (content) content.innerHTML = ''; // forzar re-render
            showStep(currentStep);               // re-inicializa step actual
          } else {
            alert('No se pudo borrar la firma.');
          }
        })
        .catch(() => alert('No se pudo contactar el servidor.'));
    }

    // wiring
    showStep(0);
    if (nextBtn) nextBtn.addEventListener('click', handleNext);
    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentStep > 0) showStep(currentStep - 1); });
  });
})();
