import socket
import os
from pathlib import Path
import ipaddress
import time

class ClienteArchivos:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.socket = None
        self.buffer_size = 4096

    def conectar(self):
        """Establece conexion con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Conectado al servidor {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def _reconectar(self, max_intentos=5, espera=8):
        """Intenta reconectar hasta max_intentos veces"""
        for intento in range(1, max_intentos + 1):
            print(f"Reintentando conexion ({intento}/{max_intentos})...")
            if self.conectar():
                return True
            time.sleep(espera)
        return False

    def cerrar(self):
        """Cierra la conexion con el servidor"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Conexion cerrada")

    def enviar_comando(self, comando):
        """Envia un comando; si falla, intenta reconectar y reintentar una vez"""
        try:
            self.socket.sendall(comando.encode('utf-8'))
            return self.socket.recv(self.buffer_size).decode('utf-8')
        except Exception as e:
            print(f"Error en comunicacion: {e}")
            if not self._reconectar():
                print("No se pudo reconectar. Desconectando.")
                self.cerrar()
                return None
            try:
                self.socket.sendall(comando.encode('utf-8'))
                return self.socket.recv(self.buffer_size).decode('utf-8')
            except Exception as e2:
                print(f"Error tras reconexion: {e2}")
                self.cerrar()
                return None

    def listar_archivos(self):
        respuesta = self.enviar_comando("LISTAR|")
        if respuesta is not None:
            print("\nArchivos en el servidor:")
            print(respuesta)

    def leer_archivo(self, nombre_archivo):
        respuesta = self.enviar_comando(f"LEER|{nombre_archivo}")
        if respuesta is not None:
            print(f"\nContenido del archivo {nombre_archivo}:")
            print(respuesta)

    def subir_archivo(self, ruta_archivo):
        if not os.path.exists(ruta_archivo):
            print(f"Error: el archivo {ruta_archivo} no existe")
            return
        try:
            with open(ruta_archivo, 'r') as f:
                contenido = f.read()
            nombre = os.path.basename(ruta_archivo)
            respuesta = self.enviar_comando(f"SUBIR|{nombre}|{contenido}")
            if respuesta is not None:
                print(respuesta)
        except Exception as e:
            print(f"Error al subir el archivo: {e}")

    def descargar_archivo(self, nombre_archivo):
        respuesta = self.enviar_comando(f"DESCARGAR|{nombre_archivo}")
        if respuesta is None or "Error" in respuesta:
            print(respuesta or "Error desconocido")
            return
        try:
            with open(nombre_archivo, 'w') as f:
                f.write(respuesta)
            print(f"Archivo {nombre_archivo} descargado exitosamente")
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")

    def ver_logs(self):
        respuesta = self.enviar_comando("LOGS|")
        if respuesta is not None:
            print("\nRegistro de operaciones del servidor:")
            print(respuesta)

def preguntar_host():
    while True:
        h = input("IP del servidor (o 'localhost'): ")
        if h.lower() == 'localhost':
            return '127.0.0.1'
        try:
            ipaddress.ip_address(h)
            return h
        except ValueError:
            print("-> IP invalida, intente de nuevo.")

def preguntar_port():
    while True:
        try:
            p = int(input("Puerto (1–65535): "))
            if 1 <= p <= 65535:
                return p
        except ValueError:
            pass
        print("-> Puerto invalido, ingrese un numero entre 1 y 65535.")

def mostrar_menu():
    print("\n=== CLIENTE DE ARCHIVOS ===")
    print("1. Listar archivos")
    print("2. Leer archivo")
    print("3. Subir archivo")
    print("4. Descargar archivo")
    print("5. Ver logs")
    print("0. Salir")
    return input("Seleccione una opcion: ")

def main():
    host = preguntar_host()
    port = preguntar_port()

    cliente = ClienteArchivos(host, port)
    if not cliente.conectar():
        return

    try:
        while True:
            opcion = mostrar_menu()
            if opcion == "1":
                cliente.listar_archivos()
            elif opcion == "2":
                nombre = input("Nombre del archivo a leer: ")
                cliente.leer_archivo(nombre)
            elif opcion == "3":
                ruta = input("Ruta del archivo a subir: ")
                cliente.subir_archivo(ruta)
            elif opcion == "4":
                nombre = input("Nombre del archivo a descargar: ")
                cliente.descargar_archivo(nombre)
            elif opcion == "5":
                cliente.ver_logs()
            elif opcion == "0":
                break
            else:
                print("Opcion no valida")
    except KeyboardInterrupt:
        print("\nOperacion interrumpida por el usuario")
    finally:
        cliente.cerrar()

if __name__ == "__main__":
    main()
