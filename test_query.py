from app import create_app
from app.extensions import db
from app.models import Activo
from sqlalchemy import select

app = create_app()
with app.app_context():
    term = "BIO"
    search_term = f'%{term}%'
    stmt = select(Activo.id, Activo.nombre_activo, Activo.placa_codigo_interno).where(
        (Activo.nombre_activo.ilike(search_term)) |
        (Activo.placa_codigo_interno.ilike(search_term))
    )
    results = db.session.execute(stmt).all()
    print(f"Results for {term}: {results}")
