import datetime
import pandas as pd
import minimal_pixel_extractor_modis
import pyproj
import sys
from datetime import datetime

from shapely.geometry import Polygon, MultiPolygon, MultiPoint
from shapely.wkt import loads

## GEE init
import ee
ee.Initialize()

## crear puntos/geometrias
class Punto():
  
  def __init__(self, WKT_poligono_pixel, fasa, faco):

    self.GEOMETRY = loads(WKT_poligono_pixel)
    self.GEE_GEOMETRY = self._crear_geometria_gee()
    self.fasa = fasa
    self.faco = faco
    
  def _crear_geometria_gee(self, reproject = True):
    """ Con la geometria del pixel, crea una geometria de punto para consultar la api. 
    Si es necesario se puede pasar el parametro reproject que reproyecta de modis a WGS84 
    
    :param reproject: True por defecto, reproyecta de MODIS a WGS84
    :returns: geometria de GEE 
    """

    if reproject == True:
      wgs84 = pyproj.Proj("+init=EPSG:4326")
      modis = pyproj.Proj("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
    
      lat, lon = pyproj.transform(modis, wgs84, self.GEOMETRY.x, self.GEOMETRY.y)

    else:
      lat = self.GEOMETRY.x
      lon = self.GEOMETRY.y
#     self.GEE_GEOMETRY = ee.Geometry.Point(lat, lon)
    
    return ee.Geometry.Point(lat, lon)
    
  def _get_recurso(self, recurso):
    """ Toma el nombre de un recurso y devuelve un dataframe con el resultado de la consulta de este punto en el producto especificado 
    
    :param recurso: Nombre del recurso que se quiere extraer (mismo nombre que en GEE)
    :returns: Pandas DataFrame con la serie temporal ## TODO: describir la tabla que devuelve 
    """
    ## Generar la coleccion del recurso y consultarla para este punto
    collection = ee.ImageCollection(recurso).filterDate(self.fasa, self.faco)
    serie_vi = collection.getRegion(self.GEE_GEOMETRY, 1).getInfo()
    
    mod = pd.DataFrame(serie_vi[1:], columns = serie_vi[0])
    mod[u'time'] = pd.to_datetime(mod[u'time'], unit='ms')
    
    return mod
  
  def _interpolar_serie(self, df, variable):
    """ Toma un df extraido y la columna que se quiere interpolar y devuelve una serie temporal interpolada linealmente (no deberia ser usada por separado (?))
    
    :param df: product dataframe
    :param variable: columna del df que se quiere interpolar

    :returns: devuelve la serie diaria interpolada de la variable
    """
    
    s = pd.Series(df[variable])
    s.index = df[u'time']
#     self.extraccion_modis_interpolada = s.asfreq("D", method='backfill') ## diferentes metodos de interpolacion (lineal y ultimo valor para atras/adelante)
    return s.resample('D').interpolate()
  
  def procesar_IV_MODIS(self):
    """ Toma el df de MOD13Q1 generado por alguna de las funciones de extraccion y filtra y procesa el producto MOD13Q1, guarda el resultado en los attributos MOD13Q1_NDVI, MOD13Q1_EVI """
    
    ## Toma el df de esta variable porque puede venir de GEE o de otro lugar (revisar)
    filtrado = self._filtro_calidad_IV_MODIS(self.MOD13Q1)
    setattr(self, "MOD13Q1_NDVI", self._interpolar_serie(filtrado, u'NDVI'))
    setattr(self, "MOD13Q1_EVI", self._interpolar_serie(filtrado, u'EVI'))
    
    return None
    
  def _filtro_calidad_IV_MODIS(self, df):
    """ Toma una extraccion de MOD13Q1 como un df y devuelve otro df con los valores de IV filtrados
    lo que no cimplen la calidad los sacan del df, funcion interna
    TODO: chequear que sea asi?? que los saque o que hace"""
    
    ## Generar un vector de condiciones de calidad usando una lambda func
    criterio = df[u'DetailedQA'].map(lambda x: not (pd.isnull(x) or\
                   int(x) & 32768 == 32768 or\
                   int(x) & 16384 == 16384 or\
                   int(x) & 1024 == 1024 or\
                   int(x) & 192 != 64))
    ## aplicar las condiciones al df original
    return df[criterio]
 
  def filtro_temporal(self, df, inicio, final):
    """ Dado un dataframe y un rango temporal devuelve los elementos dentro del rango temporal
    :param df: dataframe a filtrar
    :returns: filtered pandas dataframe """
    fecha_inicial = datetime.strptime(inicio, "%Y-%m-%d")
    fecha_final = datetime.strptime(final, "%Y-%m-%d")
    criterio = df.time.map(lambda x: (x > fecha_inicial) and (x < fecha_final))
    return df[criterio]
  
  def _filtro_calidad_TEMP_MODIS(self, df, producto):
    """ Aplica el filtro de calidad a las imagenes modis de temperatura MOD11Ax """
    ## aplica la columna de calidad que le corresponde al recurso que se esta generando
    if producto == "dia":
      df = df[df[u'QC_Day'].notnull()]
      criterion = df[u'QC_Day'].map(lambda x: int(x) == 0)
    elif producto == "noche":
      df = df[df[u'QC_Night'].notnull()]
      criterion = df[u'QC_Night'].map(lambda x: int(x) == 0)
    else:
      print "producto equivocado" ## seria mejor que tire un error, corregir
      return None
    
    ## aplicar las condiciones al df original
    return df[criterion]    
  

  def procesar_TEMP_MODIS(self):
    """ Extrae los valores de tempratura diaria/semanal de las imagenes modis
    y los guarda en la variable MODIS_T_DIA y MODIS_T_NOCHE"""
    ## TODO: pasar estas funciones a seattr como las de IV

    filtrado = self._filtro_calidad_TEMP_MODIS(self.MOD11A2, "dia")
    self.MODIS_TEMP_DIA = (self._interpolar_serie(filtrado, u'LST_Day_1km')*0.02) - 273
    
    filtrado = self._filtro_calidad_TEMP_MODIS(self.MOD11A2, "noche")
    self.MODIS_TEMP_NOCHE = (self._interpolar_serie(filtrado, u'LST_Night_1km')*0.02) - 273
    
    return None

  def calcular_fpar(self, pendiente, ordenada):
    """ calcula la Fpar para la serie """
    ## TODO: esto!!    
    return None
  
  def procesar_PPT_TRMM(self):
    """ Hace la extraccion de la serie de TRMM para el lugar y la guarda en TRMM_PP """
    
    mod = getattr(self, "3B42")
    s = pd.Series(mod[u'precipitation'])
    s.index = mod[u'time']
    
    self.TRMM_PP = s
    
    return None
  
  def extraer_IV_LANDSAT(self):
    """ Extrae y calcula el IVN para imagenes landsat"""
    
    mod = l._get_recurso('LANDSAT/LE7_L1T_8DAY_NDVI')
    self.LANDSAT7_8DAY_NDVI = self._interpolar_serie(mod, u'NDVI')

    mod = l._get_recurso('LANDSAT/LE7_L1T_8DAY_EVI')
    self.LANDSAT7_8DAY_EVI = self._interpolar_serie(mod, u'EVI')
    
    mod = l._get_recurso('LANDSAT/LE7_L1T_32DAY_NDVI')
    self.LANDSAT7_32DAY_NDVI = self._interpolar_serie(mod, u'NDVI')

    mod = l._get_recurso('LANDSAT/LE7_L1T_32DAY_EVI')
    self.LANDSAT7_32DAY_EVI = self._interpolar_serie(mod, u'EVI')  
    
    return None
  


class Lote:
  """ Clase para representar el lote, construye los pixeles modis que caen 90% dentro y hace las extracciones para esos pixeles """

  def __init__(self, wkt, fasa, faco):
    ## geometrias
    self.WKT_POLYGON = wkt
    self.PIXELES_MODIS = [] ## iterable/diccionario con los objetos "punto" del lote
    
    ## atributos del lote (poner todos los de la base??, hacer una funcion que parse los atributos desde la base)
    self.fasa = fasa
    self.faco = faco
    self.cultivar = None
    self.rendimiento = None
  
  def _get_pixeles_modis(self, proporcion):
    """ Toma el poligono del lote y devuelve los pixeles modis 
    que caen dentro y el porcentaje dentro tambien en WKT/feature collection """
    
    poligono = loads(self.WKT_POLYGON)
    geometrias = minimal_pixel_extractor_modis.get_pixeles_modis(poligono, proporcion)
    if geometrias is not None:
      ## return pixel centroid
      return geometrias[0]
    ## no selected pixels
    return None
  
  def construir_puntos_modis(self, proporcion=0.9):
    """ rellena la lista de puntos modis que caen dentro del lote con objetos Punto """
    pixels_modis = self._get_pixeles_modis(proporcion) 
    if pixels_modis is not None:
      for p in pixels_modis:
        self.PIXELES_MODIS.append(Punto(p.wkt, self.fasa, self.faco))
    
    return None
  
  def extraer_variables_lote_completo(self, variables):
    """ Extrae la variable que se le pasa como argumento para el lote, la variable la guarda en un atributo
    que se llama igual que la variable que extrae """
    ## agarro las geometrias del lote y las convierto en un feature para consultar en GEE
    geometrias = [self.PIXELES_MODIS[x].GEE_GEOMETRY for x in range(len(self.PIXELES_MODIS))]
    features = [ee.Feature(geometrias[x], {'id': str(x)}) for x in range(len(geometrias))]
    feature_collection = ee.FeatureCollection(features)
    
    for variable in variables:
      ## Agrego un atributo que se llama como la imagen el nombre del atributo es la ultima parte despues de un "/"
      atributo = variable.split("/")[-1]

      
      ## hago la consulta de todas las geometrias juntas para ahorrar tiempo
      collection = ee.ImageCollection(variable).filterDate(self.fasa, self.faco)
      serie_vi = collection.getRegion(feature_collection, 1).getInfo()
      mod = pd.DataFrame(serie_vi[1:], columns = serie_vi[0])
      mod = pd.DataFrame(serie_vi[1:], columns = serie_vi[0])
      mod[u'time'] = pd.to_datetime(mod[u'time'], unit='ms')

      ## redistribuyo los resultados a cada pixel usando las coordenadas como filtro
      cont = 0
      for p in self.PIXELES_MODIS:
        tolerancia = 0.00001 ## TOLERANCIA PORQUE GEE REDONDEA LAS COORDENADAS
        coordenadas = p.GEE_GEOMETRY['coordinates']
        condicion1 = mod['longitude'].map(lambda x: abs(x - coordenadas[0]) < tolerancia) 
        fitrado1 = mod[condicion1]
        condicion2 = fitrado1['latitude'].map(lambda x: abs(x - coordenadas[1]) < tolerancia)
        filtrado2 = fitrado1[condicion2]
        setattr(p, atributo, filtrado2) ## le agrego el atributo del recurso crudo que estoy bajando a la instancia del punto

    return None
  
  def aplicar_a_puntos(self, funcion):
    """ Si le das uno de los metodos de los puntos se los aplica a todos los puntos del lote uno por uno 
    XXX TODO: Tiene que tomar los argumentos de la funcion tambien asi puedo aplicar cualquier funcion que necesite"""
    for p in self.PIXELES_MODIS:
      getattr(p, funcion)()

    return None

  def calcular_serie_agregada(self, variable):
    """ toma todos los puntos que correspondan al lote y los agrega en una sola serie por el promedio 
    de la variable que se le pida
    XXX TODO: Que sea posible agregarle el metodo de agregacion como un atributo """
    
    ## Toma las series de cada uno de los puntos y las mete en una lista
    series_iterable = []
    for p in self.PIXELES_MODIS:
      series_iterable.append(getattr(p, variable))
    
    ## Concatena las listas y las agrupa por el indice
    unido = pd.concat(series_iterable)
    ## devuelve la media de las coincidencias de los indices
    return unido.groupby(unido.index).mean()
