// ============================================================================
// WIZARD DE ACTIVOS - DISEÑO iOS MINIMALISTA
// Versión 4.2 - Refactorizado con useReducer y validación robusta
// ============================================================================

import React, { useState, useEffect, useCallback, useReducer, useMemo, useRef } from 'react';

// ============================================================================
// REGLAS DE VALIDACIÓN
// ============================================================================

const validationRules = {
    1: (data) => {
        const errors = {};
        if (!data.tipo_propiedad) {
            errors.tipo_propiedad = ['Debe seleccionar un tipo de propiedad.'];
        }
        return errors;
    },
    2: (data) => {
        const errors = {};
        if (!data.nombre_activo?.trim()) {
            errors.nombre_activo = ['El nombre del activo es requerido.'];
        }
        if (!data.placa_codigo_interno?.trim()) {
            errors.placa_codigo_interno = ['La placa o código interno es requerido.'];
        }
        return errors;
    },
    3: (data) => {
        const errors = {};
        if (data.tipo_propiedad === 'Propio') {
            if (!data.clase_id) {
                errors.clase_id = ['La clase de activo es requerida.'];
            }
        }
        if (data.tipo_propiedad === 'Ajeno') {
            if (!data.propietario_ajeno?.trim()) {
                errors.propietario_ajeno = ['El propietario es requerido.'];
            }
        }
        return errors;
    },
    4: (data, atributos) => {
        const errors = {};
        if (Array.isArray(atributos)) {
            atributos.forEach(attr => {
                if (attr.required) {
                    const value = (data.atributos_dinamicos ?? {})[attr.name];
                    if (!value || (typeof value === 'string' && !value.trim())) {
                        errors[attr.name] = [`El campo "${attr.label}" es requerido.`];
                    }
                }
            });
        }
        return errors;
    }
};


// ============================================================================
// HOOKS PERSONALIZADOS
// ============================================================================

/**
 * Hook para gestionar el estado del wizard con useReducer.
 */
const useWizardState = (initialAssetData) => {
    const base = {
        tipo_propiedad: '',
        nombre_activo: '',
        placa_codigo_interno: '',
        marca: '',
        modelo: '',
        serie: '',
        ubicacion: '',
        estado: 'Operativo',
        observaciones: '',
        clase_id: '',
        valor_comercial: '',
        valor_compra: '',
        fecha_compra: '',
        proveedor_id: '',
        funcionario_id: '',
        origen_adquisicion: '',
        propietario_ajeno: '',
        condicion_tenencia: '',
        es_ingreso_temporal: false,
        fecha_inicio_temporal: '',
        fecha_fin_temporal: '',
        orden_compra: null,
        factura: null,
        documento_soporte: null,
        atributos_dinamicos: {}
    };
    const initialState = {
        step: 1,
        loading: false,
        message: null,
        clases: [],
        proveedores: [],
        funcionarios: [],
        atributos: [],
        data: initialAssetData ? {...base, ...initialAssetData, atributos_dinamicos: initialAssetData.atributos_dinamicos ?? {}} : base,
        error: null,
        errors: {}
    };

    const reducer = (state, action) => {
        switch (action.type) {
            case 'SET_STEP':
                return { ...state, step: action.payload };
            case 'NEXT_STEP':
                return { ...state, step: state.step + 1, errors: {} };
            case 'PREV_STEP':
                return { ...state, step: state.step - 1, errors: {} };
            case 'SET_LOADING':
                return { ...state, loading: action.payload };
            case 'SET_MESSAGE':
                return { ...state, message: action.payload };
            case 'SET_CLASES':
                return { ...state, clases: action.payload };
            case 'SET_PROVEEDORES':
                return { ...state, proveedores: action.payload };
            case 'SET_FUNCIONARIOS':
                return { ...state, funcionarios: action.payload };
            case 'SET_ATRIBUTOS':
                return { ...state, atributos: action.payload, loading: false };
            case 'HANDLE_CHANGE':
                const newErrors = { ...state.errors };
                delete newErrors[action.payload.name];
                return {
                    ...state,
                    data: { ...state.data, [action.payload.name]: action.payload.value },
                    errors: newErrors
                };
            case 'HANDLE_FILE_CHANGE':
                return {
                    ...state,
                    data: { ...state.data, [action.payload.name]: action.payload.file }
                };
            case 'HANDLE_ATRIBUTO_CHANGE':
                const newAttrErrors = { ...state.errors };
                delete newAttrErrors[action.payload.name];
                return {
                    ...state,
                    data: {
                        ...state.data,
                        atributos_dinamicos: {
                            ...(state.data.atributos_dinamicos ?? {}),
                            [action.payload.name]: action.payload.value
                        }
                    },
                    errors: newAttrErrors
                };
            case 'SET_ERROR':
                return { ...state, error: action.payload, loading: false };
            case 'SET_VALIDATION_ERRORS':
                return { ...state, errors: action.payload };
            case 'RESET':
                return initialState;
            default:
                return state;
        }
    };

    return useReducer(reducer, initialState);
};


// ============================================================================
// COMPONENTE PRINCIPAL DEL WIZARD
// ============================================================================

const AssetWizard = ({ mode = 'create', assetData = null }) => {
    console.log('🎬 Wizard iniciado -', mode, assetData);

    const [state, dispatch] = useWizardState(assetData);
    const { step, loading, message, clases, proveedores, funcionarios, atributos, data, error, errors } = state;
    const abortControllerRef = useRef(null);

    // Normalización de IDs - Mapa de entidades seleccionadas
    const selectedEntitiesMap = useMemo(() => ({
        proveedor: proveedores.find(p => p.id == data.proveedor_id) ?? null,
        funcionario: funcionarios.find(f => f.id == data.funcionario_id) ?? null,
        clase: clases.find(c => c.id == data.clase_id) ?? null
    }), [proveedores, funcionarios, clases, data.proveedor_id, data.funcionario_id, data.clase_id]);

    // ========================================================================
    // CARGAR DATOS INICIALES
    // ========================================================================
    useEffect(() => {
        // Cargar clases
        fetch('/activos/api/clases')
            .then(res => {
                if (!res.ok) throw new Error('No se pudo obtener la lista de clases.');
                return res.json();
            })
            .then(clasesData => {
                console.log('✅ Clases cargadas:', clasesData.length);
                dispatch({ type: 'SET_CLASES', payload: Array.isArray(clasesData) ? clasesData : [] });
            })
            .catch(err => {
                console.error('❌ Error cargando clases:', err);
                dispatch({ type: 'SET_ERROR', payload: 'Error al cargar clases. Intente de nuevo.' });
            });

        // Cargar proveedores - API Resilient
        fetch('/proveedores/api/lista')
            .then(res => res.ok ? res.json() : [])
            .then(provData => {
                const validated = Array.isArray(provData) && provData.length > 0 ? provData : [];
                dispatch({ type: 'SET_PROVEEDORES', payload: validated });
            })
            .catch(err => {
                console.error('❌ Error cargando proveedores:', err);
                dispatch({ type: 'SET_PROVEEDORES', payload: [] });
            });

        // Cargar funcionarios - API Resilient
        fetch('/funcionarios/api/lista')
            .then(res => res.ok ? res.json() : [])
            .then(funcData => {
                const validated = Array.isArray(funcData) && funcData.length > 0 ? funcData : [];
                dispatch({ type: 'SET_FUNCIONARIOS', payload: validated });
            })
            .catch(err => {
                console.error('❌ Error cargando funcionarios:', err);
                dispatch({ type: 'SET_FUNCIONARIOS', payload: [] });
            });
    }, []);

    // ========================================================================
    // CARGAR ATRIBUTOS CUANDO CAMBIA LA CLASE (CON ABORTCONTROLLER)
    // ========================================================================
    useEffect(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        if (!data.clase_id) {
            dispatch({ type: 'SET_ATRIBUTOS', payload: [] });
            return;
        }

        abortControllerRef.current = new AbortController();
        const { signal } = abortControllerRef.current;

        dispatch({ type: 'SET_LOADING', payload: true });
        console.log('Fetching atributos para clase:', data.clase_id);

        fetch(`/activos/api/clase_atributos/${data.clase_id}`, { signal })
            .then(res => {
                if (!res.ok) throw new Error(`Error ${res.status}: No se pudo obtener los atributos.`);
                return res.json();
            })
            .then(attrs => {
                const validos = (Array.isArray(attrs) ? attrs : [])
                    .filter(a => a && a.name && a.label);
                console.log('Atributos válidos:', validos);
                dispatch({ type: 'SET_ATRIBUTOS', payload: validos });
            })
            .catch(err => {
                if (err.name === 'AbortError') {
                    console.log('Fetch de atributos abortado.');
                } else {
                    console.error('❌ Error cargando atributos:', err);
                    dispatch({ type: 'SET_ERROR', payload: 'Error al cargar atributos dinámicos.' });
                    dispatch({ type: 'SET_ATRIBUTOS', payload: [] });
                }
            });

        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [data.clase_id]);

    // ========================================================================
    // HANDLERS Y VALIDACIÓN
    // ========================================================================
    const handleChange = useCallback((e) => {
        const { name, value } = e.target;
        dispatch({ type: 'HANDLE_CHANGE', payload: { name, value } });
    }, []);

    const handleFileChange = useCallback((e) => {
        const { name, files } = e.target;
        dispatch({ type: 'HANDLE_FILE_CHANGE', payload: { name, file: files[0] } });
    }, []);

    const handleAtributoChange = useCallback((e) => {
        const { name, value, type, files } = e.target;
        const val = type === 'file' ? files[0] : value;
        dispatch({ type: 'HANDLE_ATRIBUTO_CHANGE', payload: { name, value: val } });
    }, []);

    const validateStep = useCallback((stepToValidate) => {
        const validator = validationRules[stepToValidate];
        if (!validator) return true;

        const errors = validator(data, atributos);

        if (Object.keys(errors).length > 0) {
            dispatch({ type: 'SET_VALIDATION_ERRORS', payload: errors });
            console.warn('❌ Falló la validación:', errors);
            return false;
        }

        dispatch({ type: 'SET_VALIDATION_ERRORS', payload: {} });
        return true;
    }, [data, atributos]);


    const nextStep = useCallback(() => {
        if (validateStep(step)) {
            dispatch({ type: 'NEXT_STEP' });
            window.scrollTo(0, 0);
        }
    }, [step, validateStep]);

    const prevStep = useCallback(() => {
        dispatch({ type: 'PREV_STEP' });
        window.scrollTo(0, 0);
    }, []);

    const handleSubmit = useCallback(async () => {
        dispatch({ type: 'SET_LOADING', payload: true });

        try {
            const formData = new FormData();
            Object.keys(data).forEach(key => {
                if (key === 'atributos_dinamicos') {
                    Object.keys(data.atributos_dinamicos ?? {}).forEach(attrKey => {
                        const value = (data.atributos_dinamicos ?? {})[attrKey];
                        if (value instanceof File) {
                            formData.append(attrKey, value, value.name);
                        } else if (value != null && value !== '') {
                            formData.append(attrKey, value);
                        }
                    });
                } else {
                    const val = data[key];
                    if (val == null) return;
                    if (val instanceof File) {
                        formData.append(key, val, val.name);
                    } else if (val !== '') {
                        formData.append(key, val);
                    }
                }
            });

            const url = mode === 'edit' && assetData ? `/activos/editar/${assetData.id}` : '/activos/nuevo';
            const response = await fetch(url, { method: 'POST', body: formData });

            if (response.ok) {
                dispatch({ type: 'SET_MESSAGE', payload: { type: 'success', text: 'Activo guardado exitosamente' } });
                setTimeout(() => { window.location.href = '/activos/'; }, 1500);
            } else {
                const errorData = await response.json().catch(() => ({ message: 'Error desconocido del servidor.' }));
                dispatch({ type: 'SET_MESSAGE', payload: { type: 'error', text: `Error: ${errorData.message}` } });
            }
        } catch (error) {
            console.error('❌ Error:', error);
            dispatch({ type: 'SET_MESSAGE', payload: { type: 'error', text: 'Error de conexión al guardar: ' + error.message } });
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [data, mode, assetData]);

    // ========================================================================
    // LÓGICA DE PASOS
    // ========================================================================
    const totalSteps = useMemo(() => {
        if (data.tipo_propiedad === 'Propio') return 5;
        if (data.tipo_propiedad === 'Ajeno') return 4;
        return 3;
    }, [data.tipo_propiedad]);

    // ========================================================================
    // RENDER
    // ========================================================================
    return (
        <div className="wizard-container">
            <div className="wizard-header">
                <h1>{mode === 'edit' ? 'Editar Activo' : 'Nuevo Activo'}</h1>
                <p>Paso {step} de {totalSteps}</p>
            </div>

            <div className="wizard-progress">
                <div className="wizard-progress-bar" style={{ width: `${(step / totalSteps) * 100}%` }} />
            </div>

            {message && <div className={`wizard-message ${message.type}`}>{message.text}</div>}
            {error && <div className="wizard-message error">{error}</div>}

            <div className="wizard-content">
                {step === 1 && <Step1 data={data} onChange={handleChange} errors={errors} />}
                {step === 2 && <Step2 data={data} onChange={handleChange} errors={errors} />}
                {step === 3 && data.tipo_propiedad === 'Propio' && (
                    <Step3Propio
                        data={data}
                        onChange={handleChange}
                        onFileChange={handleFileChange}
                        clases={clases}
                        proveedores={proveedores}
                        funcionarios={funcionarios}
                        errors={errors}
                    />
                )}
                {step === 3 && data.tipo_propiedad === 'Ajeno' && (
                    <Step3Ajeno data={data} onChange={handleChange} errors={errors} />
                )}
                {step === 4 && data.tipo_propiedad === 'Propio' && (
                    <Step4Atributos
                        data={data}
                        onChange={handleAtributoChange}
                        atributos={atributos}
                        loading={loading}
                        errors={errors}
                    />
                )}
                {step === totalSteps && (
                    <StepConfirm data={data} atributos={atributos} selectedEntitiesMap={selectedEntitiesMap} />
                )}
            </div>

            <div className="wizard-nav">
                {step > 1 && <button className="btn-secondary" onClick={prevStep} disabled={loading}>Anterior</button>}
                {step < totalSteps && <button className="btn-primary" onClick={nextStep} disabled={loading}>Siguiente</button>}
                {step === totalSteps && <button className="btn-primary" onClick={handleSubmit} disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>}
            </div>
        </div>
    );
};

// ============================================================================
// COMPONENTES DE PASOS
// ============================================================================

const Step1 = React.memo(({ data, onChange, errors }) => (
    <div className="step-content">
        <h2>Tipo de Activo</h2>
        <p className="step-subtitle">Selecciona el tipo de propiedad</p>
        <div className="type-selector">
            <div
                className={`type-card ${data.tipo_propiedad === 'Propio' ? 'selected' : ''}`}
                onClick={() => onChange({ target: { name: 'tipo_propiedad', value: 'Propio' } })}
            >
                <div className="type-icon">🏢</div>
                <h3>Activo Propio</h3>
                <p>Pertenece a la institución</p>
            </div>
            <div
                className={`type-card ${data.tipo_propiedad === 'Ajeno' ? 'selected' : ''}`}
                onClick={() => onChange({ target: { name: 'tipo_propiedad', value: 'Ajeno' } })}
            >
                <div className="type-icon">👤</div>
                <h3>Activo Ajeno</h3>
                <p>De terceros en custodia</p>
            </div>
        </div>
        {errors.tipo_propiedad && <span className="error-message-centered">{errors.tipo_propiedad[0]}</span>}
    </div>
));

const Step2 = React.memo(({ data, onChange, errors }) => (
    <div className="step-content">
        <h2>Información Básica</h2>
        <p className="step-subtitle">Datos esenciales del activo</p>
        <div className="form-grid">
            <Input label="Nombre del Activo" name="nombre_activo" value={data.nombre_activo} onChange={onChange} required error={errors.nombre_activo?.[0]} />
            <Input label="Placa / Código" name="placa_codigo_interno" value={data.placa_codigo_interno} onChange={onChange} required error={errors.placa_codigo_interno?.[0]} />
            <Input label="Marca" name="marca" value={data.marca} onChange={onChange} />
            <Input label="Modelo" name="modelo" value={data.modelo} onChange={onChange} />
            <Input label="Serie" name="serie" value={data.serie} onChange={onChange} />
            <Input label="Ubicación" name="ubicacion" value={data.ubicacion} onChange={onChange} />
            <Select
                label="Estado"
                name="estado"
                value={data.estado}
                onChange={onChange}
                options={[
                    { value: 'Operativo', label: 'Operativo' },
                    { value: 'En Mantenimiento', label: 'En Mantenimiento' },
                    { value: 'Dañado', label: 'Dañado' }
                ]}
            />
            <div className="full-width">
                <Textarea label="Observaciones" name="observaciones" value={data.observaciones} onChange={onChange} rows={3} />
            </div>
        </div>
    </div>
));

const Step3Propio = React.memo(({ data, onChange, onFileChange, clases, proveedores, funcionarios, errors }) => (
    <div className="step-content">
        <h2>Clasificación y Documentos</h2>
        <p className="step-subtitle">Información administrativa y documentación</p>
        {clases.length === 0 && <div className="alert alert-warning">Cargando clases disponibles...</div>}
        <div className="form-grid">
            <Select
                label="Clase de Activo"
                name="clase_id"
                value={data.clase_id}
                onChange={onChange}
                options={clases.map(c => ({ value: c.id, label: c.nombre_clase }))}
                required
                error={errors.clase_id?.[0]}
            />
            <SearchableSelect
                label="Proveedor"
                name="proveedor_id"
                value={data.proveedor_id}
                onChange={onChange}
                options={proveedores.map(p => ({ value: p.id, label: p.nombre }))}
                placeholder="Buscar proveedor..."
            />
            <Input
                label="Valor Comercial"
                name="valor_comercial"
                type="number"
                value={data.valor_comercial}
                onChange={onChange}
                step="0.01"
            />
            <Input
                label="Valor de Compra"
                name="valor_compra"
                type="number"
                value={data.valor_compra}
                onChange={onChange}
                step="0.01"
            />
            <Input
                label="Fecha de Compra"
                name="fecha_compra"
                type="date"
                value={data.fecha_compra}
                onChange={onChange}
            />
            <SearchableSelect
                label="Responsable (Funcionario)"
                name="funcionario_id"
                value={data.funcionario_id}
                onChange={onChange}
                options={funcionarios.map(f => ({ value: f.id, label: `${f.nombres} ${f.apellidos} - ${f.cedula}` }))}
                placeholder="Buscar funcionario por nombre o cédula..."
            />
            <FileInput
                label="Orden de Compra"
                name="orden_compra"
                onChange={onFileChange}
                accept=".pdf,.jpg,.jpeg,.png"
            />
            <FileInput
                label="Factura"
                name="factura"
                onChange={onFileChange}
                accept=".pdf,.jpg,.jpeg,.png"
            />
            <FileInput
                label="Documento Soporte"
                name="documento_soporte"
                onChange={onFileChange}
                accept=".pdf,.jpg,.jpeg,.png"
            />
        </div>
    </div>
));

const Step3Ajeno = React.memo(({ data, onChange, errors }) => (
    <div className="step-content">
        <h2>Información del Propietario</h2>
        <p className="step-subtitle">Datos del propietario del activo</p>
        <div className="form-grid">
            <Input
                label="Propietario"
                name="propietario_ajeno"
                value={data.propietario_ajeno}
                onChange={onChange}
                required
                error={errors.propietario_ajeno?.[0]}
            />
            <Select
                label="Condición de Tenencia"
                name="condicion_tenencia"
                value={data.condicion_tenencia}
                onChange={onChange}
                options={[
                    { value: 'Comodato', label: 'Comodato' },
                    { value: 'Arriendo', label: 'Arriendo' },
                    { value: 'Préstamo', label: 'Préstamo' }
                ]}
            />
        </div>
        <div className="form-grid" style={{ marginTop: '20px' }}>
            <div className="field full-width">
                 <label>
                    <input
                        type="checkbox"
                        name="es_ingreso_temporal"
                        checked={data.es_ingreso_temporal}
                        onChange={(e) => onChange({ target: { name: 'es_ingreso_temporal', value: e.target.checked } })}
                    />
                    <span style={{ marginLeft: '10px' }}>Es Ingreso Temporal</span>
                </label>
            </div>
            {data.es_ingreso_temporal && (
                <>
                    <Input
                        label="Fecha de Inicio Temporal"
                        name="fecha_inicio_temporal"
                        type="date"
                        value={data.fecha_inicio_temporal}
                        onChange={onChange}
                    />
                    <Input
                        label="Fecha de Fin Temporal"
                        name="fecha_fin_temporal"
                        type="date"
                        value={data.fecha_fin_temporal}
                        onChange={onChange}
                    />
                </>
            )}
        </div>
    </div>
));

const Step4Atributos = ({ data, onChange, atributos, loading, errors }) => {
    const atributosValidos = useMemo(() => Array.isArray(atributos) ? atributos : [], [atributos]);

    return (
        <div className="step-content">
            <h2>Atributos Especiales</h2>
            <p className="step-subtitle">Campos específicos de la clase</p>

            {loading && <div className="alert alert-info">⏳ Cargando atributos especiales...</div>}
            {!loading && atributosValidos.length === 0 && <div className="alert alert-info">Esta clase no tiene atributos especiales.</div>}

            {!loading && atributosValidos.length > 0 && (
                <div className="form-grid">
                    {atributosValidos.map((attr, idx) => {
                        const { name, label, type = 'text', options = [], required = false } = attr;
                        const value = (data.atributos_dinamicos ?? {})[name] ?? '';
                        const error = errors[name]?.[0];

                        if (type === 'select') {
                            return (
                                <Select
                                    key={idx}
                                    label={label}
                                    name={name}
                                    value={value}
                                    onChange={onChange}
                                    options={options.map(opt => ({ value: opt, label: opt }))}
                                    required={required}
                                    error={error}
                                />
                            );
                        } else if (type === 'textarea') {
                            return (
                                <div key={idx} className="full-width">
                                    <Textarea
                                        label={label}
                                        name={name}
                                        value={value}
                                        onChange={onChange}
                                        required={required}
                                        error={error}
                                    />
                                </div>
                            );
                        } else {
                            return (
                                <Input
                                    key={idx}
                                    label={label}
                                    name={name}
                                    type={type}
                                    value={type !== 'file' ? value : undefined}
                                    onChange={onChange}
                                    required={required}
                                    error={error}
                                />
                            );
                        }
                    })}
                </div>
            )}
        </div>
    );
};

const StepConfirm = ({ data, atributos, selectedEntitiesMap }) => {
    const { clase, proveedor, funcionario } = selectedEntitiesMap;

    const renderAtributoValor = (key, value) => {
        if (value instanceof File) {
            return `${value.name} (${(value.size / 1024).toFixed(2)} KB)`;
        }
        return value;
    };

    return (
        <div className="step-content">
            <h2>Confirmación</h2>
            <p className="step-subtitle">Revisa la información antes de guardar</p>

            <div className="confirm-section">
                <h3>Información Básica</h3>
                <div className="confirm-grid">
                    <div><strong>Nombre:</strong> {data.nombre_activo}</div>
                    <div><strong>Placa:</strong> {data.placa_codigo_interno}</div>
                    <div><strong>Tipo:</strong> {data.tipo_propiedad}</div>
                    <div><strong>Estado:</strong> {data.estado}</div>
                    {data.marca && <div><strong>Marca:</strong> {data.marca}</div>}
                    {data.modelo && <div><strong>Modelo:</strong> {data.modelo}</div>}
                    {data.serie && <div><strong>Serie:</strong> {data.serie}</div>}
                    {data.ubicacion && <div><strong>Ubicación:</strong> {data.ubicacion}</div>}
                </div>
            </div>

            {data.tipo_propiedad === 'Propio' && (
                <div className="confirm-section">
                    <h3>Clasificación y Documentos</h3>
                    <div className="confirm-grid">
                        {clase && <div><strong>Clase:</strong> {clase.nombre_clase}</div>}
                        {proveedor && <div><strong>Proveedor:</strong> {proveedor.nombre}</div>}
                        {funcionario && <div><strong>Responsable:</strong> {`${funcionario.nombres} ${funcionario.apellidos}`}</div>}
                        {data.valor_comercial && <div><strong>Valor Comercial:</strong> ${parseFloat(data.valor_comercial).toLocaleString()}</div>}
                        {data.valor_compra && <div><strong>Valor Compra:</strong> ${parseFloat(data.valor_compra).toLocaleString()}</div>}
                        {data.fecha_compra && <div><strong>Fecha Compra:</strong> {data.fecha_compra}</div>}
                        {data.orden_compra && <div><strong>Orden de Compra:</strong> {data.orden_compra.name}</div>}
                        {data.factura && <div><strong>Factura:</strong> {data.factura.name}</div>}
                        {data.documento_soporte && <div><strong>Documento Soporte:</strong> {data.documento_soporte.name}</div>}
                    </div>
                </div>
            )}

            {data.tipo_propiedad === 'Ajeno' && (
                <div className="confirm-section">
                    <h3>Propietario</h3>
                    <div className="confirm-grid">
                        <div><strong>Propietario:</strong> {data.propietario_ajeno}</div>
                        {data.condicion_tenencia && <div><strong>Condición:</strong> {data.condicion_tenencia}</div>}
                        {data.es_ingreso_temporal && (
                            <>
                                <div><strong>Ingreso Temporal:</strong> Sí</div>
                                <div><strong>Inicio:</strong> {data.fecha_inicio_temporal}</div>
                                <div><strong>Fin:</strong> {data.fecha_fin_temporal}</div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {Object.keys(data.atributos_dinamicos ?? {}).length > 0 && (
                <div className="confirm-section">
                    <h3>Atributos Especiales</h3>
                    <div className="confirm-grid">
                        {atributos.map(attr => {
                            const value = (data.atributos_dinamicos ?? {})[attr.name];
                            return value ? (
                                <div key={attr.name}>
                                    <strong>{attr.label}:</strong> {renderAtributoValor(attr.name, value)}
                                </div>
                            ) : null;
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};


// ============================================================================
// COMPONENTES REUTILIZABLES
// ============================================================================

const Input = React.memo(({ label, name, type = 'text', value, onChange, required, error, ...props }) => (
    <div className="field">
        <label>{label} {required && <span className="required">*</span>}</label>
        <input
            type={type}
            name={name}
            value={value || ''}
            onChange={onChange}
            required={required}
            {...props}
            className={error ? 'input-error' : ''}
        />
        {error && <span className="error-message">{error}</span>}
    </div>
));

const FileInput = React.memo(({ label, name, onChange, accept, required, error }) => (
    <div className="field">
        <label>{label} {required && <span className="required">*</span>}</label>
        <input
            type="file"
            name={name}
            onChange={onChange}
            accept={accept}
            required={required}
            className={error ? 'input-error' : ''}
        />
        {error && <span className="error-message">{error}</span>}
    </div>
));

const Select = React.memo(({ label, name, value, onChange, options, required, error }) => (
    <div className="field">
        <label>{label} {required && <span className="required">*</span>}</label>
        <select
            name={name}
            value={value || ''}
            onChange={onChange}
            required={required}
            className={error ? 'input-error' : ''}
        >
            <option value="">Seleccionar...</option>
            {options.map((opt, idx) => (
                <option key={idx} value={opt.value}>{opt.label}</option>
            ))}
        </select>
        {error && <span className="error-message">{error}</span>}
    </div>
));

const Textarea = React.memo(({ label, name, value, onChange, required, error, rows = 4 }) => (
    <div className="field">
        <label>{label} {required && <span className="required">*</span>}</label>
        <textarea
            name={name}
            value={value || ''}
            onChange={onChange}
            required={required}
            rows={rows}
            className={error ? 'input-error' : ''}
        />
        {error && <span className="error-message">{error}</span>}
    </div>
));

const SearchableSelect = React.memo(({ label, name, value, onChange, options, required, error, placeholder = 'Buscar...' }) => {
    const [q, setQ] = useState('');
    const [open, setOpen] = useState(false);
    const ref = useRef(null);

    const filtered = options.filter(o => o.label.toLowerCase().includes(q.toLowerCase()));
    const selected = options.find(o => o.value == value);

    useEffect(() => {
        const handleClick = (e) => {
            if (ref.current && !ref.current.contains(e.target)) setOpen(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    const handleSelect = (opt) => {
        onChange({ target: { name, value: opt.value } });
        setQ('');
        setOpen(false);
    };

    return (
        <div className="field" ref={ref}>
            <label>{label} {required && <span className="required">*</span>}</label>
            <div style={{ position: 'relative' }}>
                <input
                    type="text"
                    value={open ? q : (selected?.label || '')}
                    onChange={(e) => { setQ(e.target.value); setOpen(true); }}
                    onFocus={() => setOpen(true)}
                    placeholder={placeholder}
                    className={error ? 'input-error' : ''}
                />
                {open && filtered.length > 0 && (
                    <ul style={{
                        position: 'absolute', top: '100%', left: 0, right: 0, margin: 0, padding: 0,
                        listStyle: 'none', background: '#fff', border: '1px solid #ddd', borderRadius: '4px',
                        maxHeight: '200px', overflowY: 'auto', zIndex: 1000, boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                    }}>
                        {filtered.map((o, i) => (
                            <li
                                key={i}
                                onClick={() => handleSelect(o)}
                                style={{
                                    padding: '8px 12px', cursor: 'pointer', borderBottom: i < filtered.length - 1 ? '1px solid #eee' : 'none'
                                }}
                                onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                                onMouseLeave={(e) => e.target.style.background = '#fff'}
                            >
                                {o.label}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            {error && <span className="error-message">{error}</span>}
        </div>
    );
});

export default AssetWizard;
