import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY",)

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://cinthialopezku15_db_user:lopez1234@inventario.oc13kz1.mongodb.net/?appName=inventario"
).strip()

USE_FAKE_DB = False
db = None
users_col = None
products_col = None
categories_col = None
events_col = None  

try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
    client.admin.command("ping")
    db = client.get_default_database()
    print(" Conectado a MongoDB Atlas")
except Exception as e:
    print(" No se pudo conectar a MongoDB Atlas")
    print("Error:", e)
    print(" Usando base de datos en memoria")
    USE_FAKE_DB = True

if USE_FAKE_DB:
    import uuid

    class FakeCollection:
        def __init__(self):
            self.rows = []

        def find(self, *args, **kwargs):
            return list(self.rows)

        def find_one(self, query):
            for r in self.rows:
                match = True
                for k, v in query.items():
                    if str(r.get(k)) != str(v):
                        match = False
                        break
                if match:
                    return r
            return None

        def insert_one(self, doc):
            doc = dict(doc)
            if "_id" not in doc:
                doc["_id"] = str(uuid.uuid4())
            self.rows.append(doc)
            return type("R", (), {"inserted_id": doc["_id"]})()

        def delete_one(self, query):
            r = self.find_one(query)
            if r:
                self.rows.remove(r)

        def update_one(self, q, upd):
            r = self.find_one(q)
            if not r:
                return
            if "$set" in upd:
                for k, v in upd["$set"].items():
                    r[k] = v

        def update_many(self, q, upd):
            for r in list(self.rows):
                match = True
                for k, v in q.items():
                    if str(r.get(k)) != str(v):
                        match = False
                        break
                if match and "$set" in upd:
                    for k, v in upd["$set"].items():
                        r[k] = v

        def count_documents(self, q=None):
            if not q:
                return len(self.rows)
            c = 0
            for r in self.rows:
                match = True
                for k, v in q.items():
                    if isinstance(v, dict) and "$lte" in v:
                        if not (r.get(k, 0) <= v["$lte"]):
                            match = False
                            break
                    else:
                        if str(r.get(k)) != str(v):
                            match = False
                            break
                if match:
                    c += 1
            return c

    users_col = FakeCollection()
    products_col = FakeCollection()
    categories_col = FakeCollection()
    events_col = FakeCollection()  

    categories_col.insert_one({"_id": "cat1", "name": "Ropa"})
    categories_col.insert_one({"_id": "cat2", "name": "Calzado"})
    products_col.insert_one({"name": "Camisa", "quantity": 10, "price": 100, "category_id": "cat1"})
    products_col.insert_one({"name": "Tenis", "quantity": 4, "price": 500, "category_id": "cat2"})

else:
    users_col = db.users
    products_col = db.products
    categories_col = db.categories
    events_col = db.eventos  


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}


class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]
        self.role = user_doc.get("role", "user")


@login_manager.user_loader
def load_user(user_id):
    try:
        user_doc = users_col.find_one({"_id": ObjectId(user_id)})
    except:
        user_doc = users_col.find_one({"_id": user_id})
    if user_doc:
        return User(user_doc)
    return None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Acceso denegado", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return wrapper

def guardar_movimiento(accion, producto, cantidad):
    if current_user.is_authenticated:
        events_col.insert_one({
            "usuario": current_user.username,
            "accion": accion,
            "producto": producto,
            "cantidad": cantidad,
            "fecha": "2025-03-21"
        })


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form.get("role", "user")

        if users_col.find_one({"username": username}):
            flash("Usuario ya existe", "danger")
            return redirect(url_for("register"))

        users_col.insert_one({
            "username": username,
            "password": generate_password_hash(password),
            "role": role
        })

        flash("Usuario registrado", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_doc = users_col.find_one({"username": username})
        if user_doc and check_password_hash(user_doc["password"], password):
            login_user(User(user_doc))
            guardar_movimiento("INICIÓ SESIÓN", username, 0)  
            return redirect(url_for("dashboard"))

        flash("Datos incorrectos", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    guardar_movimiento("CERRÓ SESIÓN", current_user.username, 0)  
    logout_user()
    flash("Has cerrado sesión", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    total_products = products_col.count_documents({})
    low_stock = products_col.count_documents({"quantity": {"$lte": 5}})

    cats = list(categories_col.find())

    labels = [c.get("name", "Sin nombre") for c in cats]
    values = [products_col.count_documents({"category_id": str(c["_id"])}) for c in cats]
    
    
    movimientos = list(events_col.find())[:10] if events_col else []

    return render_template(
        "dashboard.html",
        total_products=total_products,
        low_stock=low_stock,
        labels=labels,
        values=values,
        movimientos=movimientos
    )


@app.route("/historial")
@login_required
def historial():
    movimientos = list(events_col.find())
    return render_template("historial.html", movimientos=movimientos)


@app.route("/categories")
@login_required
def categories():
    cats = list(categories_col.find())
    for c in cats:
        c["count"] = products_col.count_documents({"category_id": str(c["_id"])})
    return render_template("categories.html", categories=cats)


@app.route("/category/new", methods=["GET", "POST"])
@login_required
@admin_required
def category_new():
    if request.method == "POST":
        name = request.form["name"].strip()
        sub = request.form.get("subcategory", "").strip()

        categories_col.insert_one({"name": name, "subcategory": sub})
        flash("Categoría creada", "success")
        return redirect(url_for("categories"))

    return render_template("category_form.html", action="Crear")


@app.route("/category/edit/<id>", methods=["GET", "POST"])
@login_required
@admin_required
def category_edit(id):
    cat = categories_col.find_one({"_id": ObjectId(id)})
    if request.method == "POST":
        categories_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form["name"].strip(),
            "subcategory": request.form.get("subcategory", "").strip()
        }})
        flash("Categoría actualizada", "success")
        return redirect(url_for("categories"))

    return render_template("category_form.html", action="Editar", category=cat)


@app.route("/category/delete/<id>", methods=["POST"])
@login_required
@admin_required
def category_delete(id):
    categories_col.delete_one({"_id": ObjectId(id)})
    products_col.update_many({"category_id": str(id)}, {"$set": {"category_id": None}})
    flash("Categoría eliminada", "info")
    return redirect(url_for("categories"))


@app.route("/inventory")
@login_required
def inventory():
    products = list(products_col.find())
    for p in products:
        p["_id"] = str(p["_id"])
    categories = list(categories_col.find())
    return render_template("inventory.html", products=products, categories=categories)


@app.route("/product/new", methods=["GET", "POST"])
@login_required
def product_new():
    if request.method == "POST":
        image_filename = None
        if "image" in request.files:
            f = request.files["image"]
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                image_filename = filename

        products_col.insert_one({
            "name": request.form["name"].strip(),
            "quantity": int(request.form.get("quantity", 0)),
            "price": float(request.form.get("price", 0)),
            "description": request.form.get("description", "").strip(),
            "category_id": request.form.get("category_id") or None,
            "image": image_filename
        })
        
        guardar_movimiento("AGREGÓ PRODUCTO", request.form["name"], request.form.get("quantity", 0))  # NUEVA

        flash("Producto creado", "success")
        return redirect(url_for("inventory"))

    categories = list(categories_col.find())
    return render_template("product_form.html", action="Crear", categories=categories)


@app.route("/product/edit/<id>", methods=["GET", "POST"])
@login_required
def product_edit(id):
    prod = products_col.find_one({"_id": ObjectId(id)})
    if not prod:
        flash("Producto no encontrado", "danger")
        return redirect(url_for("inventory"))

    if request.method == "POST":
        image_filename = prod.get("image")
        if "image" in request.files:
            f = request.files["image"]
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                image_filename = filename

        products_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form["name"].strip(),
            "quantity": int(request.form.get("quantity", 0)),
            "price": float(request.form.get("price", 0)),
            "description": request.form.get("description", "").strip(),
            "category_id": request.form.get("category_id") or None,
            "image": image_filename
        }})
        
        guardar_movimiento("EDITÓ PRODUCTO", request.form["name"], request.form.get("quantity", 0))  # NUEVA

        flash("Producto actualizado", "success")
        return redirect(url_for("inventory"))

    prod["_id"] = str(prod["_id"])
    categories = list(categories_col.find())
    return render_template("product_form.html", action="Editar", product=prod, categories=categories)


@app.route("/product/delete/<id>", methods=["POST"])
@login_required
def product_delete(id):
    prod = products_col.find_one({"_id": ObjectId(id)})
    if prod:
        guardar_movimiento("ELIMINÓ PRODUCTO", prod.get("name"), prod.get("quantity", 0))
    products_col.delete_one({"_id": ObjectId(id)})
    flash("Producto eliminado", "info")
    return redirect(url_for("inventory"))


@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)