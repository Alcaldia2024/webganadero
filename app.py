import os
from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'

# Credenciales correctas
CORRECT_USERNAME = 'gamhuacaraje'
CORRECT_PASSWORD = '1234'

# Ruta para la página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifica si las credenciales son correctas
        if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
            session['user'] = username  # Guarda el usuario en la sesión
            return redirect(url_for('sistema_ganadero'))  # Redirige al sistema de ganaderos
        else:
            flash('Usuario o contraseña incorrectos.')  # Muestra un mensaje de error
            return render_template('login.html')  # Vuelve al formulario de login con mensaje de error

    return render_template('login.html')  # GET: Muestra la página de login

# Ruta para la página del sistema ganadero
@app.route('/sistema_ganadero')
def sistema_ganadero():
    if 'user' in session:
        return render_template('sistema_ganadero.html')  # Solo si el usuario está en sesión
    else:
        return redirect(url_for('login'))  # Si no ha iniciado sesión, redirige al login

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user', None)  # Elimina la sesión
    return redirect(url_for('login'))

# Configuración para la subida de imágenes
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Tamaño máximo de archivo: 16 MB

# Crear la base de datos si no existe
def init_db():
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ganaderos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            ci TEXT,
            refMarca TEXT,
            estancia TEXT,
            imagen TEXT,
            carimbo TEXT,
            imagen_carimbo TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Llamar a la función para inicializar la base de datos
init_db()

@app.route('/')
def index():
    return render_template('ver_ganadero.html')

# Ruta para crear ganaderos
@app.route('/crear_ganadero', methods=['POST'])
def crear_ganadero():
    
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    ci = request.form.get('ci')
    refMarca = request.form.get('refMarca')
    estancia = request.form.get('estancia')
    carimbo = request.form.get('carimbo')

    # Manejo de imagen del ganadero
    filename = None
    if 'imagenMarca' in request.files:
        imagen = request.files['imagenMarca']
        if imagen.filename:
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Manejo de imagen del carimbo
    filename_carimbo = None
    if 'imagenCarimbo' in request.files:
        imagen_carimbo = request.files['imagenCarimbo']
        if imagen_carimbo.filename:
            filename_carimbo = secure_filename(imagen_carimbo.filename)
            imagen_carimbo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_carimbo))

    # Insertar el nuevo ganadero en la base de datos
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ganaderos (nombre, apellido, ci, refMarca, estancia, imagen, carimbo, imagen_carimbo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, apellido, ci, refMarca, estancia, filename, carimbo, filename_carimbo))
    conn.commit()
    conn.close()

    return redirect(url_for('ver_ganaderos'))

# Ruta para ver ganaderos
@app.route('/ver_ganaderos')
def ver_ganaderos():
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ganaderos")
    ganaderos = cursor.fetchall()
    conn.close()
    return render_template('ver_ganaderos.html', ganaderos=ganaderos)

# Ruta para buscar ganaderos
@app.route('/buscar_ganaderos', methods=['GET'])
def buscar_ganaderos():
    query = request.args.get('q', '')
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ganaderos WHERE nombre LIKE ? OR apellido LIKE ?", (f'%{query}%', f'%{query}%'))
    ganaderos = cursor.fetchall()
    conn.close()
    return render_template('ver_ganaderos.html', ganaderos=ganaderos)
@app.route('/editar_ganadero/<int:ganadero_id>', methods=['GET', 'POST'])
def editar_ganadero(ganadero_id):
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Procesar los datos del formulario para actualizar el ganadero
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        ci = request.form.get('ci')
        refMarca = request.form.get('refMarca')
        estancia = request.form.get('estancia')
        carimbo = request.form.get('carimbo')

        # Si se sube una nueva imagen del ganadero
        if 'imagenMarca' in request.files and request.files['imagenMarca'].filename != '':
            imagen = request.files['imagenMarca']
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute('''
                UPDATE ganaderos 
                SET nombre = ?, apellido = ?, ci = ?, refMarca = ?, estancia = ?, imagen = ?, carimbo = ? 
                WHERE id = ?
            ''', (nombre, apellido, ci, refMarca, estancia, filename, carimbo, ganadero_id))
        else:
            cursor.execute('''
                UPDATE ganaderos 
                SET nombre = ?, apellido = ?, ci = ?, refMarca = ?, estancia = ?, carimbo = ? 
                WHERE id = ?
            ''', (nombre, apellido, ci, refMarca, estancia, carimbo, ganadero_id))

        conn.commit()
        conn.close()

        return redirect(url_for('ver_ganaderos'))
    else:
        # Mostrar el formulario de edición con los datos actuales del ganadero
        cursor.execute("SELECT * FROM ganaderos WHERE id = ?", (ganadero_id,))
        ganadero = cursor.fetchone()
        conn.close()
        return render_template('editar_ganadero.html', ganadero=ganadero)


    
@app.route('/eliminar_ganadero/<int:ganadero_id>', methods=['POST'])
def eliminar_ganadero(ganadero_id):
    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ganaderos WHERE id = ?", (ganadero_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ver_ganaderos'))


# Ruta para actualizar ganaderos
@app.route('/actualizar_ganadero/<int:ganadero_id>', methods=['POST'])
def actualizar_ganadero(ganadero_id):
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    ci = request.form.get('ci')
    refMarca = request.form.get('refMarca')
    estancia = request.form.get('estancia')
    carimbo = request.form.get('carimbo')

    conn = sqlite3.connect('ganaderos.db')
    cursor = conn.cursor()

    # Si se sube una nueva imagen
    if 'imagenMarca' in request.files and request.files['imagenMarca'].filename != '':
        imagen = request.files['imagenMarca']
        filename = secure_filename(imagen.filename)
        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute('''UPDATE ganaderos SET nombre = ?, apellido = ?, ci = ?, refMarca = ?, estancia = ?, imagen = ?, carimbo = ? WHERE id = ?''',
                       (nombre, apellido, ci, refMarca, estancia, filename, carimbo, ganadero_id))
    else:
        cursor.execute('''UPDATE ganaderos SET nombre = ?, apellido = ?, ci = ?, refMarca = ?, estancia = ?, carimbo = ? WHERE id = ?''',
                       (nombre, apellido, ci, refMarca, estancia, carimbo, ganadero_id))

    conn.commit()
    conn.close()

    return redirect(url_for('ver_ganaderos'))

# Asegúrate de que la carpeta para las imágenes exista
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
