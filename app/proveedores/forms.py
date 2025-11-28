from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ProveedorForm(FlaskForm):
    """
    Formulario para la creación y edición de proveedores.
    Los campos están diseñados para ser intuitivos y claros, 
    siguiendo una estética minimalista y funcional similar a la de iOS.
    """
    nit = StringField(
        'NIT', 
        validators=[
            DataRequired(message="El NIT es obligatorio."),
            Length(min=5, max=20, message="El NIT debe tener entre 5 y 20 caracteres.")
        ],
        render_kw={"placeholder": "Escriba el NIT del proveedor"}
    )
    razon_social = StringField(
        'Razón Social', 
        validators=[
            DataRequired(message="La razón social es obligatoria."),
            Length(min=3, max=120, message="La razón social debe tener entre 3 y 120 caracteres.")
        ],
        render_kw={"placeholder": "Nombre o razón social"}
    )
    direccion = StringField(
        'Dirección', 
        validators=[
            DataRequired(message="La dirección es obligatoria."),
            Length(min=5, max=120, message="La dirección debe tener entre 5 y 120 caracteres.")
        ],
        render_kw={"placeholder": "Dirección de la sede principal"}
    )
    numero_contacto = StringField(
        'Teléfono de Contacto',
        validators=[
            Optional(),
            Length(max=20, message="El teléfono no debe exceder los 20 caracteres.")
        ],
        render_kw={"placeholder": "Número de teléfono (opcional)"}
    )
    persona_contacto = StringField(
        'Nombre del Contacto',
        validators=[
            Optional(),
            Length(max=120, message="El nombre del contacto no debe exceder los 120 caracteres.")
        ],
        render_kw={"placeholder": "Persona de contacto (opcional)"}
    )
    submit = SubmitField(
        'Guardar Proveedor',
        render_kw={"class": "btn btn-primary btn-block"}
    )