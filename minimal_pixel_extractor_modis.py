from shapely.geometry import Polygon, MultiPolygon, MultiPoint
from shapely.wkt import loads
import numpy as np

def pixel_factory(ul):
	""" Toma la tupla de las coordenadas ul y devuelve el pixel modis que empiea ne esa coordenada pixel modis """
	
	pixel_size_x = 231.656358263750064
	pixel_size_y = -231.656358263750064

	ll = (ul[0], ul[1] + pixel_size_y)
	lr = (ul[0] + pixel_size_x, ul[1] + pixel_size_y)
	ur = (ul[0] + pixel_size_x, ul[1])
	
	pol = Polygon([ll, lr, ur, ul])
	
	return pol

def get_pixeles_modis(multipoligono_wkt, proporcion):
	""" Toma el poligono en shapely format (6842) y devuelve lo pixeles que caen dentro de modis 250 """

	pixel_size_x = 231.656358263750064
	pixel_size_y = -231.656358263750064
	
	## Exrtaer los pixeles dentro del poligono
	for feature in multipoligono_wkt:
		## Minima caja de pixeles modis (puede sacarse de ser necesario)
		coordenadas_envelope = list(feature.envelope.boundary.coords)
		ll = (int((coordenadas_envelope[0][0]//pixel_size_x)+1)*pixel_size_x, int((coordenadas_envelope[0][1]//pixel_size_y))*pixel_size_y)
		lr = (int((coordenadas_envelope[1][0]//pixel_size_x))*pixel_size_x, int((coordenadas_envelope[1][1]//pixel_size_y))*pixel_size_y)
		ur = (int((coordenadas_envelope[2][0]//pixel_size_x))*pixel_size_x, int((coordenadas_envelope[2][1]//pixel_size_y)+1)*pixel_size_y)
		ul = (int((coordenadas_envelope[3][0]//pixel_size_x)+1)*pixel_size_x, int((coordenadas_envelope[3][1]//pixel_size_y)+1)*pixel_size_y)
		interno = Polygon([ll, lr, ur, ul])

		## crear los candidatos para estar dentro del poligono
		pixeles_dentro = []
		centroides_dentro = []
		for x in np.arange(min(ul[0], lr[0]), max(ul[0], lr[0]) - pixel_size_x, pixel_size_x):
			for y in np.arange(max(ul[1], lr[1]), min(ul[1], lr[1]) , pixel_size_y):

				## crear el pixel e interceptarlo
				pixel = pixel_factory((x, y))
				pp = np.asarray(pixel.boundary.coords)
				dif = pixel.intersection(feature)

				## si esta dentro mas de x% se queda
				if dif.area > pixel.area * proporcion:
					centroide = pixel.centroid
					pc = np.asarray(centroide.coords)
					
					pixeles_dentro.append(pixel)
					centroides_dentro.append(centroide)
	
	if len(centroides_dentro) > 0:
		multipoligono = MultiPolygon(pixeles_dentro) 
		multipunto = MultiPoint(centroides_dentro)
		return multipunto, multipoligono
	else:
		return None
