"""
modelos.py
Clases del sistema: Usuario (Cliente, Administrador), Destino, Paquete y Reserva.
(Paso 2 - Diagrama de clases / Paso 4 - POO)
"""



# ----------------------------------------------------------------------
# usuario
# ----------------------------------------------------------------------
class Usuario:
    def __init__(self, nombre, email, password_hash, id=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self._password_hash = password_hash   # "_" = dato protegido (encapsulamiento)

    def obtener_hash(self):
        return self._password_hash

    def rol(self):
        return "usuario"

    def es_admin(self):
        return False

    def mostrar(self):
        return f"{self.nombre} <{self.email}> ({self.rol()})"


class Cliente(Usuario):
    def rol(self):                # POLIMORFISMO: cada clase responde distinto
        return "cliente"


class Administrador(Usuario):
    def rol(self):
        return "admin"

    def es_admin(self):
        return True


# ----------------------------------------------------------------------
# destino
# ----------------------------------------------------------------------
class Destino:
    def __init__(self, nombre, pais, costo, id=None):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self.costo = float(costo)

    def mostrar(self):
        return f"[{self.id}] {self.nombre} ({self.pais}) - ${self.costo:,.0f}"


# ----------------------------------------------------------------------
# paquete
# ----------------------------------------------------------------------
class Paquete:
    def __init__(self, nombre, fecha_inicio, fecha_fin, cupos, destinos=None, id=None,
                 ida_y_vuelta=False, fecha_vuelta=None, hora_vuelo=None):
        self.id = id
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.cupos = int(cupos)
        self.destinos = destinos if destinos is not None else []
        self.ida_y_vuelta = bool(ida_y_vuelta)
        self.fecha_vuelta = fecha_vuelta
        self.hora_vuelo = hora_vuelo

    def agregar_destino(self, destino):
        self.destinos.append(destino)

    def calcular_costo(self, personas):
        """Costo total = suma del costo de cada destino x número de personas."""
        total = 0
        for destino in self.destinos:
            total += destino.costo
        return total * personas

    def hay_disponibilidad(self, personas):
        return self.cupos >= personas

    def mostrar(self):
        nombres = ", ".join(d.nombre for d in self.destinos)
        if self.ida_y_vuelta:
            vuelo = f"ida y vuelta (vuelta: {self.fecha_vuelta})"
        else:
            vuelo = "solo ida"
        hora = f" | hora de vuelo: {self.hora_vuelo}" if self.hora_vuelo else ""
        return (f"[{self.id}] {self.nombre} | {self.fecha_inicio} a {self.fecha_fin} | "
                f"{vuelo}{hora} | cupos: {self.cupos} | destinos: {nombres}")


# ----------------------------------------------------------------------
# reserva
# ----------------------------------------------------------------------
class Reserva:
    def __init__(self, usuario_id, paquete_id, personas, total, fecha_reserva,
                 estado="confirmada", id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.paquete_id = paquete_id
        self.personas = personas
        self.total = float(total)
        self.fecha_reserva = fecha_reserva
        self.estado = estado

    def mostrar(self):
        return (f"Reserva #{self.id} | paquete {self.paquete_id} | {self.personas} personas | "
                f"${self.total:,.0f} | {self.fecha_reserva} | {self.estado}")
