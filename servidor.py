import os
import socket
import threading
import time
import shutil
import datetime
import logging
from pathlib import Path

# Configuracion global
HOST = '127.0.0.1'
PORT = 65432  
BUFFER_SIZE = 4096
BASE_DIR = os.path.expanduser("~/servidor_archivos")
ENTRADA_DIR = os.path.join(BASE_DIR, "entrada")
PROCESADOS_DIR = os.path.join(BASE_DIR, "procesados")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "registro.log")
MAX_CLIENTES = 5

# Sincronizacion de acceso a archivos y logs
log_mutex = threading.Lock()
files_mutex = threading.Lock()

def registrar_operacion(operacion):
    """Registra una operacion en el archivo de log"""
    with log_mutex:
        # Asegurar que el directorio de logs existe
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Asegurar que el archivo de log existe
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, 'a').close()
            
        # Registrar la operacion
        try:
            with open(LOG_FILE, 'a') as f:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp} - {operacion}\n")
            print(f"[LOG] {operacion}")
        except Exception as e:
            print(f"Error al registrar operacion: {str(e)}")

def manejar_cliente(socket_cliente, addr):
    """Maneja la conexion con un cliente"""
    direccion_cliente = f"{addr[0]}:{addr[1]}"
    registrar_operacion(f"Nueva conexion establecida: {direccion_cliente}")
    
    try:
        while True:
            # Recibir comando del cliente
            data = socket_cliente.recv(BUFFER_SIZE)
            if not data:
                break
            
            try:
                # Decodificar el comando como texto simple
                comando_completo = data.decode('utf-8').strip()
                registrar_operacion(f"Comando recibido de {direccion_cliente}: {comando_completo}")
                
                # Dividir el comando en partes usando | como separador
                partes = comando_completo.split('|')
                comando = partes[0].upper()  # convertir a mayusculas para estandarizar
                
                # Procesar el comando
                if comando == 'LISTAR':
                    respuesta = manejar_comando_listar()
                elif comando == 'COPIAR' and len(partes) > 1:
                    nombre_archivo = partes[1]
                    respuesta = manejar_comando_copiar(nombre_archivo)
                elif comando == 'LEER' and len(partes) > 1:
                    nombre_archivo = partes[1]
                    respuesta = manejar_comando_leer(nombre_archivo)
                elif comando == 'SUBIR' and len(partes) > 2:
                    nombre_archivo = partes[1]
                    # El contenido puede contener el caracter |, por lo que unimos el resto
                    contenido = '|'.join(partes[2:])
                    respuesta = manejar_comando_subir(nombre_archivo, contenido)
                elif comando == 'DESCARGAR' and len(partes) > 1:
                    nombre_archivo = partes[1]
                    respuesta = manejar_comando_descargar(nombre_archivo)
                elif comando == 'LOGS':
                    respuesta = manejar_comando_logs()
                else:
                    respuesta = "Comando desconocido o formato incorrecto."
                
            except Exception as e:
                respuesta = f"Error: {str(e)}"
            
            # Enviar respuesta al cliente
            socket_cliente.sendall(respuesta.encode('utf-8'))
    
    except Exception as e:
        registrar_operacion(f"Error en la conexion con {direccion_cliente}: {str(e)}")
    finally:
        socket_cliente.close()
        registrar_operacion(f"Conexion cerrada: {direccion_cliente}")

def manejar_comando_listar():
    """Lista los archivos en el directorio de entrada"""
    with files_mutex:
        try:
            archivos = [f for f in os.listdir(ENTRADA_DIR) if os.path.isfile(os.path.join(ENTRADA_DIR, f))]
            registrar_operacion(f"Cliente solicito listar archivos en entrada - {len(archivos)} archivos encontrados")
            
            if not archivos:
                return "No hay archivos en el directorio de entrada."
            
            respuesta = ""
            for archivo in archivos:
                respuesta += f"{archivo}\n"
            
            return respuesta.strip() # Eliminar el salto de linea final
        except Exception as e:
            registrar_operacion(f"Error al listar archivos: {str(e)}")
            return f"Error al listar archivos: {str(e)}"

def manejar_comando_copiar(nombre_archivo):
    """Copia un archivo de entrada a procesados"""
    with files_mutex:
        try:
            ruta_origen = os.path.join(ENTRADA_DIR, nombre_archivo)
            ruta_destino = os.path.join(PROCESADOS_DIR, nombre_archivo)
            
            if not os.path.exists(ruta_origen):
                return f"Error: El archivo '{nombre_archivo}' no fue encontrado en el directorio de entrada."
            
            # Asegurar que el directorio de procesados existe
            os.makedirs(PROCESADOS_DIR, exist_ok=True)
            
            shutil.copy2(ruta_origen, ruta_destino)
            registrar_operacion(f"Archivo copiado: {nombre_archivo} (entrada -> procesados)")
            return f"Archivo '{nombre_archivo}' copiado exitosamente al directorio procesados."
        
        except Exception as e:
            registrar_operacion(f"Error al copiar archivo {nombre_archivo}: {str(e)}")
            return f"Error al copiar archivo: {str(e)}"

def manejar_comando_leer(nombre_archivo):
    """Lee el contenido de un archivo"""
    with files_mutex:
        try:
            ruta_archivo = os.path.join(ENTRADA_DIR, nombre_archivo)
            
            if not os.path.exists(ruta_archivo):
                ruta_archivo = os.path.join(PROCESADOS_DIR, nombre_archivo)
                if not os.path.exists(ruta_archivo):
                    return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
            
            with open(ruta_archivo, 'r') as f:
                contenido = f.read()
            
            registrar_operacion(f"Contenido leido: {nombre_archivo}")
            return contenido
        
        except Exception as e:
            registrar_operacion(f"Error al leer archivo {nombre_archivo}: {str(e)}")
            return f"Error al leer archivo: {str(e)}"

def manejar_comando_subir(nombre_archivo, contenido):
    """Recibe un archivo del cliente y lo guarda en entrada"""
    with files_mutex:
        try:
            # Asegurar que el directorio de entrada existe
            os.makedirs(ENTRADA_DIR, exist_ok=True)
            
            ruta_archivo = os.path.join(ENTRADA_DIR, nombre_archivo)
            with open(ruta_archivo, 'w') as f:
                f.write(contenido)
            
            registrar_operacion(f"Archivo recibido del cliente: {nombre_archivo}")
            return f"Archivo '{nombre_archivo}' recibido y guardado correctamente."
        
        except Exception as e:
            registrar_operacion(f"Error al guardar archivo {nombre_archivo}: {str(e)}")
            return f"Error al guardar archivo: {str(e)}"

def manejar_comando_descargar(nombre_archivo):
    """Prepara un archivo para enviar al cliente"""
    with files_mutex:
        try:
            # Buscar en entrada primero, luego en procesados
            ruta_archivo = os.path.join(ENTRADA_DIR, nombre_archivo)
            if not os.path.exists(ruta_archivo):
                ruta_archivo = os.path.join(PROCESADOS_DIR, nombre_archivo)
                if not os.path.exists(ruta_archivo):
                    return f"Error: El archivo '{nombre_archivo}' no fue encontrado."
            
            with open(ruta_archivo, 'r') as f:
                contenido = f.read()
            
            registrar_operacion(f"Archivo enviado al cliente: {nombre_archivo}")
            return contenido
        
        except Exception as e:
            registrar_operacion(f"Error al enviar archivo {nombre_archivo}: {str(e)}")
            return f"Error al enviar archivo: {str(e)}"

def manejar_comando_logs():
    """Envia el contenido del archivo de log"""
    with log_mutex:
        try:
            # Asegurar que el archivo de log existe
            if not os.path.exists(LOG_FILE):
                return "El archivo de registro esta vacio."
                
            with open(LOG_FILE, 'r') as f:
                contenido = f.read()
            
            if not contenido:
                return "El archivo de registro esta vacio."
            
            registrar_operacion("Logs solicitados por cliente")
            return contenido
        
        except Exception as e:
            registrar_operacion(f"Error al leer logs: {str(e)}")
            return f"Error al leer logs: {str(e)}"

def verificar_entorno():
    """Verifica y crea los directorios necesarios"""
    for directorio in [BASE_DIR, ENTRADA_DIR, PROCESADOS_DIR, LOGS_DIR]:
        os.makedirs(directorio, exist_ok=True)
        print(f"Directorio verificado: {directorio}")
    
    # Crear archivo de log si no existe
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Servidor iniciado - Creacion del archivo de registro\n")
        print(f"Archivo de registro creado: {LOG_FILE}")

def iniciar_servidor():
    """Inicia el servidor"""
    print("Verificando entorno...")
    verificar_entorno()
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4 y TCP
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permitir reutilizar la direccion
    
    try:
        servidor.bind((HOST, PORT)) # Asignar la direccion y puerto
        servidor.listen(MAX_CLIENTES)
        registrar_operacion(f"Servidor iniciado en {HOST}:{PORT}")
        print(f"[*] Servidor escuchando en {HOST}:{PORT}")
        
        while True:
            cliente, addr = servidor.accept() # Aceptar una nueva conexion
            manejador_cliente = threading.Thread(target=manejar_cliente, args=(cliente, addr)) # Crear un hilo para manejar al cliente
            manejador_cliente.start()
            print(f"[*] Conexion aceptada de {addr[0]}:{addr[1]}")
    
    except KeyboardInterrupt:
        print("\n[*] Servidor detenido por el usuario")
        registrar_operacion("Servidor detenido por el usuario")
    except Exception as e:
        print(f"[!] Error en el servidor: {str(e)}")
        registrar_operacion(f"Error en el servidor: {str(e)}")
    finally:
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()