"""
menus.py
Menús de consola: principal, cliente y administrador.
"""

import unicodedata

import autenticacion
from gestores import GestorDestinos, GestorPaquetes, GestorReservas

gestor_destinos = GestorDestinos()
gestor_paquetes = GestorPaquetes()
gestor_reservas = GestorReservas()

MAX_INTENTOS = 3   # intentos de inicio de sesión antes de volver al menú


def pedir(texto):
    return input(texto + ": ").strip()


def pedir_opcional(texto):
    """Devuelve None si el usuario aprieta Enter (para no cambiar el dato)."""
    valor = input(texto + " (Enter = no cambiar): ").strip()
    if valor == "":
        return None
    return valor


def pedir_entero(texto):
    """Pide un número entero. Si no lo es, lanza un ValueError con mensaje claro."""
    valor = pedir(texto)
    try:
        return int(valor)
    except ValueError:
        raise ValueError(f"{texto} debe ser un número entero.")


def pedir_lista_ids(texto):
    try:
        return [int(x) for x in texto.split(",") if x.strip() != ""]
    except ValueError:
        raise ValueError("Los IDs deben ser números enteros separados por coma (ejemplo: 1,2).")


def _normalizar(texto):
    """Minúsculas y sin tildes, para que 'Sí', 'si' y 'SI' sean lo mismo."""
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def a_booleano(texto):
    """True para s/si/sí, False para n/no, None si no se entiende."""
    texto = _normalizar(texto)
    if texto in ("s", "si"):
        return True
    if texto in ("n", "no"):
        return False
    return None


def confirmar(pregunta):
    """Pregunta s/n y repite hasta recibir una respuesta válida."""
    while True:
        respuesta = a_booleano(input(pregunta + " (s/n): "))
        if respuesta is not None:
            return respuesta
        print("Respuesta no válida. Escriba 's' (sí) o 'n' (no).")


def mostrar_lista(titulo, lista):
    print("\n--- " + titulo + " ---")
    if len(lista) == 0:
        print("(sin datos)")
    for elemento in lista:
        print(elemento.mostrar())


# ---------------------------------------------------------------- menú principal
def menu_principal():
    while True:
        print("\n=== VIAJES AVENTURA ===")
        print("1. Iniciar sesión")
        print("2. Registrar cliente")
        print("0. Salir")
        opcion = pedir("Opción")

        if opcion == "1":
            # al cerrar sesión se vuelve a este menú principal
            iniciar_sesion()
        elif opcion == "2":
            try:
                autenticacion.registrar_cliente(pedir("Nombre"), pedir("Correo"),
                                                input("Contraseña: "))
                print("Cuenta creada. Ya puede iniciar sesión.")
            except ValueError as error:
                print("Error:", error)
        elif opcion == "0":
            print("Hasta pronto.")
            break
        else:
            print("Opción inválida.")


def iniciar_sesion():
    """Pide las credenciales. Devuelve True si el usuario inició y luego cerró sesión
    y False si se canceló o falló. En ambos casos se vuelve al menú principal."""
    print("\n=== INICIAR SESIÓN ===")
    for intento in range(MAX_INTENTOS):
        correo = input("Correo: ").strip()
        if correo == "":
            return False
        try:
            usuario = autenticacion.iniciar_sesion(correo, input("Contraseña: "))
        except ValueError as error:
            print("Error:", error)
            continue
        print("Bienvenido,", usuario.nombre)
        if usuario.es_admin():
            menu_admin(usuario)
        else:
            menu_cliente(usuario)
        print("Sesión cerrada.")
        return True
    print("Demasiados intentos fallidos. Volviendo al menú principal.")
    return False


# ---------------------------------------------------------------- menú cliente
def menu_cliente(cliente):
    while True:
        print("\n--- MENÚ CLIENTE ---")
        print("1. Ver destinos")
        print("2. Ver paquetes disponibles")
        print("3. Calcular costo de un paquete")
        print("4. Reservar un paquete")
        print("5. Ver mi historial de reservas")
        print("6. Cancelar una reserva")
        print("7. Modificar personas de una reserva")
        print("0. Cerrar sesión")
        opcion = pedir("Opción")

        try:
            if opcion == "1":
                mostrar_lista("Destinos", gestor_destinos.listar())
            elif opcion == "2":
                mostrar_lista("Paquetes disponibles", gestor_paquetes.listar(solo_disponibles=True))
            elif opcion == "3":
                costo = gestor_paquetes.calcular_costo(pedir_entero("ID del paquete"),
                                                       pedir("Número de personas"))
                print(f"Costo total: ${costo:,.0f}")
            elif opcion == "4":
                id_reserva = gestor_reservas.reservar(cliente, pedir_entero("ID del paquete"),
                                                      pedir("Número de personas"))
                print("Reserva confirmada. Número:", id_reserva)
            elif opcion == "5":
                mostrar_lista("Mis reservas", gestor_reservas.historial(cliente))
            elif opcion == "6":
                id_reserva = pedir_entero("ID de la reserva")
                if confirmar("¿Seguro que desea cancelar la reserva?"):
                    gestor_reservas.cancelar(cliente, id_reserva)
                    print("Reserva cancelada.")
            elif opcion == "7":
                gestor_reservas.modificar_personas(cliente, pedir_entero("ID de la reserva"),
                                                   pedir("Nuevo número de personas"))
                print("Reserva modificada.")
            elif opcion == "0":
                break
            else:
                print("Opción inválida.")
        except (ValueError, PermissionError) as error:
            print("Error:", error)


# ---------------------------------------------------------------- menú administrador
def menu_admin(admin):
    while True:
        print("\n--- MENÚ ADMINISTRADOR ---")
        print("1. Registrar destino")
        print("2. Listar destinos")
        print("3. Modificar destino")
        print("4. Eliminar destino")
        print("5. Crear paquete")
        print("6. Listar paquetes")
        print("7. Modificar paquete")
        print("8. Eliminar paquete")
        print("9. Ver todas las reservas")
        print("10. Eliminar una reserva cancelada")
        print("0. Cerrar sesión")
        opcion = pedir("Opción")

        try:
            if opcion == "1":
                gestor_destinos.registrar(admin, pedir("Nombre"), pedir("País"),
                                          pedir("Costo"))
                print("Destino registrado.")
            elif opcion == "2":
                mostrar_lista("Destinos", gestor_destinos.listar())
            elif opcion == "3":
                destino_id = pedir_entero("ID del destino")
                gestor_destinos.modificar(admin, destino_id,
                                          pedir_opcional("Nombre"), pedir_opcional("País"),
                                          pedir_opcional("Costo"))
                print("Destino modificado.")
            elif opcion == "4":
                destino_id = pedir_entero("ID del destino")
                if confirmar("¿Seguro que desea eliminarlo?"):
                    gestor_destinos.eliminar(admin, destino_id)
                    print("Destino eliminado. ¡IDs actualizados!")
            elif opcion == "5":
                mostrar_lista("Destinos", gestor_destinos.listar())
                ids = pedir_lista_ids(pedir("IDs de destinos separados por coma"))
                nombre = pedir("Nombre del paquete")
                inicio = pedir("Fecha de ida/inicio (AAAA-MM-DD)")
                fin = pedir("Fecha fin (AAAA-MM-DD)")
                cupos = pedir("Cupos")
                ida_vuelta = confirmar("¿Es ida y vuelta?")
                vuelta = pedir("Fecha de vuelta (AAAA-MM-DD)") if ida_vuelta else None
                hora = pedir("Hora del vuelo (HH:MM)")
                gestor_paquetes.crear(admin, nombre, inicio, fin, cupos, ids,
                                      ida_vuelta, vuelta, hora)
                print("Paquete creado.")
            elif opcion == "6":
                mostrar_lista("Paquetes", gestor_paquetes.listar())
            elif opcion == "7":
                paquete_id = pedir_entero("ID del paquete")
                nombre = pedir_opcional("Nombre")
                inicio = pedir_opcional("Fecha inicio (AAAA-MM-DD)")
                fin = pedir_opcional("Fecha fin (AAAA-MM-DD)")
                cupos = pedir_opcional("Cupos")
                texto_ids = pedir_opcional("IDs de destinos separados por coma")
                ids = pedir_lista_ids(texto_ids) if texto_ids is not None else None
                texto_iv = pedir_opcional("¿Ida y vuelta? (s/n)")
                ida_vuelta = None
                if texto_iv is not None:
                    ida_vuelta = a_booleano(texto_iv)
                    if ida_vuelta is None:
                        raise ValueError("Responda 's' (sí) o 'n' (no) en ida y vuelta.")
                vuelta = pedir_opcional("Fecha de vuelta (AAAA-MM-DD)") if ida_vuelta is not False else None
                hora = pedir_opcional("Hora del vuelo (HH:MM)")
                gestor_paquetes.modificar(admin, paquete_id, nombre, inicio, fin, cupos, ids,
                                          ida_vuelta, vuelta, hora)
                print("Paquete modificado.")
            elif opcion == "8":
                paquete_id = pedir_entero("ID del paquete")
                if confirmar("¿Seguro que desea eliminarlo?"):
                    gestor_paquetes.eliminar(admin, paquete_id)
                    print("Paquete eliminado. ¡IDs actualizados!")
            elif opcion == "9":
                mostrar_lista("Todas las reservas", gestor_reservas.historial(admin))
            elif opcion == "10":
                reserva_id = pedir_entero("ID de la reserva")
                if confirmar("¿Seguro que desea eliminarla?"):
                    gestor_reservas.eliminar(admin, reserva_id)
                    print("Reserva eliminada. ¡IDs actualizados!")
            elif opcion == "0":
                break
            else:
                print("Opción inválida.")
        except (ValueError, PermissionError) as error:
            print("Error:", error)
