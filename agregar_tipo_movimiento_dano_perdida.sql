-- Script para agregar el tipo de movimiento "Reporte de Daño o Pérdida"
-- Base de datos: activos_fijos_v4.db (SQLite)
-- Fecha: 2025-01-26

-- Verificar si ya existe el tipo de movimiento
-- Si no existe, insertarlo

INSERT OR IGNORE INTO tipo_movimiento (nombre, descripcion, requiere_firmas)
VALUES (
    'Reporte de Daño o Pérdida',
    'Reporte formal de daño o pérdida de un activo fijo para gestión de acciones correctivas y preventivas',
    1
);

-- Verificar que se insertó correctamente
SELECT id, nombre, descripcion, requiere_firmas
FROM tipo_movimiento
WHERE nombre = 'Reporte de Daño o Pérdida';
