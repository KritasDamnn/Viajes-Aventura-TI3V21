"""
seguridad.py
Protección de contraseñas y control de permisos.
(Paso 5 - Acceso seguro)

Se usan solo librerías oficiales de Python (biblioteca estándar):
  - hashlib.scrypt : convierte la contraseña en un hash (no se guarda el texto real)
  - secrets        : genera la "sal" aleatoria
  - hmac           : compara hashes de forma segura
"""
import hashlib
import hmac
import re
import secrets


def hashear_password(password):
    """Devuelve 'sal$hash' en hexadecimal. Cada contraseña usa una sal distinta."""
    sal = secrets.token_bytes(16)
    hash_ = hashlib.scrypt(password.encode("utf-8"), salt=sal, n=2**14, r=8, p=1)
    return sal.hex() + "$" + hash_.hex()


def verificar_password(password, guardado):
    """Compara la contraseña ingresada con el hash guardado en la base de datos."""
    try:
        sal_hex, hash_hex = guardado.split("$")
        sal = bytes.fromhex(sal_hex)
        esperado = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    calculado = hashlib.scrypt(password.encode("utf-8"), salt=sal, n=2**14, r=8, p=1)
    return hmac.compare_digest(calculado, esperado)


def validar_fortaleza(password):
    """La contraseña debe tener 8+ caracteres, mayúscula, minúscula, número y símbolo."""
    if len(password) < 8 or len(password) > 128:
        raise ValueError("La contraseña debe tener entre 8 y 128 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe incluir al menos una mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe incluir al menos una minúscula.")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe incluir al menos un número.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("La contraseña debe incluir al menos un símbolo.")


def exigir_admin(usuario):
    """Corta la operación si el usuario no es administrador."""
    if usuario is None or not usuario.es_admin():
        raise PermissionError("No tiene permiso para realizar esta operación.")


def exigir_cliente(usuario):
    """Corta la operación si el usuario no es cliente."""
    if usuario is None or usuario.es_admin():
        raise PermissionError("Esta operación es solo para clientes.")
