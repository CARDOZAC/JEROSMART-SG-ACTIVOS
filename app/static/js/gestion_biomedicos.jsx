// =====================================================================
// MÓDULO DE GESTIÓN DE ACTIVOS BIOMÉDICOS - VERSIÓN COMPLETA Y OPTIMIZADA
// =====================================================================

// Se asume que React y ReactDOM están disponibles globalmente.
const { useState, useEffect, useCallback, useMemo } = React;

// =====================================================================
// COMPONENTES REUTILIZABLES
// =====================================================================

/**
 * Muestra un modal de confirmación, reemplazando a `window.confirm`.
 */
const ConfirmationModal = React.memo(({ title, message, onConfirm, onCancel }) => (
    <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
        <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
                <div className="modal-header">
                    <h5 className="modal-title">{title || 'Confirmación Requerida'}</h5>
                    <button type="button" className="btn-close" onClick={onCancel}></button>
                </div>
                <div className="modal-body"><p>{message}</p></div>
                <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancelar</button>
                    <button type="button" className="btn btn-danger" onClick={onConfirm}>Confirmar</button>
                </div>
            </div>
        </div>
    </div>
));

/**
 * Componente principal para el asistente de creación/edición de mantenimientos.
 * Este es el "wizard" dinámico que solicitaste.
 */
const MaintenanceWizard = ({ onBack, editingRecord, allAssets, allReportTypes, allReportDetails }) => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState(editingRecord || {
        activo_id: '',
        tipo_id: '',
        fecha_mantenimiento: new Date().toISOString().slice(0, 10),
        duracion_minutos: '',
        observaciones: '',
        estado: 'Pendiente',
        atributos_reporte_json: {},
        fotos_evidencia: [] // Para las subidas de archivos
    });
    const [dynamicFields, setDynamicFields] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);

    // Actualiza los campos dinámicos cuando cambia el tipo de reporte
    useEffect(() => {
        if (formData.tipo_id) {
            const selectedReportTypeName = allReportTypes.find(t => t.id == formData.tipo_id)?.nombre;
            if (selectedReportTypeName && allReportDetails[selectedReportTypeName]) {
                setDynamicFields(allReportDetails[selectedReportTypeName]);
            } else {
                setDynamicFields([]);
            }
        }
    }, [formData.tipo_id, allReportDetails, allReportTypes]);

    // Lógica para buscar activos por placa o nombre
    const handleAssetSearch = useCallback(async (query) => {
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }
        const res = await fetch(`/api/buscar_activos?term=${encodeURIComponent(query)}`);
        const data = await res.json(); // La API ahora es /api/activos-biomedicos
        setSearchResults(data);
    }, []);

    // Maneja los cambios en los campos del formulario
    const handleChange = (e) => {
        const { name, value, type, files } = e.target;
        if (type === 'file') {
            setFormData(prev => ({
                ...prev,
                fotos_evidencia: [...prev.fotos_evidencia, ...Array.from(files)]
            }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    // Maneja los cambios en los campos dinámicos
    const handleDynamicChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            atributos_reporte_json: {
                ...prev.atributos_reporte_json,
                [name]: value
            }
        }));
    };

    const handleSave = async (e) => {
        e.preventDefault();
        const url = editingRecord ? `/api/mantenimientos/${editingRecord.id}` : '/api/mantenimientos';
        const method = editingRecord ? 'PUT' : 'POST';

        try {
            // Se usa FormData para enviar archivos y JSON
            const formPayload = new FormData();
            formPayload.append('activo_id', formData.activo_id);
            formPayload.append('tipo_id', formData.tipo_id);
            formPayload.append('fecha_mantenimiento', formData.fecha_mantenimiento);
            formPayload.append('duracion_minutos', formData.duracion_minutos);
            formPayload.append('observaciones', formData.observaciones);
            formPayload.append('estado', formData.estado);
            formPayload.append('atributos_reporte_json', JSON.stringify(formData.atributos_reporte_json));
            formData.fotos_evidencia.forEach(file => {
                formPayload.append('fotos_evidencia', file);
            });
            
            const response = await fetch(url, { method, body: formPayload });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || 'Error al guardar el registro.');
            }
            onBack();
        } catch (err) {
            alert(err.message);
        }
    };

    return (
        <div className="card p-4">
            <button className="btn btn-outline-secondary btn-sm mb-3" onClick={onBack}><i className="bi bi-arrow-left me-1"></i> Volver</button>
            <h4 className="fw-bold">{editingRecord ? 'Editar Mantenimiento' : 'Nuevo Mantenimiento'}</h4>
            <div className="progress wizard-progress-bar" style={{height: '8px'}}><div className="progress-bar" style={{width: `${(step/4)*100}%`}}></div></div>
            <form onSubmit={handleSave}>
                {/* Paso 1: Selección de Activo */}
                <div className={`form-step ${step === 1 ? 'active' : ''}`}>
                    <h5 className="step-header">Paso 1: Seleccionar Activo</h5>
                    <div className="mb-3">
                        <label className="form-label">Activo Biomédico</label>
                        <input
                            type="text"
                            className="form-control"
                            placeholder="Buscar por placa o nombre..."
                            value={searchQuery}
                            onChange={(e) => {
                                setSearchQuery(e.target.value); // El debounce se aplica en el efecto
                                handleAssetSearch(e.target.value);
                            }}
                        />
                        <ul className="list-group mt-2">
                            {searchResults.map(asset => (
                                <li key={asset.id} className="list-group-item list-group-item-action" onClick={() => {
                                    setFormData(prev => ({ ...prev, activo_id: asset.id }));
                                    setSearchQuery(`${asset.nombre_activo} (${asset.placa_codigo_interno})`);
                                    setSearchResults([]);
                                }}>
                                    {asset.nombre_activo} ({asset.placa_codigo_interno})
                                </li>
                            ))}
                        </ul>
                    </div>
                    {formData.activo_id && <div className="alert alert-success">Activo seleccionado: {allAssets.find(a => a.id == formData.activo_id)?.nombre_activo}</div>}
                    <button type="button" className="btn btn-primary" onClick={() => setStep(2)} disabled={!formData.activo_id}>Siguiente</button>
                </div>

                {/* Paso 2: Tipo de Reporte */}
                <div className={`form-step ${step === 2 ? 'active' : ''}`}>
                    <h5 className="step-header">Paso 2: Tipo de Reporte</h5>
                    <div className="mb-3">
                        <label className="form-label">Seleccione el tipo de reporte</label>
                        <select name="tipo_id" value={formData.tipo_id} onChange={handleChange} className="form-select">
                            <option value="">Seleccione...</option>
                            {allReportTypes.map(type => ( // allReportTypes viene de la API /api/mantenimiento-tipos
                                <option key={type.id} value={type.id}>{type.nombre}</option>
                            ))}
                        </select>
                    </div>
                    <div className="d-flex justify-content-between">
                        <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>Anterior</button>
                        <button type="button" className="btn btn-primary" onClick={() => setStep(3)} disabled={!formData.tipo_id}>Siguiente</button>
                    </div>
                </div>

                {/* Paso 3: Campos dinámicos y generales */}
                <div className={`form-step ${step === 3 ? 'active' : ''}`}>
                    <h5 className="step-header">Paso 3: Detalles del Mantenimiento</h5>
                    <div className="row g-3">
                        {dynamicFields.map(field => (
                            <div key={field.name} className="col-md-6">
                                <label className="form-label">{field.label}</label>
                                {field.type === 'select' ? (
                                    <select name={field.name} value={formData.atributos_reporte_json[field.name] || ''} onChange={handleDynamicChange} className="form-select">
                                        <option value="">Seleccione...</option>
                                        {field.options.map(option => <option key={option} value={option}>{option}</option>)}
                                    </select>
                                ) : field.type === 'textarea' ? (
                                    <textarea name={field.name} value={formData.atributos_reporte_json[field.name] || ''} onChange={handleDynamicChange} className="form-control" rows="3"></textarea>
                                ) : (
                                    <input type={field.type} name={field.name} value={formData.atributos_reporte_json[field.name] || ''} onChange={handleDynamicChange} className="form-control" />
                                )}
                            </div>
                        ))}
                        <div className="col-md-6">
                            <label className="form-label">Duración (minutos)</label>
                            <input type="number" name="duracion_minutos" value={formData.duracion_minutos} onChange={handleChange} className="form-control" />
                        </div>
                        <div className="col-md-6">
                            <label className="form-label">Estado del Mantenimiento</label>
                            <select name="estado" value={formData.estado} onChange={handleChange} className="form-select">
                                <option value="Pendiente">Pendiente</option>
                                <option value="Incompleto">Incompleto</option>
                                <option value="Completo">Completo</option>
                            </select>
                        </div>
                        <div className="col-12">
                            <label className="form-label">Observaciones</label>
                            <textarea name="observaciones" value={formData.observaciones} onChange={handleChange} className="form-control" rows="4"></textarea>
                        </div>
                    </div>
                    <div className="d-flex justify-content-between mt-3">
                        <button type="button" className="btn btn-secondary" onClick={() => setStep(2)}>Anterior</button>
                        <button type="button" className="btn btn-primary" onClick={() => setStep(4)}>Siguiente</button>
                    </div>
                </div>

                {/* Paso 4: Subir fotos y guardar */}
                <div className={`form-step ${step === 4 ? 'active' : ''}`}>
                    <h5 className="step-header">Paso 4: Evidencia y Guardar</h5>
                    <div className="mb-3">
                        <label className="form-label">Subir fotos de evidencia</label>
                        <input type="file" name="fotos_evidencia" multiple className="form-control" onChange={handleChange} />
                    </div>
                    <div className="d-flex justify-content-between">
                        <button type="button" className="btn btn-secondary" onClick={() => setStep(3)}>Anterior</button>
                        <button type="submit" className="btn btn-success">Guardar Mantenimiento</button>
                    </div>
                </div>
            </form>
        </div>
    );
};

const MaintenanceListView = ({ onBack, allAssets, allReportTypes }) => {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showConfirm, setShowConfirm] = useState(false);
    const [recordToDelete, setRecordToDelete] = useState(null);
    const [editingRecord, setEditingRecord] = useState(null);
    const [showWizard, setShowWizard] = useState(false);

    const fetchRecords = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/biomedicos/api/mantenimientos');
            if (!response.ok) throw new Error('Error al cargar los registros.');
            const data = await response.json();
            setRecords(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchRecords(); }, [fetchRecords]);

    const handleDelete = async () => {
        if (!recordToDelete) return;
        try {
            const response = await fetch(`/biomedicos/api/mantenimientos/${recordToDelete.id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Error al eliminar el registro.');
            setShowConfirm(false);
            setRecordToDelete(null);
            fetchRecords();
        } catch (err) {
            alert(err.message);
        }
    };

    if (showWizard) {
        return <MaintenanceWizard onBack={() => setShowWizard(false)} editingRecord={editingRecord} allAssets={allAssets} allReportTypes={allReportTypes} />;
    }

    if (loading) return <div className="text-center p-5"><div className="spinner-border text-primary" role="status"></div></div>;
    if (error) return <div className="alert alert-danger">{error}</div>;

    return (
        <div className="card p-4">
            <div className="card-header bg-white d-flex justify-content-between align-items-center mb-3">
                <button className="btn btn-outline-secondary btn-sm me-3" onClick={onBack}><i className="bi bi-arrow-left me-1"></i>Volver</button>
                <h3 className="d-inline-block mb-0">Historial de Mantenimientos</h3>
                <button className="btn btn-primary" onClick={() => { setEditingRecord(null); setShowWizard(true); }}>
                    <i className="bi bi-plus-lg me-1"></i> Añadir Mantenimiento
                </button>
            </div>
            <div className="table-responsive">
                <table className="table table-hover align-middle">
                    <thead className="table-light">
                        <tr><th>Activo</th><th>Placa</th><th>Fecha</th><th>Tipo</th><th>Estado</th><th className="text-center">Acciones</th></tr>
                    </thead>
                    <tbody>
                        {records.length === 0 ? (
                            <tr><td colSpan="6" className="text-center text-muted p-4">No hay registros de mantenimiento.</td></tr>
                        ) : (
                            records.map(rec => (
                                <tr key={rec.id}>
                                    <td><strong>{rec.nombre_activo}</strong></td>
                                    <td><span className="badge bg-secondary">{rec.placa_codigo_interno}</span></td>
                                    <td>{rec.fecha_mantenimiento}</td>
                                    <td>{rec.tipo_reporte}</td>
                                    <td>{rec.estado}</td>
                                    <td className="text-center">
                                        <button className="btn btn-sm btn-outline-secondary me-1" title="Editar" onClick={() => { setEditingRecord(rec); setShowWizard(true); }}><i className="bi bi-pencil-fill"></i></button>
                                        <button className="btn btn-sm btn-outline-danger" title="Eliminar" onClick={() => { setRecordToDelete(rec); setShowConfirm(true); }}><i className="bi bi-trash-fill"></i></button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
            {showConfirm && <ConfirmationModal title="Confirmar Eliminación" message={`¿Estás seguro de que quieres eliminar el registro de mantenimiento para "${recordToDelete?.nombre_activo}"?`} onConfirm={handleDelete} onCancel={() => setShowConfirm(false)} />}
        </div>
    );
};

const HojaVidaWizard = ({ onBack, onSave, editingRecord, allAssets }) => {
    const [formData, setFormData] = useState(editingRecord || {
        activo_id: '',
        normativa_aplicable: '',
        hoja_vida_pdf: null,
        foto_activo: null,
    });
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);

    const handleAssetSearch = useCallback(async (query) => {
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }
        const res = await fetch(`/biomedicos/api/activos-biomedicos?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setSearchResults(data.filter(asset => !asset.tiene_hoja_vida)); // Solo mostrar activos sin hoja de vida
    }, []);

    const handleChange = (e) => {
        const { name, value, type, files } = e.target;
        if (type === 'file') {
            setFormData(prev => ({ ...prev, [name]: files[0] }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const url = editingRecord ? `/biomedicos/api/hojas-vida/${editingRecord.id}` : '/biomedicos/api/hojas-vida';
        const method = editingRecord ? 'PUT' : 'POST';

        const formPayload = new FormData();
        formPayload.append('activo_id', formData.activo_id);
        formPayload.append('normativa_aplicable', formData.normativa_aplicable);
        if (formData.hoja_vida_pdf) {
            formPayload.append('hoja_vida_pdf', formData.hoja_vida_pdf);
        }
        if (formData.foto_activo) {
            formPayload.append('foto_activo', formData.foto_activo);
        }

        try {
            const response = await fetch(url, { method, body: formPayload });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || 'Error al guardar la Hoja de Vida.');
            }
            onSave(); // Llama a la función para recargar y volver
        } catch (err) {
            alert(err.message);
        }
    };

    const selectedAsset = useMemo(() => allAssets.find(a => a.id == formData.activo_id), [formData.activo_id, allAssets]);

    return (
        <div className="card p-4">
            <button className="btn btn-outline-secondary btn-sm mb-3" onClick={onBack}><i className="bi bi-arrow-left me-1"></i> Volver</button>
            <h4 className="fw-bold">{editingRecord ? 'Editar Hoja de Vida' : 'Nueva Hoja de Vida'}</h4>
            <form onSubmit={handleSubmit}>
                {!editingRecord && (
                    <div className="mb-3">
                        <label className="form-label">Buscar Activo Biomédico (sin Hoja de Vida)</label>
                        <input
                            type="text"
                            className="form-control"
                            placeholder="Buscar por placa o nombre..."
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); handleAssetSearch(e.target.value); }}
                        />
                        <ul className="list-group mt-2">
                            {searchResults.map(asset => (
                                <li key={asset.id} className="list-group-item list-group-item-action" onClick={() => {
                                    setFormData(prev => ({ ...prev, activo_id: asset.id }));
                                    setSearchQuery(`${asset.nombre_activo} (${asset.placa_codigo_interno})`);
                                    setSearchResults([]);
                                }}>
                                    {asset.nombre_activo} ({asset.placa_codigo_interno})
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                {selectedAsset && <div className="alert alert-success">Activo seleccionado: <strong>{selectedAsset.nombre_activo}</strong></div>}

                <div className="mb-3">
                    <label htmlFor="normativa_aplicable" className="form-label">Normativa Aplicable</label>
                    <input type="text" id="normativa_aplicable" name="normativa_aplicable" value={formData.normativa_aplicable} onChange={handleChange} className="form-control" />
                </div>
                <div className="row">
                    <div className="col-md-6 mb-3">
                        <label htmlFor="hoja_vida_pdf" className="form-label">Subir Hoja de Vida Física (PDF)</label>
                        <input type="file" id="hoja_vida_pdf" name="hoja_vida_pdf" accept=".pdf" onChange={handleChange} className="form-control" />
                    </div>
                    <div className="col-md-6 mb-3">
                        <label htmlFor="foto_activo" className="form-label">Subir Foto del Activo</label>
                        <input type="file" id="foto_activo" name="foto_activo" accept="image/*" onChange={handleChange} className="form-control" />
                    </div>
                </div>
                <div className="text-end">
                    <button type="submit" className="btn btn-success" disabled={!formData.activo_id}>
                        <i className="bi bi-check-circle-fill me-1"></i> Guardar Hoja de Vida
                    </button>
                </div>
            </form>
        </div>
    );
};

const HojaVidaView = ({ onBack, allAssets }) => {
    const [hojasVida, setHojasVida] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showConfirm, setShowConfirm] = useState(false);
    const [recordToDelete, setRecordToDelete] = useState(null);
    const [editingRecord, setEditingRecord] = useState(null);
    const [showWizard, setShowWizard] = useState(false);

    const fetchHojasVida = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch('/biomedicos/api/hojas-vida');
            if (!response.ok) throw new Error('Error al cargar las Hojas de Vida.');
            const data = await response.json();
            setHojasVida(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchHojasVida(); }, [fetchHojasVida]);

    const handleDelete = async () => {
        if (!recordToDelete) return;
        try {
            const response = await fetch(`/biomedicos/api/hojas-vida/${recordToDelete.id}`, { method: 'DELETE' });
            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || 'Error al eliminar la Hoja de Vida.');
            }
            setShowConfirm(false);
            setRecordToDelete(null);
            // Optimistic UI update
            setHojasVida(prev => prev.filter(hv => hv.id !== recordToDelete.id));
        } catch (err) {
            alert(err.message);
        }
    };

    const handleGeneratePdf = (hdvId) => {
        // Abrir el PDF en una nueva pestaña
        window.open(`/biomedicos/api/hojas-vida/${hdvId}/pdf`, '_blank');
    };

    if (showWizard) {
        return <HojaVidaWizard onBack={() => setShowWizard(false)} editingRecord={editingRecord} allAssets={allAssets}
            onSave={() => { setShowWizard(false); fetchHojasVida(); }} />;
    }

    if (loading) return <div className="text-center p-5"><div className="spinner-border text-primary" role="status"></div></div>;
    if (error) return <div className="alert alert-danger">{error}</div>;

    return (
        <div className="card p-4">
            <div className="card-header bg-white d-flex justify-content-between align-items-center mb-3">
                <button className="btn btn-outline-secondary btn-sm me-3" onClick={onBack}><i className="bi bi-arrow-left me-1"></i>Volver</button>
                <h3 className="d-inline-block mb-0">Hojas de Vida de Equipos</h3>
                <button className="btn btn-primary" onClick={() => { setEditingRecord(null); setShowWizard(true); }}>
                    <i className="bi bi-plus-lg me-1"></i> Añadir Hoja de Vida
                </button>
            </div>
            <p className="text-muted">
                Esta tabla muestra todos los equipos biomédicos. Aquellos que ya tienen una Hoja de Vida registrada ofrecen la opción de generar el PDF consolidado.
            </p>
            <div className="table-responsive">
                <table className="table table-hover align-middle">
                    <thead className="table-light">
                        <tr>
                            <th>Equipo Biomédico</th>
                            <th>Placa</th>
                            <th>Estado</th>
                            <th className="text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {hojasVida.map(hv => (
                            <tr key={hv.activo_id}>
                                <td><strong>{hv.nombre_activo}</strong></td>
                                <td><span className="badge bg-secondary">{hv.placa_codigo_interno}</span></td>
                                <td>
                                    {hv.tiene_hoja_vida ? 
                                        <span className="badge bg-success">Registrada</span> : 
                                        <span className="badge bg-warning text-dark">Pendiente</span>
                                    }
                                </td>
                                <td className="text-center">
                                    {hv.tiene_hoja_vida ? (
                                        <>
                                            <button className="btn btn-sm btn-info me-1" title="Generar PDF Consolidado" onClick={() => handleGeneratePdf(hv.id)}><i className="bi bi-file-earmark-pdf-fill"></i></button>
                                            <button className="btn btn-sm btn-outline-secondary me-1" title="Editar" onClick={() => { setEditingRecord(hv); setShowWizard(true); }}><i className="bi bi-pencil-fill"></i></button>
                                            <button className="btn btn-sm btn-outline-danger" title="Eliminar Hoja de Vida" onClick={() => { setRecordToDelete(hv); setShowConfirm(true); }}><i className="bi bi-trash-fill"></i></button>
                                        </>
                                    ) : (
                                        <button className="btn btn-sm btn-outline-primary" onClick={() => { setEditingRecord({ activo_id: hv.activo_id }); setShowWizard(true); }}>Crear Hoja de Vida</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {showConfirm && <ConfirmationModal title="Confirmar Eliminación" message={`¿Estás seguro de que quieres eliminar la Hoja de Vida para "${recordToDelete?.nombre_activo}"? Esta acción no se puede deshacer.`} onConfirm={handleDelete} onCancel={() => setShowConfirm(false)} />}
        </div>
    );
};

const DashboardView = React.memo(({ onSelectView, stats }) => (
    <>
        <div className="hero-section">
            <h1 className="display-5 fw-bold text-primary">Módulo Biomédico</h1>
            <p className="fs-4">Gestión centralizada de equipos, mantenimientos y hojas de vida.</p>
        </div>
        <div className="row g-4 mb-5">
            <div className="col-md-6">
                <div className="stat-card">
                    <div className="stat-icon"><i className="bi bi-tools"></i></div>
                    <div className="stat-info">
                        <div className="stat-number">{stats.totalAssets}</div>
                        <div className="stat-label">Equipos Registrados</div>
                    </div>
                </div>
            </div>
            <div className="col-md-6">
                <div className="stat-card">
                    <div className="stat-icon"><i className="bi bi-exclamation-circle"></i></div>
                    <div className="stat-info">
                        <div className="stat-number text-danger">{stats.assetsInMaintenance}</div>
                        <div className="stat-label">Equipos en Mantenimiento</div>
                    </div>
                </div>
            </div>
        </div>
        <h2 className="mb-4">Menú de Opciones</h2>
        <div className="row row-cols-1 row-cols-md-2 g-4">
            <MenuCard icon="bi-tools" title="Ver Mantenimientos" description="Revisa y gestiona el historial de mantenimientos." onClick={() => onSelectView('mantenimientos')} />
            <MenuCard icon="bi-journal-text" title="Ver Hojas de Vida" description="Consulta y descarga el historial de cada equipo." onClick={() => onSelectView('hojasDeVida')} />
            <MenuCard icon="bi-file-earmark-bar-graph-fill" title="Generar Informes" description="Crea reportes de mantenimiento por fechas." onClick={() => onSelectView('informes')} />
            {/* Placeholder para la gestión de activos */}
            <MenuCard icon="bi-grid-fill" title="Gestión de Activos" description="Visualiza y administra tus equipos biomédicos." onClick={() => onSelectView('assets')} />
        </div>
    </>
));

/**
 * Componente principal de la aplicación.
 * Maneja la lógica de enrutamiento y carga de datos globales.
 */
const App = () => {
    const [activeView, setActiveView] = useState('dashboard');
    const [assets, setAssets] = useState([]);
    const [reportTypes, setReportTypes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Mapeo de los detalles de los 38 reportes (simulado)
    const reportDetails = useMemo(() => ({
  "Reporte de Mantenimiento Preventivo Calentador de Paciente": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_manguera",
      "label": "Estado de manguera",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "interruptor_alimentacion",
      "label": "Interruptor de alimentación",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_boquilla",
      "label": "Estado de boquilla",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "cable_electrico",
      "label": "Cable eléctrico",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "reloj",
      "label": "Reloj",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "panel_control",
      "label": "Panel de control",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_base_rodante",
      "label": "Estado de base rodante",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_ruedas_freno",
      "label": "Estado de ruedas/freno",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "filtro_hepa",
      "label": "Filtro HEPA",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Cama Hospitalaria": [
    {
      "name": "estado_fisico_general",
      "label": "Estado físico general",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "control_mano",
      "label": "Control de mano (si aplica)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_barandas",
      "label": "Estado de barandas",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_caja_control",
      "label": "Estado de caja de control",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "bateria",
      "label": "Batería (si aplica)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "cable_alimentacion_electrica",
      "label": "Cable de alimentación eléctrica",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "ruedas",
      "label": "Ruedas (4)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "sistema_freno",
      "label": "Sistema de freno",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_cabecero",
      "label": "Estado de cabecero",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_piecero",
      "label": "Estado de piecero",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_motores",
      "label": "Estado de motores",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_tendidos",
      "label": "Estado de tendidos (espaldar, fijo, piecero y pies)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Desfibrilador NIHON KOHDEN": [
    {
      "name": "estado_unidad_limpia",
      "label": "Unidad limpia y en buen estado",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "verificacion_estructura",
      "label": "Verificación de estructura física",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_parches",
      "label": "Parches",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_bateria",
      "label": "Batería",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "verificacion_carga",
      "label": "Verificación de estado de carga",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_equipo",
      "label": "Test",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "autocomprobacion_automatica",
      "label": "Autocomprobación automática",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "monitoria_ecg",
      "label": "Monitoria ECG",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cable_ecg",
      "label": "Estado de cable de ECG",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "pulsoximetria",
      "label": "Pulsoximetria",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_sensor_spo2",
      "label": "Estado de sensor de SPO2",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_palas_adulto",
      "label": "Estado de palas adulto",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_palas_pediatrico",
      "label": "Estado de palas pediátrico",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "asa_sujecion",
      "label": "Asa de sujeción",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "papel_impresion",
      "label": "Papel/Impresión",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_pantalla",
      "label": "Pantalla",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "prueba_carga_tiempo",
      "label": "Tiempo de carga (12 +/-3 seg)",
      "type": "text"
    },
    {
      "name": "modo_asincrono",
      "label": "Modo asíncrono",
      "type": "text"
    },
    {
      "name": "modo_sync",
      "label": "Modo SYNC",
      "type": "text"
    },
    {
      "name": "energia_5j",
      "label": "Energía 5 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_10j",
      "label": "Energía 10 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_20j",
      "label": "Energía 20 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_30j",
      "label": "Energía 30 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_50j",
      "label": "Energía 50 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_100j",
      "label": "Energía 100 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_200j",
      "label": "Energía 200 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_300j",
      "label": "Energía 300 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_360j",
      "label": "Energía 360 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Electrocardiógrafo": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "cable_paciente",
      "label": "Cable de paciente",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "electrodos_chupas",
      "label": "Electrodos (chupasX6)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "electrodos_clamps",
      "label": "Electrodos (clampsX4)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "panel_control",
      "label": "Panel de control",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_display",
      "label": "Estado de display",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "cabezal_impresion",
      "label": "Cabezal de impresión",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "papel_termico",
      "label": "Papel térmico",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_manual",
      "label": "Funcionamiento modo manual",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_automatico",
      "label": "Funcionamiento modo automático",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "limpieza_cabezal_impresion",
      "label": "Limpieza cabezal de impresión",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "verificacion_bateria",
      "label": "Verificación de bateria (12 v)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "ondas_simulador_30bpm",
      "label": "Ondas con Simulador - 30 bpm",
      "type": "select",
      "options": ["Pasa", "Falla", "Valor Medido"]
    },
    {
      "name": "ondas_simulador_40bpm",
      "label": "Ondas con Simulador - 40 bpm",
      "type": "select",
      "options": ["Pasa", "Falla", "Valor Medido"]
    },
    {
      "name": "ondas_simulador_60bpm",
      "label": "Ondas con Simulador - 60 bpm",
      "type": "select",
      "options": ["Pasa", "Falla", "Valor Medido"]
    },
    {
      "name": "ondas_simulador_80bpm",
      "label": "Ondas con Simulador - 80 bpm",
      "type": "select",
      "options": ["Pasa", "Falla", "Valor Medido"]
    },
    {
      "name": "ondas_simulador_120bpm",
      "label": "Ondas con Simulador - 120 bpm",
      "type": "select",
      "options": ["Pasa", "Falla", "Valor Medido"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Estimulador de Nervio Periférico": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "panel_membrana",
      "label": "Panel de membrana",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "control_intensidad",
      "label": "Control On/Off-Intensidad",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "led_pulso",
      "label": "Led indicador de pulso",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "led_bateria",
      "label": "Led indicador de batería",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_100hz",
      "label": "Funcionamiento 100 Hz",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_tof",
      "label": "Funcionamiento TOF",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_twitch",
      "label": "Funcionamiento TWITCH",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "estado_bateria_9v",
      "label": "Estado de batería (9V)",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "electrodos_bola",
      "label": "Electrodos tipo bola",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "conexion_polo_positivo",
      "label": "Conexión polo positivo",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "conexion_polo_negativo",
      "label": "Conexión polo negativo",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["bien", "Malo", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Laringoscopio": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_baterias",
      "label": "Estado de las baterías",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "bombillo",
      "label": "Bombillo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "base_bombillo",
      "label": "Base del bombillo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_hojas",
      "label": "Estado de las hojas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },

    { 
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
   "Reporte de Mantenimiento Preventivo Báscula": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "estado_tallimetro",
      "label": "Estado de tallímetro",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "verificacion_brazo",
      "label": "Verificación de brazo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "estado_plataforma",
      "label": "Estado de plataforma",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "ajuste_medicion",
      "label": "Ajuste de medición",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "peso_20kg",
      "label": "Peso aplicado (20 Kg)",
      "type": "text"
    },
    {
      "name": "peso_40kg",
      "label": "Peso aplicado (40 Kg)",
      "type": "text"
    },
    {
      "name": "peso_50kg",
      "label": "Peso aplicado (50 Kg)",
      "type": "text"
    },
    {
      "name": "peso_60kg",
      "label": "Peso aplicado (60 Kg)",
      "type": "text"
    },
    {
      "name": "peso_70kg",
      "label": "Peso aplicado (70 Kg)",
      "type": "text"
    },
    {
      "name": "peso_80kg",
      "label": "Peso aplicado (80 Kg)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Camilla": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "barandas_laterales",
      "label": "Barandas laterales",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "ruedas",
      "label": "Ruedas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_freno",
      "label": "Sistema de freno",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_base",
      "label": "Sistema de base",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_hidraulico",
      "label": "Sistema hidráulico",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_tensores",
      "label": "Sistema de tensores",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "movimientos",
      "label": "Movimientos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "colchoneta",
      "label": "Colchoneta",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "Reporte de Mantenimiento Preventivo Calentador de Sangre y Fluidos": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "luz_alarma",
      "label": "Luz indicadora de alarma",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "ranura_casete",
      "label": "Ranura de casete",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "pantalla_alfanumerica",
      "label": "Pantalla alfanumérica",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "interruptor_alimentacion",
      "label": "Interruptor de alimentación",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "soporte_burbujas",
      "label": "Soporte de retención de burbujas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "abrazadera_portasueros",
      "label": "Abrazadera para portasueros",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "punto_ajuste",
      "label": "Punto de ajuste 41 °C",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_placas_calentadoras",
      "label": "Limpieza de placas calentadoras",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "pruebas_funcionales",
      "label": "Pruebas funcionales",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO DESFIBRILADOR MINDRAY": [
    {
      "name": "inspeccion_visual",
      "label": "1. Inspección visual",
      "type": "checkbox_group",
      "options": [
        "Carcaza, pantalla, botones, módulos, cable de alimentación y accesorios en buen estado",
        "Cables de conexión externos y pines de conexión no se evidencian dañados ni sueltos",
        "Inspección y funcionamiento de la impresora",
        "Etiquetas y labels se encuentran claramente legibles"
      ]
    },
    {
      "name": "test_encendido",
      "label": "2. Test de encendido",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_usuario",
      "label": "3. Test de usuario - Resultado",
      "type": "text"
    },
    {
      "name": "desfibrilacion_manual_rango",
      "label": "Desfibrilación Manual (Rango)",
      "type": "text"
    },
    {
      "name": "desfibrilacion_manual_v_medido",
      "label": "Desfibrilación Manual (V. Medido)",
      "type": "text"
    },
    {
      "name": "desfibrilacion_sincronica",
      "label": "Desfibrilación sincrónica (Resultado)",
      "type": "text"
    },
    {
      "name": "test_pacer_rate_70",
      "label": "Test Pacer - Pacer Rate 70ppm",
      "type": "text"
    },
    {
      "name": "test_pacer_out_30",
      "label": "Test Pacer - Pacer Out 30mA",
      "type": "text"
    },
    {
      "name": "test_pacer_rate_170",
      "label": "Test Pacer - Pacer Rate 170ppm",
      "type": "text"
    },
    {
      "name": "test_pacer_out_200",
      "label": "Test Pacer - Pacer Out 200mA",
      "type": "text"
    },
    {
      "name": "test_ecg_lead_off",
      "label": "Test ECG - Lead Off",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_ecg_calibracion",
      "label": "Test ECG - Calibración ECG",
      "type": "text"
    },
    {
      "name": "test_respiracion",
      "label": "Test Respiración (Resultado)",
      "type": "text"
    },
    {
      "name": "test_spo2_mindray_v_medido",
      "label": "Test SPO2 Mindray (V. Medido)",
      "type": "text"
    },
    {
      "name": "test_spo2_mindray_pr",
      "label": "Test SPO2 Mindray (PR bmp)",
      "type": "text"
    },
    {
      "name": "test_spo2_masimo_v_medido",
      "label": "Test SPO2 Masimo (V. Medido)",
      "type": "text"
    },
    {
      "name": "test_spo2_masimo_pr",
      "label": "Test SPO2 Masimo (PR bmp)",
      "type": "text"
    },
    {
      "name": "test_spo2_nellcor_v_medido",
      "label": "Test SPO2 Nellcor (V. Medido)",
      "type": "text"
    },
    {
      "name": "test_spo2_nellcor_pr",
      "label": "Test SPO2 Nellcor (PR bmp)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO DESFIBRILADOR PRIMEDIC": [
    {
      "name": "estado_unidad_limpia",
      "label": "Unidad limpia y en buen estado",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "verificacion_estructura",
      "label": "Verificación de estructura física",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_savepads",
      "label": "Estado de SavePads (opcional)",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_akupak",
      "label": "AkuPak PRIMEDIC",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "verificacion_carga",
      "label": "Verificación de estado de carga",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_savecard",
      "label": "Estado de SaveCard",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_mmi",
      "label": "Test MMI",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "autocomprobacion_automatica",
      "label": "Autocomprobación automática",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_diodo",
      "label": "Estado de diodo",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cf",
      "label": "Estado CF",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "monitoria_ecg",
      "label": "Monitoria ECG",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cable_ecg",
      "label": "Estado de cable de ECG",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "pulsoximetria",
      "label": "Pulsoximetria",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_sensor_spo2",
      "label": "Estado de sensor de SPO2",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_palas_adulto",
      "label": "Estado de palas adulto",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_palas_pediatrico",
      "label": "Estado de palas pediátrico",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "asa_sujecion",
      "label": "Asa de sujeción",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "papel_impresion",
      "label": "Papel/Impresión",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_pantalla",
      "label": "Pantalla",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "prueba_carga_tiempo",
      "label": "Tiempo de carga (12 +/-3 seg)",
      "type": "text"
    },
    {
      "name": "modo_asincrono",
      "label": "Modo asíncrono",
      "type": "text"
    },
    {
      "name": "modo_sync",
      "label": "Modo SYNC",
      "type": "text"
    },
    {
      "name": "energia_5j",
      "label": "Energía 5 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_10j",
      "label": "Energía 10 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_20j",
      "label": "Energía 20 J (+/-3 J)",
      "type": "text"
    },
    {
      "name": "energia_30j",
      "label": "Energía 30 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_50j",
      "label": "Energía 50 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_100j",
      "label": "Energía 100 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_200j",
      "label": "Energía 200 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_300j",
      "label": "Energía 300 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "energia_360j",
      "label": "Energía 360 J (+/-15%)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO DESFIBRILADOR ZOLL": [
    {
      "name": "estado_inspeccion_fisica",
      "label": "1. Inspección física",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "estado_cables",
      "label": "Estado de cables, palas, batería",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_panel_frontal",
      "label": "2. Test de panel frontal",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_leads",
      "label": "3. Test leads x3",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_alimentacion",
      "label": "4. Test de alimentación",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "verificacion_fugas",
      "label": "5. Verificación fugas de corriente",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_palas",
      "label": "6. Test palas",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_hr_120bpm",
      "label": "7. Test hr 120 BPM",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "calibracion_senal",
      "label": "8. Calibración de señal",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "filtro_notch",
      "label": "9. Filtro notch",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_alarma_hr",
      "label": "10. Test alarma hr",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "prueba_desfibrilacion",
      "label": "11. Prueba desfibrilación",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "cardioversion_sincronizada",
      "label": "12. Cardioversión sincronizada",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_descarga_1_150j",
      "label": "13. Test descarga 1-150J (+/-15%)",
      "type": "text"
    },
    {
      "name": "test_descarga_200j",
      "label": "13. Test descarga 200J (170-230J)",
      "type": "text"
    },
    {
      "name": "test_historial",
      "label": "14. Test historial informes",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "test_pacer_180ppm",
      "label": "15. Test pacer 180ppm",
      "type": "text"
    },
    {
      "name": "test_pacer_salida_60ma",
      "label": "15. Test pacer salida 60mA",
      "type": "text"
    },
    {
      "name": "test_pacer_estimulo",
      "label": "15. Test pacer estimulo 60 mm",
      "type": "text"
    },
    {
      "name": "peso_20kg",
      "label": "Simulación de parámetros: 20 Kg",
      "type": "text"
    },
    {
      "name": "peso_40kg",
      "label": "Simulación de parámetros: 40 Kg",
      "type": "text"
    },
    {
      "name": "peso_50kg",
      "label": "Simulación de parámetros: 50 Kg",
      "type": "text"
    },
    {
      "name": "peso_60kg",
      "label": "Simulación de parámetros: 60 Kg",
      "type": "text"
    },
    {
      "name": "peso_70kg",
      "label": "Simulación de parámetros: 70 Kg",
      "type": "text"
    },
    {
      "name": "peso_80kg",
      "label": "Simulación de parámetros: 80 Kg",
      "type": "text"
    },
    {
      "name": "peso_100kg",
      "label": "Simulación de parámetros: 100 Kg",
      "type": "text"
    },
    {
      "name": "peso_120kg",
      "label": "Simulación de parámetros: 120 Kg",
      "type": "text"
    },
    {
      "name": "peso_150kg",
      "label": "Simulación de parámetros: 150 Kg",
      "type": "text"
    },
    {
      "name": "peso_200kg",
      "label": "Simulación de parámetros: 200 Kg",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO ELECTROBISTURÍ": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "panel_membrana",
      "label": "Panel de membrana",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "indicadores_potencia",
      "label": "Indicadores de potencia",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "panel_frontal_posterior",
      "label": "Panel frontal/posterior",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "dosificadores_cut_coag_bipolar",
      "label": "Dosificadores cut, coag, bipolar",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "lapiz_electrodo_placa",
      "label": "Lápiz/ electrodo/placa paciente",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "pinza_bipolar_cable",
      "label": "Pinza bipolar/ cable bipolar",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "pedal_monopolar_bipolar",
      "label": "Pedal monopolar / bipolar",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "inspeccion_componentes_internos",
      "label": "Inspección de componentes internos",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "auto_chequeo_inicio",
      "label": "Auto-chequeo de inicio",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Pasa", "Falla"]
    },
    {
      "name": "bipolar_precise_23w",
      "label": "Bipolar Precise - 23W",
      "type": "text"
    },
    {
      "name": "bipolar_precise_45w",
      "label": "Bipolar Precise - 45W",
      "type": "text"
    },
    {
      "name": "bipolar_precise_70w",
      "label": "Bipolar Precise - 70W",
      "type": "text"
    },
    {
      "name": "bipolar_standard_23w",
      "label": "Bipolar Standard - 23W",
      "type": "text"
    },
    {
      "name": "bipolar_standard_45w",
      "label": "Bipolar Standard - 45W",
      "type": "text"
    },
    {
      "name": "bipolar_standard_70w",
      "label": "Bipolar Standard - 70W",
      "type": "text"
    },
    {
      "name": "cut_low_100w",
      "label": "Cut Low - 100W",
      "type": "text"
    },
    {
      "name": "cut_low_200w",
      "label": "Cut Low - 200W",
      "type": "text"
    },
    {
      "name": "cut_low_300w",
      "label": "Cut Low - 300W",
      "type": "text"
    },
    {
      "name": "cut_pure_100w",
      "label": "Cut Pure - 100W",
      "type": "text"
    },
    {
      "name": "cut_pure_200w",
      "label": "Cut Pure - 200W",
      "type": "text"
    },
    {
      "name": "cut_pure_300w",
      "label": "Cut Pure - 300W",
      "type": "text"
    },
    {
      "name": "cut_blend_65w",
      "label": "Cut Blend - 65W",
      "type": "text"
    },
    {
      "name": "cut_blend_130w",
      "label": "Cut Blend - 130W",
      "type": "text"
    },
    {
      "name": "cut_blend_200w",
      "label": "Cut Blend - 200W",
      "type": "text"
    },
    {
      "name": "coag_low_40w",
      "label": "Coag Low - 40W",
      "type": "text"
    },
    {
      "name": "coag_low_80w",
      "label": "Coag Low - 80W",
      "type": "text"
    },
    {
      "name": "coag_low_120w",
      "label": "Coag Low - 120W",
      "type": "text"
    },
    {
      "name": "coag_med_40w",
      "label": "Coag Med - 40W",
      "type": "text"
    },
    {
      "name": "coag_med_80w",
      "label": "Coag Med - 80W",
      "type": "text"
    },
    {
      "name": "coag_med_120w",
      "label": "Coag Med - 120W",
      "type": "text"
    },
    {
      "name": "coag_high_40w",
      "label": "Coag High - 40W",
      "type": "text"
    },
    {
      "name": "coag_high_80w",
      "label": "Coag High - 80W",
      "type": "text"
    },
    {
      "name": "coag_high_120w",
      "label": "Coag High - 120W",
      "type": "text"
    },
    {
      "name": "rem",
      "label": "REM",
      "type": "text"
    },
    {
      "name": "corriente_fuga",
      "label": "Corriente de fuga (menor o igual 300 μΑ)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO EQUIPO DE ÓRGANOS": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cabezal_otoscopio",
      "label": "Cabezal de otoscopio",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cabezal_oftalmoscopio",
      "label": "Cabezal de oftalmoscopio",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "bombillos_cabezales",
      "label": "Bombillos cabezales",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "interruptor_encendido",
      "label": "Interruptor de encendido",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sensores_opticos",
      "label": "Sensores ópticos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "selector_cabezal",
      "label": "Selector de cabezal",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "condicion_cables",
      "label": "Condición de los cables entorchados",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "verificacion_aperturas",
      "label": "Verificación aperturas del oftalmoscopio",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "fusibles",
      "label": "Fusibles",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_bateria",
      "label": "Estado de bateria",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO FLUJÓMETRO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "cubierta_protectora",
      "label": "Cubierta protectora",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "flujometro",
      "label": "Flujómetro",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "rotametro",
      "label": "Rotámetro",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "valvula_control_flujo",
      "label": "Válvula de control de flujo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "manifold",
      "label": "Manifold",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "o_rings",
      "label": "Anillos 'O' (O rings)",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "conector_externo",
      "label": "Conector externo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "revision_fugas",
      "label": "Revisión de fugas",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "limpieza_interna",
      "label": "Limpieza interna",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO FOTOFORO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cinta_frontal",
      "label": "Cinta frontal",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_lampara",
      "label": "Estado de lámpara",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cargador",
      "label": "Cargador",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "interruptor_on_off",
      "label": "Interruptor ON/OFF",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_sujecion_cable",
      "label": "Sistema de sujeción de cable",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "pruebas_funcionamiento",
      "label": "Pruebas de funcionamiento",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO INCUBADORA MUESTRA BIOLÓGICA VAPOR": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "canastilla_porta_tubos",
      "label": "Canastilla porta tubos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "canastilla_ruptura",
      "label": "Canastilla para ruptura",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "temperatura_operacion",
      "label": "Temperatura de operación (60°C +/- 2°C)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "leds_indicadores",
      "label": "Leds indicadores de resultado y operación",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "boton_silenciador_alarma",
      "label": "Botón silenciador de alarma",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "boton_tiempo_restante",
      "label": "Botón tiempo restante",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "display_doble",
      "label": "Display doble",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_termostato",
      "label": "Estado de termostato",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_resistencia",
      "label": "Estado de resistencia",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "tapa_superior_acrilico",
      "label": "Tapa superior en acrílico",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO INFUSOR": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "manometro",
      "label": "Manómetro",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "condicion_pera",
      "label": "Condición de la pera",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "valvula_alivio",
      "label": "Válvula de alivio",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "condicion_brazalete",
      "label": "Condición del brazalete",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "condicion_funda",
      "label": "Condición de funda",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "presion_0mmhg",
      "label": "Prueba de Presión (0 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_60mmhg",
      "label": "Prueba de Presión (60 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_100mmhg",
      "label": "Prueba de Presión (100 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_150mmhg",
      "label": "Prueba de Presión (150 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_200mmhg",
      "label": "Prueba de Presión (200 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_250mmhg",
      "label": "Prueba de Presión (250 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_300mmhg",
      "label": "Prueba de Presión (300 mmHg)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO LÁMPARA CIELITICA": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_satelites",
      "label": "Estado de satélites (x2)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_cabezales",
      "label": "Estado de cabezales (x2)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_bombillos",
      "label": "Estado de bombillos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "diodos_led",
      "label": "Diodos LED",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "panel_control",
      "label": "Panel de control",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_brazos",
      "label": "Estado de brazos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_manilares",
      "label": "Estado de manilares (x2)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "rieles_movimiento",
      "label": "Rieles de movimiento (x6)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_filtros",
      "label": "Estado de filtros",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estructura_fijadora_techo",
      "label": "Estructura fijadora a techo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_camara_hd",
      "label": "Estado de cámara HD (si aplica)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "haz_de_luz",
      "label": "Haz de luz/ foco/dispersión de luz",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO LÁMPARA CUELLO DE CISNE": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "conexiones_electricas",
      "label": "Conexiones eléctricas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "bombillo",
      "label": "Bombillo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "porta_bombillo",
      "label": "Porta bombillo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "interruptor_on_off",
      "label": "Interruptor ON/OFF",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "reflector",
      "label": "Reflector",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "base_lampara",
      "label": "Base de lámpara",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO LÁMPARA PIELITICA": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "bombillos_led",
      "label": "Bombillos LED",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "base_rodante",
      "label": "Base rodante",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_cuello",
      "label": "Estado de cuello",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sensor_encendido_apagado",
      "label": "Verificación de sensor de encendido/apagado",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sensor_intensidad",
      "label": "Verificación de sensor de intensidad",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_cabezal",
      "label": "Estado de cabezal",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO MÁQUINA DE ANESTESIA": [
    {
      "name": "estado_mueble",
      "label": "Estado del mueble",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "manometros_presion_entrada",
      "label": "Manómetros presión de entrada",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "mangueras_alta_presion",
      "label": "Mangueras de alta presión",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sistema_freno_ruedas",
      "label": "Sistema de freno / ruedas",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "cilindro_emergencia",
      "label": "Cilindro de emergencia",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "cable_alimentacion_electrica",
      "label": "Cable de alimentación eléctrica",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_flujometros",
      "label": "Estado de flujómetros",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_pantalla_remota_avs",
      "label": "Estado de pantalla remota del AV-S",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_absorbedor",
      "label": "Estado de absorbedor",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "unidad_control_ventilador",
      "label": "Unidad de control del ventilador",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "fuelle",
      "label": "Fuelle",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "salida_sist_evacuacion_gases",
      "label": "Salida sist evacuación de gases anestésicos",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "bloque_cgo",
      "label": "Bloque CGO (suministro de gas fresco)",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "posicion_control_bag_vent",
      "label": "Posición control Bag/Vent del absorbedor",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "conexiones_interfase_sp2",
      "label": "Conexiones interfase prima SP2 y A200SP",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "bateria_soporte",
      "label": "Batería (soporte 30 min totalmente cargada)",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "test_valvula_apl",
      "label": "Test funcionamiento Válvula APL",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sensor_oxigeno",
      "label": "Sensor de oxígeno",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sensor_flujo_inspiratorio",
      "label": "Sensor de flujo inspiratorio",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sensores_flujo_espiratorio",
      "label": "Sensores de flujo espiratorio",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "canister",
      "label": "Canister",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "calefactor",
      "label": "Calefactor",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "drenaje_condensados",
      "label": "Drenaje de condensados",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_autochequeo_inicio",
      "label": "Autochequeo de inicio",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_modo_volumen",
      "label": "Modo volumen",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_modo_presion",
      "label": "Modo presión",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_modo_simv",
      "label": "Modo SIMV",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_modo_smmv",
      "label": "Modo SMMV",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_modo_psv",
      "label": "Modo PSV",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_peep",
      "label": "PEEP",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_monitor_oxigeno",
      "label": "Monitor de oxígeno",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_espirometria",
      "label": "Espirometria",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_fugas_baja_presion",
      "label": "Fugas de baja presión",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "prueba_fugas_alta_presion",
      "label": "Fugas de alta presión",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "param_volumen_vt",
      "label": "Volumen (Vt Adulto - 600 mL) Valor Medido",
      "type": "text"
    },
    {
      "name": "param_presion_medida",
      "label": "Presión (Adulto - 10-50 cmH2O) Valor Medido",
      "type": "text"
    },
    {
      "name": "param_simv_vt",
      "label": "SIMV (Vt Adulto - 600 mL) Valor Medido",
      "type": "text"
    },
    {
      "name": "param_smmv_vm",
      "label": "SMMV (Vm Adulto - 3.6 L) Valor Medido",
      "type": "text"
    },
    {
      "name": "param_psv_presion",
      "label": "PSV (Presión Soporte 10 cmH2O) Valor Medido",
      "type": "text"
    },
    {
      "name": "param_fugas_valor",
      "label": "Test de fugas (ml/min) Valor",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO MARCAPASOS": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_bateria_9v",
      "label": "Estado de batería (9V)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_sockets",
      "label": "Estado de sockets",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_perillas",
      "label": "Estado de perillas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_leds",
      "label": "Estado de leds",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "frecuencia_simulacion",
      "label": "Frecuencia de simulación X2, X4",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO MESA QUIRÚRGICA": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_hidraulico",
      "label": "Funcionamiento sistema hidráulico",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "verificacion_movimientos",
      "label": "Verificación de todos los movimientos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "control_mano",
      "label": "Control de mano",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_frenos",
      "label": "Sistema de frenos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_ruedas",
      "label": "Estado de ruedas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_colchonetas_descansa_brazos",
      "label": "Estado de colchonetas y descansa - brazos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_pieceros",
      "label": "Estado de pieceros",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_cabecero",
      "label": "Estado de cabecero",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "accesorios",
      "label": "Accesorios",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "nivel_aceite",
      "label": "Nivel de aceite",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO MICROSCOPIO QUIRÚRGICO": [
    {
      "name": "revision_fisica_funcional",
      "label": "Revisión física y funcional",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_interna_externa",
      "label": "Limpieza interna y externa",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "revision_sistema_optico",
      "label": "Revisión de sistema óptico",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "lubricacion",
      "label": "Lubricación",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "ajuste_piezas_mecanicas",
      "label": "Ajuste de piezas mecánicas",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "verificacion_base_rodante",
      "label": "Verificación de Base rodante",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "frenos",
      "label": "Frenos",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "fibra_optica",
      "label": "Fibra óptica",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "tubos_binoculares",
      "label": "Tubos binoculares",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_lampara",
      "label": "Estado de lámpara",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "caja_lampara",
      "label": "Caja de lámpara",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "lentes",
      "label": "Lente(s)",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "estado_columna",
      "label": "Estado de columna",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "sistema_electrico",
      "label": "Sistema eléctrico",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
"REPORTE DE MANTENIMIENTO PREVENTIVO MONITOR DE SIGNOS VITALES": [
    {
      "name": "estado_fisico_carcasa",
      "label": "Estado físico de la carcasa",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_asa_sujecion",
      "label": "Estado de asa de sujeción",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "verificacion_botones",
      "label": "Verificación de botones",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "verificacion_perilla_navegacion",
      "label": "Verificación perilla navegación",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_accesorios_ecg",
      "label": "Estado accesorios ECG/latiguillos",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sensor_spo2",
      "label": "Sensor SPO2",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "manguera_brazalete_nibp",
      "label": "Manguera y brazalete NIBP",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "cable_invasiva",
      "label": "Cable para invasiva",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "sensor_temperatura",
      "label": "Sensor de temperatura",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "bateria_12v",
      "label": "Batería (12 V)",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "modulo_capnografia",
      "label": "Módulo de capnografía",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "ecg_30bpm",
      "label": "ECG (Amplitud 1 mV) - 30 bpm (Tolerancia: 29-31)",
      "type": "text"
    },
    {
      "name": "ecg_60bpm",
      "label": "ECG (Amplitud 1 mV) - 60 bpm (Tolerancia: 59-61)",
      "type": "text"
    },
    {
      "name": "ecg_120bpm",
      "label": "ECG (Amplitud 1 mV) - 120 bpm (Tolerancia: 119-121)",
      "type": "text"
    },
    {
      "name": "ecg_240bpm",
      "label": "ECG (Amplitud 1 mV) - 240 bpm (Tolerancia: 238-242)",
      "type": "text"
    },
    {
      "name": "ecg_300bpm",
      "label": "ECG (Amplitud 1 mV) - 300 bpm (Tolerancia: 297-303)",
      "type": "text"
    },
    {
      "name": "temp_24c",
      "label": "TEMP - 24 ℃ (Tolerancia: +/- 0,1)",
      "type": "text"
    },
    {
      "name": "temp_37c",
      "label": "TEMP - 37 ℃ (Tolerancia: +/- 0,1)",
      "type": "text"
    },
    {
      "name": "temp_40c",
      "label": "TEMP - 40 ℃ (Tolerancia: +/- 0,1)",
      "type": "text"
    },
    {
      "name": "nibp_adulto_120_80",
      "label": "NIBP Adulto - 120/80 (Tolerancia: +/- 5mmHg)",
      "type": "text"
    },
    {
      "name": "nibp_adulto_80_50",
      "label": "NIBP Adulto - 80/50 (Tolerancia: +/- 5 mmHg)",
      "type": "text"
    },
    {
      "name": "nibp_adulto_70_40",
      "label": "NIBP Adulto - 70/40 (Tolerancia: +/- 5 mmHg)",
      "type": "text"
    },
    {
      "name": "resp_fr_15",
      "label": "RESP/FR - 15 (Tolerancia: 14-16)",
      "type": "text"
    },
    {
      "name": "resp_fr_30",
      "label": "RESP/FR - 30 (Tolerancia: 29-31)",
      "type": "text"
    },
    {
      "name": "resp_fr_120",
      "label": "RESP/FR - 120 (Tolerancia: 118-122)",
      "type": "text"
    },
    {
      "name": "neonatal_160bpm",
      "label": "Neonatal - 160 bpm (Tolerancia: +/- 3)",
      "type": "text"
    },
    {
      "name": "neonatal_80bpm",
      "label": "Neonatal - 80 bpm (Tolerancia: +/- 3)",
      "type": "text"
    },
    {
      "name": "neonatal_40bpm",
      "label": "Neonatal - 40 bpm (Tolerancia: +/- 3)",
      "type": "text"
    },
    {
      "name": "spo2_100",
      "label": "SPO2 - 100% (Tolerancia: +/- 2)",
      "type": "text"
    },
    {
      "name": "spo2_96",
      "label": "SPO2 - 96% (Tolerancia: +/- 2)",
      "type": "text"
    },
    {
      "name": "spo2_80",
      "label": "SPO2 - 80% (Tolerancia: +/- 2)",
      "type": "text"
    },
    {
      "name": "presion_invasiva_estatica_0mmhg",
      "label": "PRESIÓN INVASIVA (Arterial) Estática - 0 mmHg (Tolerancia: +/- 2 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_invasiva_estatica_80mmhg",
      "label": "PRESIÓN INVASIVA (Arterial) Estática - 80 mmHg (Tolerancia: +/- 2 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_invasiva_dinamica_120_80",
      "label": "PRESIÓN INVASIVA Dinámica - 120/80mmHg (Tolerancia: +/- 2 mmHg)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO NEBULIZADOR": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "interruptor_encendido_apagado",
      "label": "Interruptor de encendido/apagado",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "salida_aire",
      "label": "Salida de aire",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "manilar_transporte",
      "label": "Manilar de transporte",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "aberturas_ventilacion",
      "label": "Aberturas de ventilación",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "filtro_tapa",
      "label": "Filtro y tapa de filtro",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO NEGATOSCOPIO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "interruptor_on_off",
      "label": "Interruptor ON/OFF",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "estado_pintura",
      "label": "Estado de pintura",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "estado_pantalla",
      "label": "Estado de pantalla",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Pasa", "Falla", "Observaciones"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
   "REPORTE DE MANTENIMIENTO PREVENTIVO PULSIOXÍMETRO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_pantalla_lcd",
      "label": "Estado de pantalla LCD",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_boton_alimentacion",
      "label": "Estado de botón de alimentación",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_boton_retroiluminacion",
      "label": "Estado de boton de retroiluminación",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_boton_confirmacion_id",
      "label": "Estado de boton de confirmación ID",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_sensor_saturacion",
      "label": "Estado de sensor de saturación",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "baterias_aa",
      "label": "Baterias AA (X4)",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "puerto_conexion_sensor",
      "label": "Puerto de conexión de sensor",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "test_inicio",
      "label": "Test de inicio",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "base_cargador",
      "label": "Base cargador (si aplica)",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "saturacion_100",
      "label": "A.) SATURACIÓN DE OXÍGENO - 100% (Tolerancia: +/- 2%)",
      "type": "text"
    },
    {
      "name": "saturacion_96",
      "label": "A.) SATURACIÓN DE OXÍGENO - 96% (Tolerancia: +/- 2%)",
      "type": "text"
    },
    {
      "name": "saturacion_94",
      "label": "A.) SATURACIÓN DE OXÍGENO - 94% (Tolerancia: +/- 2%)",
      "type": "text"
    },
    {
      "name": "saturacion_90",
      "label": "A.) SATURACIÓN DE OXÍGENO - 90% (Tolerancia: +/- 2%)",
      "type": "text"
    },
    {
      "name": "saturacion_80",
      "label": "A.) SATURACIÓN DE OXÍGENO - 80% (Tolerancia: +/- 2%)",
      "type": "text"
    },
    {
      "name": "frecuencia_180bpm",
      "label": "B.) FRECUENCIA CARDÍACA - 180 bpm (Tolerancia: +/- 2 bpm)",
      "type": "text"
    },
    {
      "name": "frecuencia_160bpm",
      "label": "B.) FRECUENCIA CARDÍACA - 160 bpm (Tolerancia: +/- 2 bpm)",
      "type": "text"
    },
    {
      "name": "frecuencia_120bpm",
      "label": "B.) FRECUENCIA CARDÍACA - 120 bpm (Tolerancia: +/- 2 bpm)",
      "type": "text"
    },
    {
      "name": "frecuencia_80bpm",
      "label": "B.) FRECUENCIA CARDÍACA - 80 bpm (Tolerancia: +/- 2 bpm)",
      "type": "text"
    },
    {
      "name": "frecuencia_40bpm",
      "label": "B.) FRECUENCIA CARDÍACA - 40 bpm (Tolerancia: +/- 2 bpm)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
    "REPORTE DE MANTENIMIENTO PREVENTIVO REGULADOR DE SUCCIÓN": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_manometro",
      "label": "Estado de manómetro",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_acrilico_manometro",
      "label": "Estado de acrílico de manómetro",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "funcionamiento_regulador_succion",
      "label": "Funcionamiento de regulador de succión",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_filtro_antibacteriano",
      "label": "Estado de filtro anti-bacteriano",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "funcionamiento_boton_on",
      "label": "Funcionamiento boton ON",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "funcionamiento_boton_off",
      "label": "Funcionamiento boton OFF",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_frasco_seguridad",
      "label": "Estado de frasco de seguridad",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "estado_conector",
      "label": "Estado de conector",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "conexion_pared",
      "label": "Conexióna pared",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["PASA", "FALLA"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO SELLADORA ELÉCTRICA": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "interruptor_on_off",
      "label": "Interruptor ON/OFF",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "display_control_temperatura",
      "label": "Display control de temperatura",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "rejillas_ventilacion",
      "label": "Rejillas de ventilación",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "ajuste_lamina_guia",
      "label": "Ajuste de lámina guía",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "banda_para_papel",
      "label": "Banda para papel",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO SIERRA PARA YESOS": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "interruptor_encendido",
      "label": "Interruptor de encendido",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "hojas_sierra",
      "label": "Hojas de la sierra",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "anillo_fijador_hoja",
      "label": "Anillo fijador de hoja",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "tornillo_montaje",
      "label": "Tornillo de montaje",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "cable_ac",
      "label": "Cable AC",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO SUCCIONADOR": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "filtro_entrada",
      "label": "Filtro de entrada",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "condicion_manometro",
      "label": "Condición de manómetro",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "valvula_reguladora_succion",
      "label": "Válvula reguladora de succión",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "maxima_succion",
      "label": "Máxima succión",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "motor",
      "label": "Motor",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "mangueras",
      "label": "Mangueras",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "botella_recolectora",
      "label": "Botella recolectora",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_base_rodante",
      "label": "Estado de base rodante (si aplica)",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO TENSIÓMETRO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "manometro",
      "label": "Manómetro",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "condicion_pera",
      "label": "Condición de la pera",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "valvula_alivio",
      "label": "Válvula de alivio",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "condicion_brazalete",
      "label": "Condicón del brazalete",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "manguera_brazalete",
      "label": "Manguera del brazalete",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "soporte_pared",
      "label": "Soporte a pared",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "presion_0mmhg",
      "label": "Prueba de Presión - 0 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_60mmhg",
      "label": "Prueba de Presión - 60 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_100mmhg",
      "label": "Prueba de Presión - 100 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_150mmhg",
      "label": "Prueba de Presión - 150 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_200mmhg",
      "label": "Prueba de Presión - 200 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_250mmhg",
      "label": "Prueba de Presión - 250 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_300mmhg",
      "label": "Prueba de Presión - 300 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO TERMÓMETRO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_pantalla_lcd",
      "label": "Estado de pantalla LCD",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_sonda",
      "label": "Estado de la sonda",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "revision_boton_expulsion",
      "label": "Revisión botón de expulsión",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "covers",
      "label": "Covers",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_botones",
      "label": "Estado de botones",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "compartimiento_baterias",
      "label": "Compartimiento para baterías",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_baterias",
      "label": "Estado de baterías (X3 AA)",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "revision_modo_monitor",
      "label": "Revisión modo monitor",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "revision_modo_oral",
      "label": "Revisión modo oral",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "revision_modo_axilar",
      "label": "Revisión modo axilar",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "revision_modo_rectal",
      "label": "Revisión modo rectal",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "verificacion_mediciones",
      "label": "Verificación de mediciones",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO TORNIQUETE NEUMÁTICO": [
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "manometro",
      "label": "Manómetro",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "condicion_pera",
      "label": "Condición de la pera",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "valvula_alivio",
      "label": "Válvula de alivio",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "condicion_brazalete",
      "label": "Condicón del brazalete",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "manguera_brazalete",
      "label": "Manguera del brazalete",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "presion_0mmhg",
      "label": "Prueba de Presión - 0 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_100mmhg",
      "label": "Prueba de Presión - 100 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_250mmhg",
      "label": "Prueba de Presión - 250 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_400mmhg",
      "label": "Prueba de Presión - 400 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_550mmhg",
      "label": "Prueba de Presión - 550 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_650mmhg",
      "label": "Prueba de Presión - 650 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "presion_700mmhg",
      "label": "Prueba de Presión - 700 mmHg (Tolerancia: +/- 3 mmHg)",
      "type": "text"
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    }
  ],
  "REPORTE DE MANTENIMIENTO PREVENTIVO VISUALIZADOR DE VENAS": [
    {
      "name": "fecha_mantenimiento",
      "label": "Fecha",
      "type": "date"
    },
    {
      "name": "placa",
      "label": "Placa",
      "type": "text"
    },
    {
      "name": "ubicacion",
      "label": "Ubicación",
      "type": "text"
    },
    {
      "name": "marca",
      "label": "Marca",
      "type": "text"
    },
    {
      "name": "modelo",
      "label": "Modelo",
      "type": "text"
    },
    {
      "name": "serie",
      "label": "Serie",
      "type": "text"
    },
    {
      "name": "tiempo_duracion",
      "label": "Tiempo de duración del mantenimiento",
      "type": "text"
    },
    {
      "name": "estado_fisico_equipo",
      "label": "Estado físico del equipo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "bombillo",
      "label": "Bombillo",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "base_rodante",
      "label": "Base rodante",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_cuello",
      "label": "Estado de cuello",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "verificacion_boton_encendido_apagado",
      "label": "Verifcación de botón de encendido/apagado",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "estado_cabezal",
      "label": "Estado de cabezal",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "panel_control",
      "label": "Panel de control",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "bateria",
      "label": "Batería",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "funcionamiento_general",
      "label": "Funcionamiento general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "limpieza_general",
      "label": "Limpieza general",
      "type": "select",
      "options": ["Bien", "Mal", "Revisar"]
    },
    {
      "name": "observaciones_adicionales",
      "label": "Observaciones y resultado del mantenimiento",
      "type": "textarea"
    },
    {
      "name": "repuestos_utilizados",
      "label": "Repuestos utilizados",
      "type": "textarea"
    },
    {
      "name": "ingeniero_tecnico_nombre",
      "label": "Ingeniero/Técnico Responsable - Nombre",
      "type": "text"
    },
    {
      "name": "ingeniero_tecnico_cargo",
      "label": "Ingeniero/Técnico Responsable - Cargo",
      "type": "text"
    },
    {
      "name": "recibe_nombre",
      "label": "Recibe a satisfacción - Nombre",
      "type": "text"
    },
    {
      "name": "recibe_cargo",
      "label": "Recibe a satisfacción - Cargo",
      "type": "text"
    }
  ]

}), []);


    // Carga inicial de datos desde la API
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [assetsRes, typesRes] = await Promise.all([
                    fetch('/biomedicos/api/activos-biomedicos'),
                    fetch('/biomedicos/api/mantenimiento-tipos')
                ]);

                if (!assetsRes.ok || !typesRes.ok) {
                    throw new Error('Error al cargar datos de la API.');
                }
                const assetsData = await assetsRes.json();
                const typesData = await typesRes.json();
                setAssets(assetsData);
                setReportTypes(typesData);
            } catch (err) {
                setError(err.message);
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const stats = useMemo(() => ({
        totalAssets: assets.length,
        assetsInMaintenance: assets.filter(a => a.estado === 'En Mantenimiento').length,
    }), [assets]);

    const handleSelectView = useCallback((view) => setActiveView(view), []);

    // Simula el enrutamiento de la aplicación con un switch
    switch (activeView) {
        case 'mantenimientos':
            return <MaintenanceListView onBack={() => handleSelectView('dashboard')} allAssets={assets} allReportTypes={reportTypes} />;
        case 'informes':
            return <div><button className="btn btn-secondary mb-3" onClick={() => handleSelectView('dashboard')}>Volver</button><h2>Informes (En construcción)</h2></div>;
        case 'dashboard':
        default:
            return <DashboardView onSelectView={handleSelectView} stats={stats} />;
    }
};

const MenuCard = React.memo(({ icon, title, description, onClick }) => (
    <div className="col">
        <div className="card h-100 shadow-sm text-center p-3" onClick={onClick} style={{ cursor: 'pointer', transition: 'transform 0.2s' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.03)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
            <div className="card-body">
                <i className={`bi ${icon} fs-1 text-primary`}></i>
                <h5 className="card-title mt-3">{title}</h5>
                <p className="card-text text-muted">{description}</p>
            </div>
        </div>
    </div>
));

// --- INICIO DE LA APLICACIÓN ---
const container = document.getElementById('biomedical-root');
if (container) {
    const root = ReactDOM.createRoot(container);
    root.render(<App />);
}
