## install flask
import mysql.connector.errorcode
from flask import Flask, request, jsonify, render_template, redirect, url_for
## install flask cors
from flask_cors import CORS
## Werkzeug
from werkzeug.utils import secure_filename
####
import os
import time
#### sql connector
import mysql.connector
print("MySQL Connector Python is installed and imported successfully.")
###
app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'static/imagenes'

class Inventario:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            ##database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)
        #
        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS libros (  
            isbn INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            image VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            year INT)''')
        self.conn.commit()

        ## cerrar cursor inicial y abrir uno nuevo con el parámetro diccionario en true
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    ### listar libros
    def listar_libros(self):
        self.cursor.execute("SELECT * FROM libros")
        libros = self.cursor.fetchall()
        return libros

    #### consultar libro
    def consultar_libro(self, isbn):  ## buscamos por isbn
        self.cursor.execute(f"SELECT * FROM libros WHERE isbn = {isbn}")
        return self.cursor.fetchone()

    ## mostrar por print a cada parámetro
    def mostrar_libro(self, isbn):
        libro = self.consultar_libro(isbn)
        if libro:
            print("-" * 40)
            print(f"ISBN: {libro['isbn']}")
            print(f"Título: {libro['title']}")
            print(f"Cantidad: {libro['quantity']}")
            print(f"Precio: {libro['price']}")
            print(f"Imagen: {libro['image']}")
            print(f"Autor: {libro['author']}")
            print(f"Año: {libro['year']}")
            print("-" * 40)
        else:
            print("Producto no encontrado")

    ### agregar libro
    def agregar_libro(self, title, quantity, price, image, author, year):
        sql = "INSERT INTO libros (title, quantity, price, image, author, year) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (title, quantity, price, image, author, year)

        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.lastrowid

    def modificar_libro(self, isbn, new_title, new_quantity, new_price, new_image, new_author, new_year):
        sql = "UPDATE libros SET title = %s, quantity = %s, price = %s, image = %s, author = %s, year = %s WHERE isbn = %s"
        valores = (new_title, new_quantity, new_price, new_image, new_author, new_year, isbn)

        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    # eliminar libro
    def eliminar_libro(self, isbn):
        self.cursor.execute(f"DELETE FROM libros WHERE isbn = {isbn}")
        self.conn.commit()
        return self.cursor.rowcount > 0

# --------------------------------------------------------------------
# Cuerpo del programa
# --------------------------------------------------------------------
# Crear una instancia de la clase Inventario
inventario = Inventario(host='localhost', user='root', password='', database='inventario')
##inventario = Inventario(host='antoniocaminos.mysql.pythonanywhere-services.com', user='antoniocaminos', password='Contra53a24', database='antoniocaminos$default')

ruta_destino = "./static/imagenes/"

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/libros", methods=["GET"])
def listar_libros():
    libros = inventario.listar_libros()
    return jsonify(libros)

@app.route("/libros/<int:isbn>", methods=["GET"])
def mostrar_libro(isbn):
    libro = inventario.consultar_libro(isbn)
    if libro:
        return jsonify(libro)
    else:
        return "Libro no encontrado", 404

@app.route('/libros', methods=["POST"])
def agregar_libro():
    ### trae datos del form title, quantity, price, image, author, year
    title = request.form["title"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    author = request.form["author"]
    year = request.form["year"]
    
    image = request.files["image"] if "image" in request.files else None
    img_name = ""

    if image:
        ### secure name para la img
        img_name = secure_filename(image.filename)
        nombre_base, extension = os.path.splitext(img_name)
        img_name = f"{nombre_base}_{int(time.time())}{extension}"

    new_isbn = inventario.agregar_libro(title, quantity, price, img_name, author, year)
    
    if new_isbn:
        if image:
            image.save(os.path.join(ruta_destino, img_name))
        return jsonify({"mensaje": "Libro agregado correctamente.", "isbn": new_isbn, "imagen": img_name}), 201
    else:
        return jsonify({"mensaje": "Error al agregar el producto."}), 500

@app.route('/libros/<int:isbn>', methods=["PUT"])
def modificar_libro(isbn):
    new_title = request.form.get("title")
    new_quantity = request.form.get("quantity")
    new_price = request.form.get("price")
    new_author = request.form.get("author")
    new_year = request.form.get("year")
    new_image = None

    ## verificar imagen
    if 'image' in request.files:
        image = request.files['image']
        # cambia imagen
        nombre_imagen = secure_filename(image.filename)
        nombre_base, extension = os.path.splitext(nombre_imagen)
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
        # guarda imagen
        image.save(os.path.join(ruta_destino, nombre_imagen))
        new_image = nombre_imagen
    else:
        new_image = inventario.consultar_libro(isbn)['image']  # Conservar la imagen anterior si no se sube una nueva

    ## se llama al método para modificar
    if inventario.modificar_libro(isbn, new_title, new_quantity, new_price, new_image, new_author, new_year):
        return jsonify({"mensaje": "Libro modificado"}), 200
    else:
        return jsonify({"mensaje": "Libro no encontrado"}), 404

@app.route('/libros/<int:isbn>', methods=["DELETE"])
def eliminar_libro(isbn):
    libro = inventario.consultar_libro(isbn)
    if libro:
        # eliminar la ruta si existe
        ruta_imagen = os.path.join(ruta_destino, libro["image"])
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
        # elimina del catálogo
        if inventario.eliminar_libro(isbn):
            return jsonify({"mensaje": "Libro eliminado"}), 200
        else:
            return jsonify({"mensaje": "Error al eliminar libro"}), 500
    else:
        return jsonify({"mensaje": "Libro no encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)
