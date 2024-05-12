from abc import ABC, abstractmethod
import time
import random
import datetime
from functools import reduce
import math

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


class IoTSystemSingleton:
    _unicaInstancia = None  

    @classmethod
    def getInstance(cls):
        if cls._unicaInstancia is None:
            try:
                cls._unicaInstancia = cls()
            except Exception as e:
                raise SingletonError(f"Error al crear una instancia singleton: {str(e)}")
        return cls._unicaInstancia

    
    def _crearsistema(self):
        return Sistema()
    
    def _crearSensor(self):
        if not isinstance(self, IoTSystemSingleton):
            raise ArgumentoInvalidoError("Método llamado desde una instancia incorrecta.")
        return SensorTemperatura()
    
    def comenzar_analisis(self, sensor):
        if not isinstance(sensor, SensorTemperatura):
            raise ArgumentoInvalidoError("El argumento 'sensor' debe ser una instancia de SensorTemperatura.")
        try:
            return sensor.comenzar_monitorizar_temperaturas()
        except SensorError as e:
            raise ControlEjecucionError(f"Error al iniciar el análisis: {str(e)}")
    
    def terminar_analisis(self, sensor):
            if not isinstance(sensor, SensorTemperatura):
                raise ArgumentoInvalidoError("El argumento 'sensor' debe ser una instancia de SensorTemperatura.")
            try:
                return sensor.end_monitor_temperature()
            except Exception as e:
                raise ControlEjecucionError(f"Error al terminar el análisis: {str(e)}")


#PATRON OBSERVER
class Observer(ABC):
    @abstractmethod
    def actualizar(self, data):
        pass

    
class Sistema(Observer):
    def __init__(self):
        super().__init__()
        self._datos = []
        self.incremento_handler = IncrementoHandler()
        self.umbral_handler = UmbralHandler(successor=self.incremento_handler, umbral=28)
        self.estadisticos_handler = EstadisticosHandler(successor=self.umbral_handler)
    
    def actualizar(self, data):
        self._datos.append(data)
        print("¡El sistema ha recibido una nueva temperatura!: ", data)
        self.calculo_estadisticos(self._datos)
    
    def consulta_temperatura(self):
        return self._datos[-1][1]
    
    def calculo_estadisticos(self,data):
        data_temp = []
        if len(data)>12:
            for i in data[-13:]:
                data_temp.append(i[1])
        else:
            for i in data:
                data_temp.append(i[1])
        self.estadisticos_handler.manejar_peticion(data_temp)


class Observable:
    def __init__(self):
        self._observers = []

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

class SensorTemperatura (Observable):
    def __init__(self):
        super().__init__()
        self.dato = 0
        self.ejecucion = False

    def leer_temperatura(self):
        return round(random.uniform(-20, 50))

    def comenzar_monitorizar_temperaturas(self):
        self.ejecucion = True
        while self.ejecucion:
            tiempo=int(time.time())
            hora = datetime.datetime.fromtimestamp(tiempo)
            hora = hora.strftime('%Y-%m-%d %H:%M:%S')
            temperature = self.leer_temperatura()
            self.dato = (hora, temperature)
            self.notificar_observers(self.dato)
            time.sleep(5) 

    def fin_monitorizar_temperaturas(self):
        self.ejecucion=False 
    

#PATRON ESTRATEGIAS
class CalcularStrategy:
    def calcular(self, data):
        pass

class Media_DesviacionStrategy(CalcularStrategy): #calcular estadisticos
    def calcular(self, data):
        if not data:
            return None, None
        mean = reduce(lambda x, y: x + y, data) / len(data)
        variance = reduce(lambda x, y: x + y, map(lambda temp: (temp - mean) ** 2, data)) / len(data)
        return mean, math.sqrt(variance)

class CuantilStrategy(CalcularStrategy): #calcular cuantiles
    def calcular(self, data):
        if not data:
            return None, None, None
        sorted_temps = sorted(data)
        q1 = sorted_temps[int(len(sorted_temps) * 0.25)]
        q2 = sorted_temps[int(len(sorted_temps) * 0.50)]
        q3 = sorted_temps[int(len(sorted_temps) * 0.75)]
        return q1, q2, q3

class MaxMinStrategy(CalcularStrategy): #calcular el minimo y maximo
    def calcular(self, data):
        if not data:
            return None, None
        return max(data), min(data)


#PATRON CHAIN OF RESPONSABILITY
class Handler:
    def __init__(self, successor=None):
        self._successor = successor

    def manejar_peticion(self, temp_data):
        try:
            if self._successor:
                self._successor.manejar_peticion(temp_data)
        except Exception as e:
            raise ProcesamientoDatosError(f"Error al procesar datos de temperatura: {str(e)}")

class EstadisticosHandler(Handler):
    def __init__(self, successor=None):
        super().__init__(successor)

        self.strategies = {
            '\tMedia y Desviacion': Media_DesviacionStrategy(),
            '\tCuantiles': CuantilStrategy(),
            '\tMax y Min': MaxMinStrategy()
        }

    def manejar_peticion(self, data):
        if len(data)==13:
            results = {name: strategy.calcular(data) for name, strategy in self.strategies.items()}
            print("Estadísticos calculados en los últimos 60 segundos:")
            for key, value in results.items():
                print(f"{key}: {value}")


        if self._successor:
            self._successor.manejar_peticion(data)


class IncrementoHandler(Handler):
    def manejar_peticion(self, temp_data,aumento = 10):
        if len(temp_data) > 6:
            temp_data=temp_data[-7:]
            temperatura_inicial = temp_data[0]
            temperaturas_aumento = list(filter(lambda temp: temp >= temperatura_inicial + aumento, temp_data))
            if len(temperaturas_aumento)>0:
                print(f"¡ALERTA DE INCREMENTO RAPIDO! La temperatura aumentó más de 10°C en los últimos 30 segundos")
        
        if self._successor:
            self._successor.manejar_peticion(temp_data)


    
class UmbralHandler(Handler):
    def __init__(self, successor=None, umbral=28):
        super().__init__(successor)
        self.umbral = umbral

    def manejar_peticion(self, temp_data):
        if temp_data[-1] > self.umbral:
            print(f"¡ALERTA! La temperatura: {temp_data[-1]}°C supera el umbral de {self.umbral}°C")       
        if self._successor:
            self._successor.manejar_peticion(temp_data)
            
if __name__ == "__main__":
    print("COMIENZA LA GESTION DE TEMPERATURAS DEL INVERNADERO")
    print()
    iotsistema = IoTSystemSingleton()
    sensor1 = iotsistema._crearSensor()
    sistema1 = iotsistema._crearsistema()
    sensor1.registrar_observer(sistema1)
    iotsistema.comenzar_analisis(sensor1)
    time.asleep(300)
    iotsistema.terminar_analisis()

