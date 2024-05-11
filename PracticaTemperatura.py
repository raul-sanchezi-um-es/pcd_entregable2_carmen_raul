#practica2
from abc import ABC, abstractmethod
import time
import random
import datetime
from functools import reduce
import math



class Singleton:
    _unicainstancia = None

    @classmethod
    def getInstance(cls):
        if cls._unicaInstancia is None:
            cls._unicaInstancia = cls()
        return cls._unicaInstancia
    
    def _crearsistema(self):
        return System()
    
    def _crearSensor(self):
        return SensorTemperatura()
    
    def comenzar_analisis(self,sensor):
        return sensor.start_monitor_temperature()
    
    def terminar_analisis(self,sensor):
        return sensor.end_monitor_temperature()
    

#PATRON OBSERVER
class Observer(ABC):
    @abstractmethod
    def update(self, data):
        pass

    
class System(Observer):
    def __init__(self):
        super().__init__()
        self._datos = []

        self.incremento_handler = IncrementoHandler()
        self.umbral_handler = UmbralHandler(successor=self.incremento_handler, threshold=28)
        self.estadisticos_handler = EstadisticosHandler(successor=self.umbral_handler)
    
    def update(self, data):
        self._datos.append(data)
        print(data)
        self.calculo_estadisticos(self._datos)
    
    def consulta_temperatura(self):
        return self._datos[-1][1]
    
    def calculo_estadisticos(self,data):
        data_temp = []
        if len(data)>12:
            for i in data[-12:]:
                data_temp.append(i[1])
        else:
            for i in data:
                data_temp.append(i[1])
        self.estadisticos_handler.process_request(data_temp)




class Observable:
    def __init__(self):
        self._observers = []

    def register_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self, data):
        for observer in self._observers:
            observer.update(data)       

class SensorTemperatura (Observable):
    def __init__(self):
        super().__init__()
        self.dato = 0
        self.ejecucion = False

    def read_temperature(self):
        return round(random.uniform(0, 80))

    def start_monitor_temperature(self):
        self.ejecucion = True
        while self.ejecucion:
            tiempo=int(time.time())
            hora = datetime.datetime.fromtimestamp(tiempo)
            hora = hora.strftime('%Y-%m-%d %H:%M:%S')
            temperature = self.read_temperature()
            self.dato = (hora, temperature)
            self.notify_observers(self.dato)
            time.sleep(5) 

    def end_monitor_temperature(self):
        self.ejecucion=False 
    

#PATRON ESTRATEGIAS
class CalculationStrategy:
    def calculate(self, data):
        pass

class AverageStdDevStrategy(CalculationStrategy): #calcular estadisticos
    def calculate(self, data):
        if not data:
            return None, None
        mean = reduce(lambda x, y: x + y, data) / len(data)
        variance = reduce(lambda x, y: x + y, map(lambda temp: (temp - mean) ** 2, data)) / len(data)
        return mean, math.sqrt(variance)

class QuantileStrategy(CalculationStrategy): #calcular cuantiles
    def calculate(self, data):
        if not data:
            return None, None, None
        sorted_temps = sorted(data)
        q1 = sorted_temps[int(len(sorted_temps) * 0.25)]
        q2 = sorted_temps[int(len(sorted_temps) * 0.50)]
        q3 = sorted_temps[int(len(sorted_temps) * 0.75)]
        return q1, q2, q3

class MaxMinStrategy(CalculationStrategy): #calcular el minimo y maximo
    def calculate(self, data):
        if not data:
            return None, None
        return max(data), min(data)




#PATRON CHAIN OF RESPONSABILITY
class Handler:
    def __init__(self, successor=None):
        self._successor = successor

    def process_request(self, temp_data):
        pass

class EstadisticosHandler(Handler):
    def __init__(self, successor=None):
        super().__init__(successor)

        self.strategies = {
            'average_stddev': AverageStdDevStrategy(),
            'quantiles': QuantileStrategy(),
            'max_min': MaxMinStrategy()
        }

    def process_request(self, data):

        if len(data)==12:
            results = {name: strategy.calculate(data) for name, strategy in self.strategies.items()}
            print("Estadísticas calculadas:")
            for key, value in results.items():
                print(f"{key}: {value}")


        if self._successor:
            self._successor.process_request(data)


class IncrementoHandler(Handler):
    def process_request(self, temp_data,aumento = 10):
        if len(temp_data) >= 6:
            temp_data=temp_data[-6:]
            temperatura_inicial = temp_data[0]
            temperaturas_aumento = list(filter(lambda temp: temp >= temperatura_inicial + aumento, temp_data))
            if len(temperaturas_aumento)>0:
                print(f"Alerta de incremento rápido: temperatura aumentó más de 10°C en los últimos 30 segundos")
        
        if self._successor:
            self._successor.process_request(temp_data)


    
class UmbralHandler(Handler):
    def __init__(self, successor=None, threshold=28):
        super().__init__(successor)
        self.threshold = threshold

    def process_request(self, temp_data):
        if temp_data[-1] > self.threshold:
            print(f"Alerta de temperatura: {temp_data[-1]}°C supera el umbral de {self.threshold}°C")       
        if self._successor:
            self._successor.process_request(temp_data)



iotsistema = Singleton()
sensor1 = iotsistema._crearSensor()
sistema1 = iotsistema._crearsistema()
sensor1.register_observer(sistema1)
iotsistema.comenzar_analisis(sensor1)
time.asleep(300)
iotsistema.terminar_analisis()

