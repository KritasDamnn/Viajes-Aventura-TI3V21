"""
validaciones.py
Funciones para validar los datos que ingresa el usuario.
Si un dato es incorrecto lanzan ValueError con un mensaje claro.
(Requerimiento: "Validar datos ingresados por el usuario")
"""
import re
from datetime import date, datetime

# Solo se aceptan estos caracteres (lista blanca)
PATRON_TEXTO = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 .,'\-]{2,80}$")
PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]{2,}$")


def validar_texto(valor, campo="texto"):
    valor = valor.strip()
    if not PATRON_TEXTO.match(valor):
        raise ValueError(f"El campo {campo} tiene caracteres no permitidos o largo incorrecto (2 a 80).")
    return valor


def validar_correo(valor):
    valor = valor.strip().lower()
    if len(valor) > 120 or not PATRON_CORREO.match(valor):
        raise ValueError("El correo no tiene un formato válido.")
    return valor


def validar_numero(valor, campo="valor"):
    """Valida un número mayor que 0 (para costos)."""
    try:
        numero = float(valor)
    except ValueError:
        raise ValueError(f"{campo} debe ser un número.")
    if numero <= 0 or numero > 1_000_000_000:
        raise ValueError(f"{campo} debe ser mayor que 0.")
    return numero


def validar_entero(valor, minimo, maximo, campo="valor"):
    try:
        numero = int(valor)
    except ValueError:
        raise ValueError(f"{campo} debe ser un número entero.")
    if numero < minimo or numero > maximo:
        raise ValueError(f"{campo} debe estar entre {minimo} y {maximo}.")
    return numero


def validar_fecha(valor, campo="fecha"):
    """Valida una fecha con formato AAAA-MM-DD y la devuelve como objeto date."""
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{campo} debe tener formato AAAA-MM-DD.")


def validar_hora(valor, campo="La hora"):
    """Valida una hora con formato HH:MM (24 horas) y la devuelve como texto."""
    try:
        return datetime.strptime(valor.strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError(f"{campo} debe tener formato HH:MM (ejemplo 08:30).")


def validar_rango_fechas(inicio, fin):
    """La fecha de inicio no puede ser pasada y el fin no puede ser antes del inicio."""
    f_inicio = validar_fecha(inicio, "La fecha de inicio")
    f_fin = validar_fecha(fin, "La fecha de fin")
    if f_inicio < date.today():
        raise ValueError("La fecha de inicio no puede ser anterior a hoy.")
    if f_fin < f_inicio:
        raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
