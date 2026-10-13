"""
autenticacion.py
Registro de usuarios, creación del administrador inicial e inicio de sesión.
(Paso 5 - Acceso seguro)
"""
import sqlite3

import base_datos
import seguridad
import validaciones
from modelos import Administrador, Cliente

MENSAJE_ERROR = "Correo o contraseña incorrectos."   # mismo mensaje siempre (no revela qué falló)


def _crear_objeto(fila):
    """Convierte una fila de la base de datos en un objeto Cliente o Administrador."""
    if fila["rol"] == "admin":
        clase = Administrador
    else:
        clase = Cliente
    return clase(fila["nombre"], fila["email"], fila["password_hash"], fila["id"])


def _guardar_usuario(nombre, email, password, rol):
    nombre = validaciones.validar_texto(nombre, "nombre")
    email = validaciones.validar_correo(email)
    seguridad.validar_fortaleza(password)
    password_hash = seguridad.hashear_password(password)
    try:
        # Consulta parametrizada (?) para evitar SQL Injection
        return base_datos.ejecutar(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, email, password_hash, rol),
        )
    except sqlite3.IntegrityError:
        raise ValueError("Ya existe una cuenta con ese correo.")


def registrar_cliente(nombre, email, password):
    return _guardar_usuario(nombre, email, password, "cliente")


def crear_admin_inicial():
    """La primera vez que se usa el sistema se pide crear al administrador."""
    filas = base_datos.consultar("SELECT id FROM usuarios WHERE rol = 'admin'")
    if len(filas) > 0:
        return
    print("\n=== Crear administrador inicial ===")
    while True:
        nombre = input("Nombre: ")
        email = input("Correo: ")
        password = input("Contraseña: ")
        try:
            _guardar_usuario(nombre, email, password, "admin")
            print("Administrador creado.")
            return
        except ValueError as error:
            print(f"Error: {error} Intente nuevamente.")


def iniciar_sesion(email, password):
    """Devuelve el usuario si las credenciales son correctas; si no, lanza ValueError."""
    email = validaciones.validar_correo(email)
    filas = base_datos.consultar("SELECT * FROM usuarios WHERE email = ?", (email,))
    if len(filas) == 0:
        raise ValueError(MENSAJE_ERROR)
    usuario = _crear_objeto(filas[0])
    if not seguridad.verificar_password(password, usuario.obtener_hash()):
        raise ValueError(MENSAJE_ERROR)
    return usuario
