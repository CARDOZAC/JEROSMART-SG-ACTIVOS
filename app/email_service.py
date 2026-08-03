"""
Servicio de notificaciones por email para el sistema de movimientos.

Soporta:
- Notificaciones de aprobación pendiente
- Alertas de movimientos de alto valor
- Recordatorios de vencimiento
- Resumen diario de actividades
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app, render_template_string
from datetime import datetime, timedelta
from threading import Thread


# ======================================================================
# TEMPLATES DE EMAIL (HTML)
# ======================================================================

TEMPLATE_APROBACION_PENDIENTE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #0066cc; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f9f9f9; padding: 20px; margin: 20px 0; }
        .info-box { background-color: #fff; border-left: 4px solid #0066cc; padding: 15px; margin: 15px 0; }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #0066cc;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 15px 0;
        }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        .alert { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Movimiento Requiere Aprobación</h1>
        </div>

        <div class="content">
            <p>Hola <strong>{{ supervisor_nombre }}</strong>,</p>

            <p>Se ha creado un nuevo movimiento que requiere tu aprobación:</p>

            <div class="info-box">
                <strong>Tipo de Movimiento:</strong> {{ tipo_movimiento }}<br>
                <strong>ID:</strong> #{{ movimiento_id }}<br>
                <strong>Creado por:</strong> {{ usuario_nombre }}<br>
                <strong>Fecha:</strong> {{ fecha }}<br>
                <strong>Activos involucrados:</strong> {{ num_activos }}
            </div>

            {% if valor_total %}
            <div class="alert">
                <strong>⚠️ Valor Total:</strong> ${{ "{:,.0f}".format(valor_total) }} COP<br>
                <small>Este movimiento supera el umbral de $5,000,000 COP</small>
            </div>
            {% endif %}

            {% if observaciones %}
            <div class="info-box">
                <strong>Observaciones:</strong><br>
                {{ observaciones }}
            </div>
            {% endif %}

            <center>
                <a href="{{ url_aprobacion }}" class="button">Ver Detalles y Aprobar</a>
            </center>
        </div>

        <div class="footer">
            <p>Este es un correo automático de <strong>JeroSmart Activos</strong></p>
            <p>No responder a este correo</p>
        </div>
    </div>
</body>
</html>
"""

TEMPLATE_MOVIMIENTO_APROBADO = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f9f9f9; padding: 20px; margin: 20px 0; }
        .success-box { background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Movimiento Aprobado</h1>
        </div>

        <div class="content">
            <p>Hola <strong>{{ usuario_nombre }}</strong>,</p>

            <div class="success-box">
                Tu movimiento <strong>#{{ movimiento_id }}</strong> ({{ tipo_movimiento }}) ha sido <strong>aprobado</strong>.
            </div>

            <p><strong>Aprobado por:</strong> {{ aprobador_nombre }}<br>
            <strong>Fecha de aprobación:</strong> {{ fecha_aprobacion }}</p>

            <p>El movimiento está ahora completado y puedes generar el PDF del acta.</p>
        </div>

        <div class="footer">
            <p>JeroSmart Activos - Sistema de Gestión de Activos Fijos</p>
        </div>
    </div>
</body>
</html>
"""

TEMPLATE_MOVIMIENTO_RECHAZADO = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f9f9f9; padding: 20px; margin: 20px 0; }
        .error-box { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Movimiento Rechazado</h1>
        </div>

        <div class="content">
            <p>Hola <strong>{{ usuario_nombre }}</strong>,</p>

            <div class="error-box">
                Tu movimiento <strong>#{{ movimiento_id }}</strong> ({{ tipo_movimiento }}) ha sido <strong>rechazado</strong>.
            </div>

            <p><strong>Rechazado por:</strong> {{ aprobador_nombre }}<br>
            <strong>Fecha de rechazo:</strong> {{ fecha_rechazo }}</p>

            {% if motivo %}
            <p><strong>Motivo:</strong><br>{{ motivo }}</p>
            {% endif %}

            <p>Por favor, revisa el movimiento y corrígelo antes de volver a enviarlo.</p>
        </div>

        <div class="footer">
            <p>JeroSmart Activos - Sistema de Gestión de Activos Fijos</p>
        </div>
    </div>
</body>
</html>
"""


# ======================================================================
# FUNCIONES DE ENVÍO
# ======================================================================

def enviar_email_async(app, msg_dict):
    """
    Envía un email de forma asíncrona en un thread separado.
    Esto evita bloquear la aplicación mientras se envía el correo.
    """
    with app.app_context():
        try:
            # Configuración SMTP desde config
            smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            smtp_user = current_app.config.get('MAIL_USERNAME')
            smtp_password = current_app.config.get('MAIL_PASSWORD')
            use_tls = current_app.config.get('MAIL_USE_TLS', True)

            if not smtp_user or not smtp_password:
                current_app.logger.warning("Email no configurado (MAIL_USERNAME/MAIL_PASSWORD faltantes)")
                return

            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = smtp_user
            msg['To'] = msg_dict['to']
            msg['Subject'] = msg_dict['subject']

            # Adjuntar HTML
            html_part = MIMEText(msg_dict['html'], 'html', 'utf-8')
            msg.attach(html_part)

            # Adjuntar PDF si existe
            if msg_dict.get('pdf'):
                pdf_part = MIMEApplication(msg_dict['pdf'], _subtype='pdf')
                pdf_part.add_header('Content-Disposition', 'attachment', filename=msg_dict.get('pdf_filename', 'documento.pdf'))
                msg.attach(pdf_part)

            # Enviar
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            current_app.logger.info(f"Email enviado a {msg_dict['to']}: {msg_dict['subject']}")

        except Exception as e:
            current_app.logger.error(f"Error enviando email: {e}", exc_info=True)


def enviar_email(to, subject, html, pdf=None, pdf_filename=None):
    """
    Envía un email de forma asíncrona.

    Args:
        to: Email del destinatario
        subject: Asunto del correo
        html: Contenido HTML del correo
        pdf: Bytes del PDF adjunto (opcional)
        pdf_filename: Nombre del archivo PDF (opcional)
    """
    msg_dict = {
        'to': to,
        'subject': subject,
        'html': html,
        'pdf': pdf,
        'pdf_filename': pdf_filename
    }

    # Obtener app fuera del contexto para el thread
    app = current_app._get_current_object()

    # Enviar en thread separado
    thread = Thread(target=enviar_email_async, args=(app, msg_dict))
    thread.daemon = True
    thread.start()


# ======================================================================
# NOTIFICACIONES ESPECÍFICAS
# ======================================================================

def notificar_aprobacion_pendiente(movimiento, supervisor_email, url_base):
    """
    Notifica a un supervisor que tiene un movimiento pendiente de aprobar.

    Args:
        movimiento: Objeto Movimiento
        supervisor_email: Email del supervisor
        url_base: URL base de la aplicación (ej: https://miapp.com)
    """
    from app.models import User

    # Obtener nombre del supervisor
    supervisor = User.query.filter_by(email=supervisor_email).first()
    supervisor_nombre = supervisor.email.split('@')[0].title() if supervisor else "Supervisor"

    # Calcular valor total
    valor_total = sum(ma.valor_libros_momento for ma in movimiento.activos) if movimiento.activos else 0

    # Renderizar template
    html = render_template_string(
        TEMPLATE_APROBACION_PENDIENTE,
        supervisor_nombre=supervisor_nombre,
        tipo_movimiento=movimiento.tipo_movimiento,
        movimiento_id=movimiento.id,
        usuario_nombre=movimiento.usuario.email if movimiento.usuario else 'Desconocido',
        fecha=movimiento.fecha.strftime('%d/%m/%Y %H:%M'),
        num_activos=len(movimiento.activos),
        valor_total=valor_total if valor_total > 0 else None,
        observaciones=movimiento.observaciones_generales,
        url_aprobacion=f"{url_base}/movimientos/{movimiento.id}"
    )

    enviar_email(
        to=supervisor_email,
        subject=f"⚠️ Movimiento #{movimiento.id} requiere tu aprobación",
        html=html
    )


def notificar_movimiento_aprobado(movimiento, url_base):
    """Notifica al creador que su movimiento fue aprobado."""
    if not movimiento.usuario or not movimiento.usuario.email:
        return

    html = render_template_string(
        TEMPLATE_MOVIMIENTO_APROBADO,
        usuario_nombre=movimiento.usuario.email.split('@')[0].title(),
        movimiento_id=movimiento.id,
        tipo_movimiento=movimiento.tipo_movimiento,
        aprobador_nombre=movimiento.aprobador.email if movimiento.aprobador else 'Sistema',
        fecha_aprobacion=movimiento.fecha_aprobacion.strftime('%d/%m/%Y %H:%M') if movimiento.fecha_aprobacion else 'N/A'
    )

    enviar_email(
        to=movimiento.usuario.email,
        subject=f"✅ Movimiento #{movimiento.id} aprobado",
        html=html
    )


def notificar_movimiento_rechazado(movimiento, url_base):
    """Notifica al creador que su movimiento fue rechazado."""
    if not movimiento.usuario or not movimiento.usuario.email:
        return

    html = render_template_string(
        TEMPLATE_MOVIMIENTO_RECHAZADO,
        usuario_nombre=movimiento.usuario.email.split('@')[0].title(),
        movimiento_id=movimiento.id,
        tipo_movimiento=movimiento.tipo_movimiento,
        aprobador_nombre=movimiento.aprobador.email if movimiento.aprobador else 'Sistema',
        fecha_rechazo=datetime.now().strftime('%d/%m/%Y %H:%M'),
        motivo=movimiento.motivo_rechazo
    )

    enviar_email(
        to=movimiento.usuario.email,
        subject=f"❌ Movimiento #{movimiento.id} rechazado",
        html=html
    )


def obtener_email_supervisor():
    """
    Obtiene el email del supervisor para notificaciones.

    Returns:
        str: Email del supervisor o None si no hay configurado
    """
    from app.models import User

    # Buscar un usuario con rol Supervisor o Admin
    supervisor = User.query.filter(User.rol.in_(['Supervisor', 'Admin'])).first()

    if supervisor:
        return supervisor.email

    # Fallback: email desde configuración
    return current_app.config.get('SUPERVISOR_EMAIL')
