import os 
import time
import threading
import shutil #Libreria para copiar mover, renombrar y eliminar archivos
import logging

#Confi de logging
logging.basicConfig(
    filename='servidor_archivos/logs/demonio.log', 
    level=logging.INFO,
    formart='%(asctime)s - %(levelname)s - %(message)s'
)
#Rutas de los directorios 

DIR_ENTRADA = 'servidor_archivos/entrada'
DIR_PROCESADOS = 'servidor_archivos/procesados'
DIR_LOGS = 'servidor_archivos/logs'

#Implementacion de los semafotos para sincronizacion de acceso a archivos

archivo_lock = threading.Lock()

#Registro de op en el archivo de registro 
def registrar_operacion(mensaje):
    with archivo_lock:
        with open(f"{DIR_LOGS}/registro.log", "a") as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {mensaje}\n")
            logging.info(mensaje)
#Procesar el arcivo
def procesar_archivo(archivo):
    try:
        origen  = os.path.join(DIR_ENTRADA, archivo)
        destino = os.path.joi(DIR_PROCESADOS, archivo)
        with archivo_lock:
        # Verificar que el archivo aun existe (podria haber sido movido por otro thread)
            if os.path.exists(origen):
                shutil.copy2(origen,destino)
                os.remove(origen)
                mensaje = f"Archivo {archivo} procesado exitosamente"
                registrar_operacion(mensaje)
                print(mensaje)

            else:
                logging.warning(f"El archivo {archivo} ya no existe en la carpeta de entrada")
    except Exception as e:
        error = f"Error al procesar el archivo {archivo}: {str(e)}"
        registrar_operacion(error)
        logging.erro(error)

#Funcion principal de demonio
def monitorear_dicrectorio():
    print(f"Iniciando monitoreo del directorio {DIR_ENTRADA}...")
    registrar_operacion("Demonio de monitoreo iniciado")

    #cREAR registro.log por si no existe

    if not os.path.exists(f"{DIR_LOGS}/registro.log"):
        with open(f"{DIR_LOGS}/registro.log", "w") as log_file:
            log_file.write("# Registro de operaciones del servidor de archivos\n")

            while True:
                try: 
                    archivos  

