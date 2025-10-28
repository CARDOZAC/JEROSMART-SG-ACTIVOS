from app.extensions import db

class Activo(db.Model):
    __tablename__ = "activos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    categoria = db.Column(db.String(100))
    estado = db.Column(db.String(50))
    valor = db.Column(db.Float)
    fecha_adquisicion = db.Column(db.Date)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))

    def __repr__(self):
        return f"<Activo {self.nombre}>"
