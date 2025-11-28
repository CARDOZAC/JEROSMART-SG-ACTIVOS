"""
Utilidad para convertir firmas SVG a elementos de ReportLab
y agregar metadata de auditoría a PDFs.
"""
from io import BytesIO
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


def svg_to_reportlab_drawing(svg_string, width=2*inch, height=1*inch):
    """
    Convierte un string SVG a un objeto Drawing de ReportLab.
    
    Args:
        svg_string: String con el contenido SVG
        width: Ancho deseado en unidades ReportLab
        height: Alto deseado en unidades ReportLab
    
    Returns:
        Drawing de ReportLab escalado
    """
    try:
        # Convertir string a BytesIO
        svg_file = BytesIO(svg_string.encode('utf-8'))
        
        # Convertir SVG a Drawing
        drawing = svg2rlg(svg_file)
        
        if not drawing:
            raise ValueError("No se pudo convertir el SVG")
        
        # Escalar al tamaño deseado manteniendo proporción
        scale_x = width / drawing.width
        scale_y = height / drawing.height
        scale = min(scale_x, scale_y)  # Mantener proporción
        
        drawing.width = drawing.width * scale
        drawing.height = drawing.height * scale
        drawing.scale(scale, scale)
        
        return drawing
        
    except Exception as e:
        print(f"Error al convertir SVG: {e}")
        return None


def crear_texto_auditoria(firma_obj):
    """
    Crea un texto de auditoría para mostrar debajo de la firma.
    
    Args:
        firma_obj: Objeto Firma con metadata
    
    Returns:
        String formateado con información de auditoría
    """
    timestamp = firma_obj.timestamp_firma.strftime('%Y-%m-%d %H:%M:%S') if firma_obj.timestamp_firma else 'N/A'
    ip = firma_obj.ip_address or 'N/A'
    hash_corto = firma_obj.hash_documento[:12] if firma_obj.hash_documento else 'N/A'
    
    return f"""
    <font size="7" color="#666666">
    <b>Firma Digital Verificable</b><br/>
    Fecha: {timestamp}<br/>
    IP: {ip}<br/>
    Hash: {hash_corto}...<br/>
    Consentimiento: {'✓ Aceptado' if firma_obj.consentimiento_aceptado else '✗ No aceptado'}
    </font>
    """


def crear_parrafo_auditoria(firma_obj):
    """
    Crea un Paragraph de ReportLab con información de auditoría.
    
    Args:
        firma_obj: Objeto Firma con metadata
    
    Returns:
        Paragraph de ReportLab
    """
    styles = getSampleStyleSheet()
    texto = crear_texto_auditoria(firma_obj)
    return Paragraph(texto, styles['Normal'])