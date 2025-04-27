import socket
import threading
import os
from pathlib import Path

# Configuracion inicial
HOST = '127.0.0.1'  # Direccion IP del servidor
PORT = 65432        # Puerto donde escucha el servidor

# Directorios para guardar archivos
DIRECTORIOS = {
    "entrada": str(Path.home() / "servidor_archivos" / "entrada"),
    "procesados": str(Path.home() / "servidor_archivos" / "procesados"),
    "logs": str(Path.home() / "servidor_archivos" / "logs")
}

# Funcion para manejar las solicitudes de un cliente
def manejar_cliente(conn, addr):
    print(f"[NUEVA CONEXION] {addr} conectado.")
    try:
        while True:
            # Recibir datos del cliente
            data = conn.recv(1024).decode() # Tamano del buffer de recepcion
            if not data: # Si no hay datos, asumimos que el cliente se ha desconectado
                break

            comando, *args = data.split('|') # Separar comando y argumentos
            print(f"[{addr}] Comando recibido: {comando}, Argumentos: {args}")

            if comando == "LISTAR": 
                # Listar archivos en el directorio 'entrada'
                archivos = os.listdir(DIRECTORIOS["entrada"]) # Listar archivos en 'entrada'
                respuesta = "\n".join(archivos) if archivos else "No hay archivos."
                conn.sendall(respuesta.encode()) # Enviar lista de archivos al cliente

            elif comando == "COPIAR":
                # Copiar un archivo de 'entrada' a 'procesados'
                nombre_archivo = args[0] # Nombre del archivo a copiar
                ruta_origen = os.path.join(DIRECTORIOS["entrada"], nombre_archivo) # Ruta de origen
                ruta_destino = os.path.join(DIRECTORIOS["procesados"], nombre_archivo) # Ruta de destino

                if os.path.exists(ruta_origen): # Verificar si el archivo existe
                    with open(ruta_origen, 'rb') as f_origen, open(ruta_destino, 'wb') as f_destino: # Abrir archivos
                        f_destino.write(f_origen.read()) # Copiar contenido
                    conn.sendall(f"Archivo '{nombre_archivo}' copiado a 'procesados'.".encode()) # Enviar confirmacion al cliente
                else:
                    conn.sendall(f"Archivo '{nombre_archivo}' no encontrado en 'entrada'.".encode()) # Enviar error al cliente

            elif comando == "LEER":
                # Leer el contenido de un archivo en 'entrada'
                nombre_archivo = args[0] # Nombre del archivo a leer
                ruta_archivo = os.path.join(DIRECTORIOS["entrada"], nombre_archivo)

                if os.path.exists(ruta_archivo):
                    with open(ruta_archivo, 'r') as f: # Abrir archivo en modo lectura
                        contenido = f.read() # Leer contenido
                    conn.sendall(contenido.encode()) # Enviar contenido al cliente
                else:
                    conn.sendall(f"Archivo '{nombre_archivo}' no encontrado en 'entrada'.".encode()) # Enviar error al cliente

            else:
                conn.sendall("Comando no reconocido.".encode()) # Enviar error al cliente

    except Exception as e:
        print(f"[ERROR] Conexion con {addr} fallida: {e}")
    finally:
        conn.close()
        print(f"[DESCONEXION] {addr} desconectado.")

# Funcionamiento principal del servidor
def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Crear socket TCP
        s.bind((HOST, PORT)) # Asociar socket a la direccion y puerto
        s.listen() # Escuchar conexiones entrantes
        print(f"[ESCUCHANDO] Servidor escuchando en {HOST}:{PORT}") 

        while True: 
            conn, addr = s.accept() # Aceptar conexion
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr)) # Crear hilo para manejar cliente
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {threading.active_count() - 1}")

if __name__ == "__main__":
    iniciar_servidor()