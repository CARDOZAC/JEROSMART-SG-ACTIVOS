// =====================================================================
// WIZARD DE IMPORTACIÓN CSV - CON PREVIEW Y VALIDACIÓN
// =====================================================================

const { useState, useEffect, useCallback, useMemo } = React;

/**
 * Wizard para importar activos desde CSV con preview y validación
 */
const CSVImportWizard = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [file, setFile] = useState(null);
    const [csvData, setCsvData] = useState([]);
    const [headers, setHeaders] = useState([]);
    const [columnMapping, setColumnMapping] = useState({});
    const [validationErrors, setValidationErrors] = useState([]);
    const [importing, setImporting] = useState(false);
    const [importResults, setImportResults] = useState(null);
    const [alert, setAlert] = useState(null);

    // Campos esperados en el CSV
    const expectedFields = [
        { key: 'nombre_activo', label: 'Nombre del Activo', required: true },
        { key: 'placa_codigo_interno', label: 'Placa/Código', required: true },
        { key: 'clase_id', label: 'ID de Clase', required: true },
        { key: 'marca', label: 'Marca', required: false },
        { key: 'modelo', label: 'Modelo', required: false },
        { key: 'serie', label: 'Serie', required: false },
        { key: 'ubicacion', label: 'Ubicación', required: false },
        { key: 'estado', label: 'Estado', required: false },
        { key: 'funcionario_id', label: 'ID Funcionario', required: false },
        { key: 'valor_comercial', label: 'Valor Comercial', required: false }
    ];

    const steps = [
        { label: 'Subir Archivo', icon: 'bi-cloud-upload' },
        { label: 'Mapear Columnas', icon: 'bi-table' },
        { label: 'Validar Datos', icon: 'bi-check-circle' },
        { label: 'Importar', icon: 'bi-download' }
    ];

    // Mostrar alerta
    const showAlert = useCallback((type, message) => {
        setAlert({ type, message });
        setTimeout(() => setAlert(null), 5000);
    }, []);

    // Parsear CSV
    const parseCSV = (text) => {
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length === 0) return { headers: [], data: [] };

        const headers = lines[0].split(',').map(h => h.trim());
        const data = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index] || '';
            });
            return row;
        });

        return { headers, data };
    };

    // Manejar carga de archivo
    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (!selectedFile) return;

        if (!selectedFile.name.endsWith('.csv')) {
            showAlert('error', 'Por favor selecciona un archivo CSV válido');
            return;
        }

        setFile(selectedFile);

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const text = event.target.result;
                const { headers: parsedHeaders, data: parsedData } = parseCSV(text);

                setHeaders(parsedHeaders);
                setCsvData(parsedData);

                // Auto-mapeo inteligente
                const autoMapping = {};
                expectedFields.forEach(field => {
                    const matchedHeader = parsedHeaders.find(h =>
                        h.toLowerCase().includes(field.key.toLowerCase()) ||
                        field.label.toLowerCase().includes(h.toLowerCase())
                    );
                    if (matchedHeader) {
                        autoMapping[field.key] = matchedHeader;
                    }
                });
                setColumnMapping(autoMapping);

                showAlert('success', `Archivo cargado: ${parsedData.length} registros encontrados`);
            } catch (error) {
                showAlert('error', 'Error al leer el archivo CSV');
                console.error(error);
            }
        };

        reader.readAsText(selectedFile);
    };

    // Validar datos
    const validateData = useCallback(() => {
        const errors = [];

        csvData.forEach((row, index) => {
            const rowErrors = [];

            // Validar campos requeridos
            expectedFields.forEach(field => {
                if (field.required) {
                    const mappedColumn = columnMapping[field.key];
                    if (!mappedColumn || !row[mappedColumn]) {
                        rowErrors.push(`Falta el campo requerido: ${field.label}`);
                    }
                }
            });

            if (rowErrors.length > 0) {
                errors.push({
                    row: index + 1,
                    errors: rowErrors,
                    data: row
                });
            }
        });

        setValidationErrors(errors);
        return errors.length === 0;
    }, [csvData, columnMapping, expectedFields]);

    // Importar datos
    const handleImport = async () => {
        setImporting(true);

        try {
            // Transformar datos según el mapeo
            const transformedData = csvData.map(row => {
                const transformed = {};
                Object.keys(columnMapping).forEach(fieldKey => {
                    const csvColumn = columnMapping[fieldKey];
                    transformed[fieldKey] = row[csvColumn] || '';
                });
                return transformed;
            });

            const formData = new FormData();
            formData.append('data', JSON.stringify(transformedData));

            const response = await fetch('/activos/api/import-csv', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                setImportResults(result);
                showAlert('success', `Importación exitosa: ${result.success_count} activos importados`);
                setCurrentStep(4);
            } else {
                showAlert('error', result.message || 'Error en la importación');
            }
        } catch (error) {
            showAlert('error', 'Error de conexión al servidor');
            console.error(error);
        } finally {
            setImporting(false);
        }
    };

    // Navegación
    const nextStep = () => {
        if (currentStep === 2) {
            // Validar mapeo antes de continuar
            const missingRequired = expectedFields
                .filter(f => f.required && !columnMapping[f.key])
                .map(f => f.label);

            if (missingRequired.length > 0) {
                showAlert('error', `Faltan campos requeridos: ${missingRequired.join(', ')}`);
                return;
            }
        }

        if (currentStep === 3) {
            if (!validateData()) {
                showAlert('error', 'Hay errores de validación. Por favor corrígelos antes de continuar.');
                return;
            }
        }

        setCurrentStep(prev => Math.min(prev + 1, steps.length));
    };

    const prevStep = () => {
        setCurrentStep(prev => Math.max(prev - 1, 1));
    };

    // Renderizado de pasos
    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return (
                    <div className="wizard-step-content fade-in">
                        <h2 className="wizard-step-title">
                            <i className="bi bi-cloud-upload me-3"></i>
                            Subir Archivo CSV
                        </h2>
                        <p className="wizard-step-subtitle">
                            Selecciona el archivo CSV con los activos a importar
                        </p>

                        <div className="csv-upload-area">
                            <div className="csv-upload-dropzone">
                                <i className="bi bi-file-earmark-spreadsheet csv-upload-icon"></i>
                                <h3>Arrastra tu archivo aquí</h3>
                                <p>o haz clic para seleccionar</p>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={handleFileChange}
                                    className="csv-file-input"
                                    id="csv-file"
                                />
                                <label htmlFor="csv-file" className="csv-upload-button">
                                    Seleccionar archivo CSV
                                </label>
                            </div>

                            {file && (
                                <div className="csv-file-info">
                                    <i className="bi bi-file-check-fill me-2"></i>
                                    <strong>{file.name}</strong>
                                    <span className="ms-2">({(file.size / 1024).toFixed(2)} KB)</span>
                                </div>
                            )}
                        </div>

                        <div className="csv-format-help">
                            <h4><i className="bi bi-info-circle me-2"></i>Formato esperado</h4>
                            <p>El archivo CSV debe contener las siguientes columnas:</p>
                            <ul>
                                {expectedFields.map((field, idx) => (
                                    <li key={idx}>
                                        <strong>{field.label}</strong>
                                        {field.required && <span className="text-danger"> (requerido)</span>}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                );

            case 2:
                return (
                    <div className="wizard-step-content fade-in">
                        <h2 className="wizard-step-title">
                            <i className="bi bi-table me-3"></i>
                            Mapear Columnas
                        </h2>
                        <p className="wizard-step-subtitle">
                            Relaciona las columnas del CSV con los campos del sistema
                        </p>

                        <div className="column-mapping-container">
                            {expectedFields.map((field, idx) => (
                                <div key={idx} className="column-mapping-row">
                                    <div className="field-info">
                                        <strong>{field.label}</strong>
                                        {field.required && <span className="required-badge">Requerido</span>}
                                    </div>
                                    <i className="bi bi-arrow-right mapping-arrow"></i>
                                    <select
                                        className="mapping-select"
                                        value={columnMapping[field.key] || ''}
                                        onChange={(e) => setColumnMapping({
                                            ...columnMapping,
                                            [field.key]: e.target.value
                                        })}
                                    >
                                        <option value="">-- Seleccionar columna --</option>
                                        {headers.map((header, headerIdx) => (
                                            <option key={headerIdx} value={header}>
                                                {header}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case 3:
                return (
                    <div className="wizard-step-content fade-in">
                        <h2 className="wizard-step-title">
                            <i className="bi bi-check-circle me-3"></i>
                            Validar Datos
                        </h2>
                        <p className="wizard-step-subtitle">
                            Revisa los datos antes de importar
                        </p>

                        <div className="validation-summary">
                            <div className="validation-stat">
                                <i className="bi bi-file-earmark-text"></i>
                                <div>
                                    <strong>{csvData.length}</strong>
                                    <span>Registros totales</span>
                                </div>
                            </div>
                            <div className="validation-stat">
                                <i className="bi bi-check-circle-fill text-success"></i>
                                <div>
                                    <strong>{csvData.length - validationErrors.length}</strong>
                                    <span>Registros válidos</span>
                                </div>
                            </div>
                            <div className="validation-stat">
                                <i className="bi bi-exclamation-triangle-fill text-danger"></i>
                                <div>
                                    <strong>{validationErrors.length}</strong>
                                    <span>Errores encontrados</span>
                                </div>
                            </div>
                        </div>

                        {validationErrors.length > 0 && (
                            <div className="validation-errors">
                                <h4>Errores de Validación</h4>
                                {validationErrors.slice(0, 10).map((error, idx) => (
                                    <div key={idx} className="validation-error-item">
                                        <strong>Fila {error.row}:</strong>
                                        <ul>
                                            {error.errors.map((err, errIdx) => (
                                                <li key={errIdx}>{err}</li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                                {validationErrors.length > 10 && (
                                    <p className="text-muted">
                                        ... y {validationErrors.length - 10} errores más
                                    </p>
                                )}
                            </div>
                        )}

                        <div className="data-preview">
                            <h4>Vista Previa</h4>
                            <div className="table-responsive">
                                <table className="preview-table">
                                    <thead>
                                        <tr>
                                            {Object.keys(columnMapping).map((key, idx) => (
                                                <th key={idx}>
                                                    {expectedFields.find(f => f.key === key)?.label}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {csvData.slice(0, 5).map((row, rowIdx) => (
                                            <tr key={rowIdx}>
                                                {Object.keys(columnMapping).map((key, colIdx) => (
                                                    <td key={colIdx}>
                                                        {row[columnMapping[key]] || '-'}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            {csvData.length > 5 && (
                                <p className="text-muted text-center mt-2">
                                    Mostrando 5 de {csvData.length} registros
                                </p>
                            )}
                        </div>
                    </div>
                );

            case 4:
                return (
                    <div className="wizard-step-content fade-in">
                        <h2 className="wizard-step-title">
                            <i className="bi bi-download me-3"></i>
                            Importación Completada
                        </h2>

                        {importResults ? (
                            <div className="import-results">
                                <div className="success-animation">
                                    <i className="bi bi-check-circle-fill"></i>
                                </div>
                                <h3>¡Importación exitosa!</h3>
                                <div className="import-stats">
                                    <div className="import-stat-item">
                                        <strong>{importResults.success_count}</strong>
                                        <span>Activos importados</span>
                                    </div>
                                    {importResults.error_count > 0 && (
                                        <div className="import-stat-item error">
                                            <strong>{importResults.error_count}</strong>
                                            <span>Errores</span>
                                        </div>
                                    )}
                                </div>

                                <div className="import-actions">
                                    <a href="/activos/" className="wizard-btn wizard-btn-primary">
                                        <i className="bi bi-box-seam me-2"></i>
                                        Ver Activos
                                    </a>
                                    <button
                                        className="wizard-btn wizard-btn-secondary"
                                        onClick={() => {
                                            setCurrentStep(1);
                                            setFile(null);
                                            setCsvData([]);
                                            setImportResults(null);
                                        }}
                                    >
                                        <i className="bi bi-arrow-repeat me-2"></i>
                                        Importar Más
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center">
                                <button
                                    className="wizard-btn wizard-btn-success"
                                    onClick={handleImport}
                                    disabled={importing}
                                >
                                    {importing ? (
                                        <>
                                            <span className="spinner-border spinner-border-sm me-2"></span>
                                            Importando...
                                        </>
                                    ) : (
                                        <>
                                            <i className="bi bi-download me-2"></i>
                                            Iniciar Importación
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="wizard-container csv-wizard">
            {alert && (
                <div className={`custom-alert alert-${alert.type} slide-in`}>
                    <i className={`bi ${alert.type === 'success' ? 'bi-check-circle-fill' : 'bi-x-circle-fill'} me-2`}></i>
                    <span>{alert.message}</span>
                    <button className="alert-close" onClick={() => setAlert(null)}>
                        <i className="bi bi-x-lg"></i>
                    </button>
                </div>
            )}

            <div className="wizard-card">
                <div className="wizard-header">
                    <h1 className="wizard-title">Importar Activos desde CSV</h1>
                    <div className="wizard-progress-container">
                        <div className="wizard-progress-bar">
                            <div
                                className="wizard-progress-fill"
                                style={{ width: `${(currentStep / steps.length) * 100}%` }}
                            >
                                <div className="progress-glow"></div>
                            </div>
                        </div>
                        <div className="wizard-progress-text">
                            Paso {currentStep} de {steps.length}
                        </div>
                    </div>
                </div>

                <div className="step-indicator-container">
                    {steps.map((step, index) => {
                        const stepNumber = index + 1;
                        const isActive = stepNumber === currentStep;
                        const isCompleted = stepNumber < currentStep;

                        return (
                            <div
                                key={index}
                                className={`step-indicator-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                            >
                                <div className="step-indicator-circle">
                                    {isCompleted ? (
                                        <i className="bi bi-check-lg"></i>
                                    ) : (
                                        <span>{stepNumber}</span>
                                    )}
                                </div>
                                <div className="step-indicator-label">{step.label}</div>
                                {index < steps.length - 1 && <div className="step-indicator-line"></div>}
                            </div>
                        );
                    })}
                </div>

                <div className="wizard-body">
                    {renderStep()}
                </div>

                <div className="wizard-footer">
                    {currentStep > 1 && currentStep < 4 && (
                        <button
                            className="wizard-btn wizard-btn-secondary"
                            onClick={prevStep}
                            disabled={importing}
                        >
                            <i className="bi bi-arrow-left me-2"></i>
                            Anterior
                        </button>
                    )}

                    {currentStep < 3 && csvData.length > 0 && (
                        <button
                            className="wizard-btn wizard-btn-primary"
                            onClick={nextStep}
                        >
                            Siguiente
                            <i className="bi bi-arrow-right ms-2"></i>
                        </button>
                    )}

                    {currentStep === 3 && validationErrors.length === 0 && (
                        <button
                            className="wizard-btn wizard-btn-success"
                            onClick={nextStep}
                        >
                            Continuar a Importación
                            <i className="bi bi-arrow-right ms-2"></i>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

// Exportar componente
window.CSVImportWizard = CSVImportWizard;
