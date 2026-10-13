"""
gestores.py
Gestores con CRUD sobre SQLite: GestorDestinos, GestorPaquetes y GestorReservas.
"""
import sqlite3
from datetime import date

import base_datos
import seguridad
import validaciones
from modelos import Destino, Paquete, Reserva


# ----------------------------------------------------------------------
# gestor_destinos
# ----------------------------------------------------------------------
class GestorDestinos:

    def _fila_a_destino(self, fila):
        return Destino(fila["nombre"], fila["pais"], fila["costo"], fila["id"])

    # CREATE
    def registrar(self, admin, nombre, pais, costo):
        seguridad.exigir_admin(admin)
        nombre = validaciones.validar_texto(nombre, "nombre")
        pais = validaciones.validar_texto(pais, "país")
        costo = validaciones.validar_numero(costo, "El costo")
        try:
            return base_datos.ejecutar(
                "INSERT INTO destinos (nombre, pais, costo) VALUES (?, ?, ?)",
                (nombre, pais, costo),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Ya existe un destino con ese nombre.")

    # READ
    def listar(self):
        filas = base_datos.consultar("SELECT * FROM destinos ORDER BY nombre")
        return [self._fila_a_destino(f) for f in filas]

    def buscar(self, destino_id):
        filas = base_datos.consultar("SELECT * FROM destinos WHERE id = ?", (destino_id,))
        if len(filas) == 0:
            return None
        return self._fila_a_destino(filas[0])

    # UPDATE (si un dato viene como None, se deja igual)
    def modificar(self, admin, destino_id, nombre=None, pais=None, costo=None):
        seguridad.exigir_admin(admin)
        destino = self.buscar(destino_id)
        if destino is None:
            raise ValueError("El destino no existe.")
        if nombre is not None:
            destino.nombre = validaciones.validar_texto(nombre, "nombre")
        if pais is not None:
            destino.pais = validaciones.validar_texto(pais, "país")
        if costo is not None:
            destino.costo = validaciones.validar_numero(costo, "El costo")
        try:
            base_datos.ejecutar(
                "UPDATE destinos SET nombre = ?, pais = ?, costo = ? WHERE id = ?",
                (destino.nombre, destino.pais, destino.costo, destino.id),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Ya existe un destino con ese nombre.")

    # DELETE
    def eliminar(self, admin, destino_id):
        seguridad.exigir_admin(admin)
        if self.buscar(destino_id) is None:
            raise ValueError("El destino no existe.")
        en_uso = base_datos.consultar(
            "SELECT 1 FROM paquete_destinos WHERE destino_id = ?", (destino_id,))
        if len(en_uso) > 0:
            raise ValueError("No se puede eliminar: el destino está en un paquete.")
        base_datos.ejecutar("DELETE FROM destinos WHERE id = ?", (destino_id,))
        base_datos.renumerar("destinos", [("paquete_destinos", "destino_id")])   # ID sin vacíos


# ----------------------------------------------------------------------
# gestor_paquetes
# ----------------------------------------------------------------------
class GestorPaquetes:

    def __init__(self):
        self.gestor_destinos = GestorDestinos()

    def _cargar_destinos(self, paquete_id):
        filas = base_datos.consultar(
            "SELECT d.* FROM destinos d "
            "JOIN paquete_destinos pd ON pd.destino_id = d.id "
            "WHERE pd.paquete_id = ? ORDER BY d.nombre",
            (paquete_id,),
        )
        return [self.gestor_destinos._fila_a_destino(f) for f in filas]

    def _fila_a_paquete(self, fila):
        destinos = self._cargar_destinos(fila["id"])
        return Paquete(fila["nombre"], fila["fecha_inicio"], fila["fecha_fin"],
                       fila["cupos"], destinos, fila["id"],
                       fila["ida_y_vuelta"], fila["fecha_vuelta"], fila["hora_vuelo"])

    def _obtener_destinos(self, ids):
        """Revisa que haya al menos 2 destinos distintos y que todos existan."""
        ids = set(ids)
        if len(ids) < 2:
            raise ValueError("El paquete debe tener al menos 2 destinos distintos.")
        destinos = []
        for id_ in ids:
            destino = self.gestor_destinos.buscar(id_)
            if destino is None:
                raise ValueError(f"El destino {id_} no existe.")
            destinos.append(destino)
        return destinos

    def _guardar_destinos(self, paquete_id, destinos):
        for destino in destinos:
            base_datos.ejecutar(
                "INSERT INTO paquete_destinos (paquete_id, destino_id) VALUES (?, ?)",
                (paquete_id, destino.id),
            )

    def _validar_vuelo(self, fecha_inicio, ida_y_vuelta, fecha_vuelta, hora_vuelo):
        """Valida los datos del vuelo. Devuelve (fecha_vuelta, hora_vuelo) listos para guardar."""
        if hora_vuelo is not None:
            hora_vuelo = validaciones.validar_hora(hora_vuelo, "La hora del vuelo")
        if not ida_y_vuelta:
            return None, hora_vuelo          # solo ida: no hay fecha de vuelta
        if fecha_vuelta is None or fecha_vuelta.strip() == "":
            raise ValueError("Si es ida y vuelta debe indicar la fecha de vuelta.")
        vuelta = validaciones.validar_fecha(fecha_vuelta, "La fecha de vuelta")
        if vuelta < validaciones.validar_fecha(fecha_inicio, "La fecha de inicio"):
            raise ValueError("La fecha de vuelta no puede ser anterior a la de ida.")
        return fecha_vuelta.strip(), hora_vuelo

    # CREATE
    def crear(self, admin, nombre, fecha_inicio, fecha_fin, cupos, destinos_ids,
              ida_y_vuelta=False, fecha_vuelta=None, hora_vuelo=None):
        seguridad.exigir_admin(admin)
        nombre = validaciones.validar_texto(nombre, "nombre")
        validaciones.validar_rango_fechas(fecha_inicio, fecha_fin)
        cupos = validaciones.validar_entero(cupos, 1, 10000, "Los cupos")
        destinos = self._obtener_destinos(destinos_ids)
        fecha_vuelta, hora_vuelo = self._validar_vuelo(fecha_inicio, ida_y_vuelta,
                                                       fecha_vuelta, hora_vuelo)
        try:
            paquete_id = base_datos.ejecutar(
                "INSERT INTO paquetes (nombre, fecha_inicio, fecha_fin, cupos, "
                "ida_y_vuelta, fecha_vuelta, hora_vuelo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombre, fecha_inicio.strip(), fecha_fin.strip(), cupos,
                 1 if ida_y_vuelta else 0, fecha_vuelta, hora_vuelo),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Ya existe un paquete con ese nombre.")
        self._guardar_destinos(paquete_id, destinos)
        return paquete_id

    # READ
    def listar(self, solo_disponibles=False):
        sql = "SELECT * FROM paquetes"
        if solo_disponibles:
            sql += " WHERE cupos > 0"
        sql += " ORDER BY fecha_inicio"
        return [self._fila_a_paquete(f) for f in base_datos.consultar(sql)]

    def buscar(self, paquete_id):
        filas = base_datos.consultar("SELECT * FROM paquetes WHERE id = ?", (paquete_id,))
        if len(filas) == 0:
            return None
        return self._fila_a_paquete(filas[0])

    # UPDATE (None = dejar igual)
    def modificar(self, admin, paquete_id, nombre=None, fecha_inicio=None,
                  fecha_fin=None, cupos=None, destinos_ids=None,
                  ida_y_vuelta=None, fecha_vuelta=None, hora_vuelo=None):
        seguridad.exigir_admin(admin)
        paquete = self.buscar(paquete_id)
        if paquete is None:
            raise ValueError("El paquete no existe.")
        if nombre is not None:
            paquete.nombre = validaciones.validar_texto(nombre, "nombre")
        if fecha_inicio is not None or fecha_fin is not None:
            inicio = fecha_inicio if fecha_inicio is not None else paquete.fecha_inicio
            fin = fecha_fin if fecha_fin is not None else paquete.fecha_fin
            validaciones.validar_rango_fechas(inicio, fin)
            paquete.fecha_inicio, paquete.fecha_fin = inicio.strip(), fin.strip()
        if cupos is not None:
            paquete.cupos = validaciones.validar_entero(cupos, 0, 10000, "Los cupos")
        if destinos_ids is not None:
            paquete.destinos = self._obtener_destinos(destinos_ids)
        # Datos del vuelo (se revisan siempre, porque la fecha de ida pudo cambiar)
        if ida_y_vuelta is not None:
            paquete.ida_y_vuelta = ida_y_vuelta
        elif fecha_vuelta is not None:
            paquete.ida_y_vuelta = True
        if fecha_vuelta is not None:
            paquete.fecha_vuelta = fecha_vuelta
        if hora_vuelo is not None:
            paquete.hora_vuelo = hora_vuelo
        paquete.fecha_vuelta, paquete.hora_vuelo = self._validar_vuelo(
            paquete.fecha_inicio, paquete.ida_y_vuelta, paquete.fecha_vuelta, paquete.hora_vuelo)
        try:
            base_datos.ejecutar(
                "UPDATE paquetes SET nombre = ?, fecha_inicio = ?, fecha_fin = ?, cupos = ?, "
                "ida_y_vuelta = ?, fecha_vuelta = ?, hora_vuelo = ? WHERE id = ?",
                (paquete.nombre, paquete.fecha_inicio, paquete.fecha_fin, paquete.cupos,
                 1 if paquete.ida_y_vuelta else 0, paquete.fecha_vuelta, paquete.hora_vuelo,
                 paquete.id),
            )
        except sqlite3.IntegrityError:
            raise ValueError("Ya existe un paquete con ese nombre.")
        if destinos_ids is not None:
            base_datos.ejecutar("DELETE FROM paquete_destinos WHERE paquete_id = ?", (paquete.id,))
            self._guardar_destinos(paquete.id, paquete.destinos)

    # DELETE
    def eliminar(self, admin, paquete_id):
        seguridad.exigir_admin(admin)
        if self.buscar(paquete_id) is None:
            raise ValueError("El paquete no existe.")
        reservas = base_datos.consultar(
            "SELECT 1 FROM reservas WHERE paquete_id = ?", (paquete_id,))
        if len(reservas) > 0:
            raise ValueError("No se puede eliminar: el paquete tiene reservas.")
        base_datos.ejecutar("DELETE FROM paquetes WHERE id = ?", (paquete_id,))
        base_datos.renumerar("paquetes", [("paquete_destinos", "paquete_id"),
                                          ("reservas", "paquete_id")])   # ID sin vacíos

    # Cálculo de costo
    def calcular_costo(self, paquete_id, personas):
        personas = validaciones.validar_entero(personas, 1, 50, "Las personas")
        paquete = self.buscar(paquete_id)
        if paquete is None:
            raise ValueError("El paquete no existe.")
        return paquete.calcular_costo(personas)


# ----------------------------------------------------------------------
# gestor_reservas
# ----------------------------------------------------------------------
class GestorReservas:

    def __init__(self):
        self.gestor_paquetes = GestorPaquetes()

    def _fila_a_reserva(self, fila):
        return Reserva(fila["usuario_id"], fila["paquete_id"], fila["personas"],
                       fila["total"], fila["fecha_reserva"], fila["estado"], fila["id"])

    def reservar(self, cliente, paquete_id, personas):
        seguridad.exigir_cliente(cliente)
        personas = validaciones.validar_entero(personas, 1, 50, "Las personas")
        paquete = self.gestor_paquetes.buscar(paquete_id)
        if paquete is None:
            raise ValueError("El paquete no existe.")
        if not paquete.hay_disponibilidad(personas):
            raise ValueError("No hay cupos suficientes.")
        total = paquete.calcular_costo(personas)

        # Descontar cupos y guardar la reserva deben ocurrir JUNTOS (transacción)
        conexion = base_datos.conectar()
        try:
            cursor = conexion.execute(
                "UPDATE paquetes SET cupos = cupos - ? WHERE id = ? AND cupos >= ?",
                (personas, paquete_id, personas),
            )
            if cursor.rowcount == 0:
                raise ValueError("No hay cupos suficientes.")
            cursor = conexion.execute(
                "INSERT INTO reservas (usuario_id, paquete_id, personas, total, fecha_reserva, estado) "
                "VALUES (?, ?, ?, ?, ?, 'confirmada')",
                (cliente.id, paquete_id, personas, total, date.today().isoformat()),
            )
            conexion.commit()
            return cursor.lastrowid
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def historial(self, usuario):
        """El cliente ve solo sus reservas; el administrador ve todas."""
        if usuario.es_admin():
            filas = base_datos.consultar("SELECT * FROM reservas ORDER BY fecha_reserva DESC")
        else:
            filas = base_datos.consultar(
                "SELECT * FROM reservas WHERE usuario_id = ? ORDER BY fecha_reserva DESC",
                (usuario.id,),
            )
        return [self._fila_a_reserva(f) for f in filas]

    def cancelar(self, cliente, reserva_id):
        seguridad.exigir_cliente(cliente)
        filas = base_datos.consultar("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        if len(filas) == 0:
            raise ValueError("La reserva no existe.")
        reserva = self._fila_a_reserva(filas[0])
        if reserva.usuario_id != cliente.id:
            raise PermissionError("No puede cancelar una reserva de otra persona.")
        if reserva.estado == "cancelada":
            raise ValueError("La reserva ya está cancelada.")

        conexion = base_datos.conectar()
        try:
            conexion.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
            conexion.execute("UPDATE paquetes SET cupos = cupos + ? WHERE id = ?",
                             (reserva.personas, reserva.paquete_id))
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    # READ (una reserva)
    def buscar(self, reserva_id):
        filas = base_datos.consultar("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        if len(filas) == 0:
            return None
        return self._fila_a_reserva(filas[0])

    # UPDATE: el cliente cambia la cantidad de personas de su reserva
    def modificar_personas(self, cliente, reserva_id, nuevas_personas):
        seguridad.exigir_cliente(cliente)
        nuevas_personas = validaciones.validar_entero(nuevas_personas, 1, 50, "Las personas")
        reserva = self.buscar(reserva_id)
        if reserva is None:
            raise ValueError("La reserva no existe.")
        if reserva.usuario_id != cliente.id:
            raise PermissionError("No puede modificar una reserva de otra persona.")
        if reserva.estado == "cancelada":
            raise ValueError("No se puede modificar una reserva cancelada.")
        paquete = self.gestor_paquetes.buscar(reserva.paquete_id)
        diferencia = nuevas_personas - reserva.personas   # positivo = necesita más cupos
        nuevo_total = paquete.calcular_costo(nuevas_personas)

        conexion = base_datos.conectar()
        try:
            cursor = conexion.execute(
                "UPDATE paquetes SET cupos = cupos - ? WHERE id = ? AND cupos >= ?",
                (diferencia, reserva.paquete_id, diferencia),
            )
            if cursor.rowcount == 0:
                raise ValueError("No hay cupos suficientes.")
            conexion.execute(
                "UPDATE reservas SET personas = ?, total = ? WHERE id = ?",
                (nuevas_personas, nuevo_total, reserva_id),
            )
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    # DELETE: el administrador borra reservas que ya estaban canceladas
    def eliminar(self, admin, reserva_id):
        seguridad.exigir_admin(admin)
        reserva = self.buscar(reserva_id)
        if reserva is None:
            raise ValueError("La reserva no existe.")
        if reserva.estado != "cancelada":
            raise ValueError("Solo se pueden eliminar reservas canceladas.")
        base_datos.ejecutar("DELETE FROM reservas WHERE id = ?", (reserva_id,))
        base_datos.renumerar("reservas")   # ID sin vacíos
