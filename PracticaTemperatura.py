from abc import ABC, abstractmethod
import time
import random
import datetime
from functools import reduce
import math

#-----------EXCEPCIONES que capturan de forma adecuada los errores que se pueden producir durante la ejecucion-----------
class SingletonError(Exception):
    """Excepción para errores relacionados con la creación de la instancia singleton."""
    pass

class SensorError(Exception):
    """Excepción para errores del sensor de temperatura."""
    pass

class ProcesamientoDatosError(Exception):
    """Excepción para errores al procesar datos en los handlers."""
    pass

class ArgumentoInvalidoError(Exception):
    """Excepción para argumentos inválidos pasados a métodos."""
    pass

class ControlEjecucionError(Exception):
    """Excepción para manejar errores en el control de ejecución de procesos, como inicio y fin de monitorización."""
    pass

class RegistroError(Exception):
    """Excepción para errores al registrar o remover observadores."""
    pass


#--------PATRON SINGLETON--------------
class IoTSystemSingleton:
    _unicaInstancia = None  

    @classmethod
    def getInstance(cls): #aseguramos que solo exista una instancia de la clase IoTSystem
        if cls._unicaInstancia is None:
            try:
                cls._unicaInstancia = cls()
            except Exception as e:
                raise SingletonError(f"Error al crear una instancia singleton: {str(e)}")
        return cls._unicaInstancia #retorna la unica instancia ya sea la recien creada o la existente

    
    def _crearsistema(self):
        return Sistema()
    
    def _crearSensor(self):
        if not isinstance(self, IoTSystemSingleton):
            raise ArgumentoInvalidoError("Método llamado desde una instancia incorrecta.")
        return SensorTemperatura()
    
    def comenzar_analisis(self, sensor): #iniciamos el analisis de las temperaturas con el SensorTemperaturas
        if not isinstance(sensor, SensorTemperatura): #Verificamos que sea una instancia de la clase Sensor
            raise ArgumentoInvalidoError("El argumento 'sensor' debe ser una instancia de SensorTemperatura.")
        try:
            return sensor.comenzar_monitorizar_temperaturas() #llama al metodo del sensor que inicia el monitoreo
        except SensorError as e:
            raise ControlEjecucionError(f"Error al iniciar el análisis: {str(e)}")
    
    def terminar_analisis(self, sensor):
            if not isinstance(sensor, SensorTemperatura):
                raise ArgumentoInvalidoError("El argumento 'sensor' debe ser una instancia de SensorTemperatura.")
            try:
                return sensor.fin_monitor_temperature()
            except Exception as e:
                raise ControlEjecucionError(f"Error al terminar el análisis: {str(e)}")


#---------PATRON OBSERVER---------
#Definimos una clase abstracta, la base de todo observador que quiera recibir actualizaciones
class Observer(ABC):
    @abstractmethod
    def actualizar(self, data):
        pass

    
class Sistema(Observer): #es el observador, que recibe y procesa los datos de temperaturas procedentes del Sensor
    def __init__(self):
        super().__init__()
        self._datos = []
        #manejadores que procesaran los datos de distintas formas, llamamos a las funciones del patron Chain of Responsability
        self.incremento_handler = IncrementoHandler()
        self.umbral_handler = UmbralHandler(successor=self.incremento_handler, umbral=28)
        self.estadisticos_handler = EstadisticosHandler(successor=self.umbral_handler)
    
    def actualizar(self, data):
        self._datos.append(data) #agregamos los datos recibidos a la lista
        print("¡El sistema ha recibido una nueva temperatura!: ", data)
        self.calculo_estadisticos(self._datos)
    
    def consulta_temperatura(self):
        return self._datos[-1][1] #devuelve la ultima temperatura registrada
    
    def calculo_estadisticos(self,data): #realizamos los calculos estadisticos oportunos
        data_temp = [] #almacenaremos los solo los valores de temperatura
        if len(data)>12: #verifica si hay mas de 12 elementos en la lista, lo que corresponde con los datos de temperaturas de 60 sg ya que se producen cada 5sg
            for i in data[-13:]: #calculamos los estadisticos en base a esos ultimos datos de la lista, correspondientes a los de 60 segundos.
                data_temp.append(i[1])
        else:
            for i in data:
                data_temp.append(i[1])
        self.estadisticos_handler.manejar_peticion(data_temp) 
        #despues de preparar la lista data_temp con los valores SOLO de temperatura, pasamos la lista a estadisticos_handler


class Observable:
    def __init__(self):
        self._observers = []
    #metodos para registrat, eliminar y notificar a los observadores, debemos comprobar previamente que son instancias de la clase Observer
    def registrar_observer(self, observer):
        if not isinstance(observer, Observer):
            raise ArgumentoInvalidoError("El argumento 'observer' debe ser una instancia de Observer.")
        try:
            self._observers.append(observer)
        except Exception as e:
            raise RegistroError(f"Error al registrar el observador: {str(e)}")

    def quitar_observer(self, observer):
        if not isinstance(observer, Observer):
            raise ArgumentoInvalidoError("El argumento 'observer' debe ser una instancia de Observer.")
        try:
            self._observers.remove(observer)
        except ValueError:
            raise RegistroError("El observador no está registrado y no se puede borrar.")

    def notificar_observers(self, data):
        for observer in self._observers:
            observer.actualizar(data)       

class SensorTemperatura (Observable): #Es el observable, que lee y monitoriza las temperaturas, y sus observadores lo observan
    def __init__(self):
        super().__init__()
        self.dato = 0 #almacenamos la ultima lectura
        self.ejecucion = False #para llevar un control sobre el comienzo y el fin de monitorizar las temperaturas

    def leer_temperatura(self):
        return round(random.uniform(-20, 50)) #generamos temperaturas entre -20 y 50ºC

    def comenzar_monitorizar_temperaturas(self): #activa el sensor para que empiece a monitorizar temperaturas
        self.ejecucion = True
        while self.ejecucion: #mientras la monitorizacion siga
            tiempo=int(time.time()) #obtenemos el tiempo actual en formato timestamp
            hora = datetime.datetime.fromtimestamp(tiempo) #convierte el timestamp en un objeto datetime
            hora = hora.strftime('%Y-%m-%d %H:%M:%S')#convierte datetime a cadena con formato año-mes-dia-hora-minuto-segundo
            temperature = self.leer_temperatura() #obtenemos una nueva medicion
            self.dato = (hora, temperature) #guarda medicion junto con el tiempo
            self.notificar_observers(self.dato)
            time.sleep(5)  #para que cada temperatura se genere cada 5 segundos, pausamos el bucle

    def fin_monitorizar_temperaturas(self): #parar de generar temperaturas
        self.ejecucion=False 
    

#---------PATRON STRATEGY----------
#con este patron podriamos crear nuevas estrategias sin alterar el codigo existente
class CalcularStrategy: #clase base para todas las estrategias de calculo que implementaran el metodo calcular
    def calcular(self, data):
        pass

class Media_DesviacionStrategy:
    def calcular(self, data):
        if not data:  # Verificamos que la lista no esté vacía
            return None, None
        # Calculamos la media y la desviación típica usando funciones de orden superior como map y reduce
        media = round(reduce(lambda x, y: x + y, data) / len(data), 2)
        # Corrección del cálculo de varianza, asegurando que no haya un error al redondear
        varianza = reduce(lambda x, y: x + y, map(lambda temp: (temp - media) ** 2, data)) / len(data)
        desviacion_tipica = round(math.sqrt(varianza), 2)
        return media, desviacion_tipica

class CuantilStrategy(CalcularStrategy): #calcular cuantiles
    def calcular(self, data):
        if not data: #verificamos que la lista no este vacia
            return None, None, None
        temp_ord = sorted(data) #ordenamos la lista y calculamos los cuantiles que corresponden al 25%,50% y 75% del tamañp de la lista
        q1 = temp_ord[int(len(temp_ord) * 0.25)]
        q2 = temp_ord[int(len(temp_ord) * 0.50)]
        q3 = temp_ord[int(len(temp_ord) * 0.75)]
        return q1, q2, q3
    
class MaxMinStrategy(CalcularStrategy):  # Calcular el mínimo y máximo
    def calcular(self, data):
        if not data:
            return None, None
        #utilizamos las funcion de segundo orden para calcular el maximo y el mimso
        maximo = reduce(lambda x, y: x if x > y else y, data)
        minimo = reduce(lambda x, y: x if x < y else y, data)
        return maximo, minimo


#---------PATRON CHAIN OF RESPONSABILITY----------

class Handler: #clase manejadora base de la cual heredaran el resto de clases
    def __init__(self, successor=None): 
        self._successor = successor

    def manejar_peticion(self, temp_data):
        try:
            if self._successor:
                self._successor.manejar_peticion(temp_data) #pasamos la peticion al sieguiente sucesor
        except Exception as e:
            raise ProcesamientoDatosError(f"Error al procesar datos de temperatura: {str(e)}")

class EstadisticosHandler(Handler):
    #inicializamos las diferentes estrategias de calculo estadistico
    def __init__(self, successor=None):
        super().__init__(successor)
        self.strategies = {
            '\tMedia y Desviacion': Media_DesviacionStrategy(),
            '\tCuantiles': CuantilStrategy(),
            '\tMax y Min': MaxMinStrategy()
        }

    def manejar_peticion(self, data):
        if len(data)==13: #hay 13 elementos que corresponden con los 60 sgs (ponemos 13 y no 12 porque contamos el 0) a partir de los cuales se calculan los estadisticos
            results = {nombre: strategy.calcular(data) for nombre, strategy in self.strategies.items()}
            print("Estadísticos calculados en los últimos 60 segundos:")
            for key, value in results.items():
                print(f"{key}: {value}") #imprime el nombre de la estrategia y su resultado el cual esta almacenado en un diccionario
                
        if self._successor: #si existe un sucesor le pasa la peticion
            self._successor.manejar_peticion(data)


class IncrementoHandler(Handler):
    #alerta sobre incrementos rapidos de temperatura en los ultimos 30 segundos
    def __init__(self, successor=None,aumento=10):
        super().__init__(successor)
        self.aumento=aumento
    
    def manejar_peticion(self, temp_data):
        if len(temp_data) > 6: #comprueba si la longitud de la lista es mayor que 6 lo que quiere decir que son 30 sg ya que cada temperatura se genera cada 5
            temp_data=temp_data[-7:] #seleccionamos los ultimos 60 segundos (ponemos 7 ya que contamos la temperatura del 0)
            temperatura_inicial = temp_data[0]
            temperaturas_aumento = list(filter(lambda temp: temp >= temperatura_inicial + self.aumento, temp_data)) #si el incremento de la temperatura en los ultimos 30 segundos supera el aumento definido
            if len(temperaturas_aumento)>0:
                print(f"¡ALERTA DE INCREMENTO RAPIDO! La temperatura aumentó más de 10°C en los últimos 30 segundos")
        
        if self._successor: #si existe un sucesor le pasa la peticion
            self._successor.manejar_peticion(temp_data)

    
class UmbralHandler(Handler):
    def __init__(self, successor=None, umbral=28):
        super().__init__(successor)
        self.umbral = umbral

    def manejar_peticion(self, temp_data):
        if temp_data[-1] > self.umbral: #comprobamos si la ultima temperatura de temp_data supera el umbral definido y en ses caso, emite una 
            print(f"¡ALERTA! La temperatura: {temp_data[-1]}°C supera el umbral de {self.umbral}°C")       
        if self._successor:
            self._successor.manejar_peticion(temp_data)
            
#---------PROGRAMA PRINCIPAL, ARRANCAMOS EL SERVICIO--------
if __name__ == "__main__":
    print("COMIENZA LA GESTION DE TEMPERATURAS DEL INVERNADERO")
    print()
    iotsistema = IoTSystemSingleton() #creamos la instancia del IoT
    sensor1 = iotsistema._crearSensor() #creamos Sensor
    sistema1 = iotsistema._crearsistema() #Creamos el sistema
    sensor1.registrar_observer(sistema1) #registramos el observador que es el propio sistema
    iotsistema.comenzar_analisis(sensor1) #comenzamos el analisis
    time.sleep(300)
    iotsistema.terminar_analisis()#finalizamos el analisis

