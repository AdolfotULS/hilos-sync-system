import os
import time
import threading
import shutil
import logging
import sys
import platform
import queue

# Aca ponemos donde van a estar los archivos (en tu carpeta personal)
BASE_DIR = os.path.expanduser("~/servidor_archivos")

# Estas son las carpetas k vamos a usar
DIR_ENTRADA = os.path.join(BASE_DIR, 'entrada')
DIR_PROCESADOS = os.path.join(BASE_DIR, 'procesados')
DIR_LOGS = os.path.join(BASE_DIR, 'logs')

# Esto crea las carpetas si no existen todavia
for directorio in [DIR_ENTRADA, DIR_PROCESADOS, DIR_LOGS]:
    if not os.path.exists(directorio):
        os.makedirs(directorio)

# Asi guardamos los errores y cosas importantes
logging.basicConfig(
    filename=os.path.join(DIR_LOGS, 'demonio.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Esto es pa k los archivos no se mezclen cuando varios procesos trabajan juntos
archivo_lock = threading.Lock()

# Cola para procesar archivos
cola_archivos = queue.Queue()

# Set para llevar un registro de archivos en procesamiento
archivos_en_proceso = set()
archivos_en_proceso_lock = threading.Lock()

# Esta funcion escribe en el log lo k pasa
def registrar_operacion(mensaje):
    with archivo_lock:
        log_path = os.path.join(DIR_LOGS, "registro.log")
        with open(log_path, "a", encoding='utf-8') as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {mensaje}\n")
            logging.info(mensaje)

# Esta funcion mueve los archivo de entrada a prosesados
def procesar_archivo(archivo):
    try:
        origen = os.path.join(DIR_ENTRADA, archivo)
        destino = os.path.join(DIR_PROCESADOS, archivo)
        
        # Verificamos si el archivo existe antes de procesar
        if not os.path.exists(origen):
            mensaje = f"El archivo {archivo} ya no existe en la carpeta de entrada"
            registrar_operacion(mensaje)
            logging.warning(mensaje)
            print(mensaje)
            return
            
        # Vemos si ya hay un archivo con el mismo nombre en destino
        if os.path.exists(destino):
            # Si ya existe, le ponemos la fecha al nombre para k sea unico
            nombre_base, extension = os.path.splitext(archivo)
            timestamp = time.strftime("%Y%m%d%H%M%S")
            nuevo_nombre = f"{nombre_base}_{timestamp}{extension}"
            destino = os.path.join(DIR_PROCESADOS, nuevo_nombre)
            mensaje = f"El archivo {archivo} ya existe en procesados, renombrando a {nuevo_nombre}"
            registrar_operacion(mensaje)
            print(mensaje)
        
        # Copiamos el archivo y borramos el orijinal
        # Aqui usamos el lock solo para la operacion critica
        with archivo_lock:
            if os.path.exists(origen):  # Verificamos de nuevo dentro del lock
                shutil.copy2(origen, destino)
                os.remove(origen)
                mensaje = f"Archivo {archivo} procesado exitosamente"
                registrar_operacion(mensaje)
                print(mensaje)
        
    except Exception as e:
        error = f"Error al procesar el archivo {archivo}: {str(e)}"
        registrar_operacion(error)
        logging.error(error)
        print(f"ERROR: {error}")
    finally:
        # Removemos el archivo de la lista de archivos en proceso
        with archivos_en_proceso_lock:
            if archivo in archivos_en_proceso:
                archivos_en_proceso.remove(archivo)

# Funcion que consume la cola de archivos
def worker_procesar_archivos():
    while True:
        try:
            # Obtenemos un archivo de la cola (espera si esta vacia)
            archivo = cola_archivos.get(block=True, timeout=10)
            try:
                procesar_archivo(archivo)
            finally:
                # Marcamos la tarea como completada
                cola_archivos.task_done()
        except queue.Empty:
            # Si no hay archivos por 10 segundos, sigue esperando
            continue
        except Exception as e:
            error = f"Error en worker de procesamiento: {str(e)}"
            registrar_operacion(error)
            logging.error(error)
            print(f"ERROR EN WORKER: {error}")

# Esta es la funcion principal k revisa cada 10 segundos si hay archivos
def monitorear_directorio():
    print(f"Iniciando monitoreo del directorio {DIR_ENTRADA}...")
    registrar_operacion(f"Demonio de monitoreo iniciado en {platform.system()}")
    print(f"Sistema operativo detectado: {platform.system()}")

    # Creamos el log si no existe
    log_path = os.path.join(DIR_LOGS, "registro.log")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding='utf-8') as log_file:
            log_file.write("# Registro de operaciones del servidor de archivos\n")

    # Creamos los workers (hilos que procesan la cola)
    num_workers = 3  # Podemos usar varios trabajadores
    for _ in range(num_workers):
        worker = threading.Thread(target=worker_procesar_archivos, daemon=True)
        worker.start()
    
    # Este es el bucle principal k nunca termina
    while True:
        try:
            # Buscamos archivos nuevos en la carpeta
            archivos = [f for f in os.listdir(DIR_ENTRADA) if os.path.isfile(os.path.join(DIR_ENTRADA, f))]
            
            # Filtramos para procesar solo archivos nuevos (que no esten ya en proceso)
            with archivos_en_proceso_lock:
                archivos_nuevos = [f for f in archivos if f not in archivos_en_proceso]
                
                # Si hay archivos nuevos los agregamos a la lista de en proceso
                for archivo in archivos_nuevos:
                    archivos_en_proceso.add(archivo)
            
            # Si hay archivos nuevos los mostramos
            if archivos_nuevos:
                mensaje = f"Se encontraron {len(archivos_nuevos)} archivos nuevos para procesar: {', '.join(archivos_nuevos)}"
                print(mensaje)
                registrar_operacion(mensaje)
                
                # Agregamos los archivos nuevos a la cola
                for archivo in archivos_nuevos:
                    cola_archivos.put(archivo)
            
            # Si no hay nada lo decimos
            if not archivos:
                print("No hay archivos nuevos para procesar. Esperando...")
            
            # Esperamos un ratito antes de revisar otra vez
            time.sleep(10)
            
        except Exception as e:
            error = f"Error durante el monitoreo: {str(e)}"
            registrar_operacion(error)
            logging.error(error)
            print(f"ERROR EN MONITOREO: {error}")
            time.sleep(10)

# Esto es lo k se ejecuta cuando arrancas el programa
if __name__ == "__main__":
    try:
        print(f"Iniciando demonio en {BASE_DIR}")
        print(f"Sistema operativo: {platform.system()}")
        # Empezamos el programa
        monitorear_directorio()
    except KeyboardInterrupt:
        mensaje = "Demonio de monitoreo detenido manualmente"
        registrar_operacion(mensaje)
        print(mensaje)
    except Exception as e:
        error = f"Error fatal en el demonio: {str(e)}"
        registrar_operacion(error)
        logging.critical(error)
        print(f"ERROR FATAL: {error}")