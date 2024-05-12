import pytest
'''Este código contiene una serie de pruebas unitarias utilizando la biblioteca pytest en Python para verificar la funcionalidad de varias clases y métodos'''

from PracticaTemperatura import IoTSystemSingleton, SensorError, SingletonError, SensorTemperatura, Sistema, Media_DesviacionStrategy, CuantilStrategy

def test_singleton_instance(): #ASEGURAR QUE SOLO EXISTA UNA INSTANCIA DE LA CLASE SINGLETON
    instance1 = IoTSystemSingleton.getInstance() #creamos dos instancias y deben ser la misma
    instance2 = IoTSystemSingleton.getInstance()
    assert instance1 is instance2, "Singleton getInstance debe retornar la misma instancia"

def test_read_temperature(): #ASEGURA QUE SE DEVUELVA UNA TEMPERATURA EN EL RANGO ESPERADO
    sensor = SensorTemperatura()
    temperature = sensor.leer_temperatura()
    assert -20 <= temperature <= 50, "La Temperatura debe incluirse en ese rango"
    
def test_sistema_actualizar(): #ASEGURA QUE EL METODO ACTIALIZAR AÑADA LOS DATOS CORRECTAMENTE A _datos
    sistema = Sistema()
    initial_count = len(sistema._datos)
    sistema.actualizar(('2024-05-08 12:00:00', 25))
    assert len(sistema._datos) == initial_count + 1, "La actualización debe incrementar los datos"

def test_procesamiento(): #VERIFICA QUE EL SISTEMA MANEJA ADECUADAMENTE UN CONJUNTO DE ACTUALIZACIONES DE DATOS
    sistema = Sistema()
    data = [('2024-05-08 12:00:00', temp) for temp in range(10, 22)]
    for d in data:
        sistema.actualizar(d)
    # Esperamos que haya calculado estadísticas tras suficientes actualizaciones
    assert len(sistema._datos) >= 12, "El calculo estadistico ocurre tras suficientes actualizaciones"
    
def test_media_desviacion_calculation(): #ASEGURA QUE LA MEDIA Y DESVIACION TIPICA SE CALCULAN CORRECTAMENTE
    strategy = Media_DesviacionStrategy()
    data = [20, 22, 24, 26, 28, 30]
    mean, desv = strategy.calcular(data)
    assert mean == sum(data) / len(data), "La media debe ser calculada correctamente"
    assert isinstance(desv, float), "Desviacion tipica debe ser un tipo float"
