# Flask Inventory App (Updated)

Instrucciones rápidas:

1. Copia `.env.example` a `.env` y completa `MONGO_URI` y `SECRET_KEY`.
2. Crea un virtualenv e instala dependencias:

```bash
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```

3. Ejecuta la app:

```bash
python app.py
```

4. Abre http://127.0.0.1:5000

Notas:
- Las rutas para administrar categorías requieren rol `admin`.
- Las imágenes subidas se guardan en `static/uploads`.
