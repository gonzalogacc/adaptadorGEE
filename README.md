# adaptadorGEE

Pandas (http://pandas.pydata.org/)
Google earth engine API (https://code.google.com/p/earthengine-api/wiki/Installation)

Operaciones a escala de pixel:

	Extraccion de recursos.  
	Filtrado por calidad.  
	Interpolar la serie temporal.
	
Operaciones a escala de lote:
	
	Creacion de geometrias. 
	Agregacion espacial.  
	reporte.  


##Pasos:
#### Creacion del lote  
Multipolygon WKT en coords modis.  Fasa y faco en '2000-01-01'.   
`l = Lote(WKT, fasa, faco)`  

#### Creacion de las geometrias y pixeles interpolados.  
extraer pixeles modis del lote.  
`l.construir_puntos_modis()`  

#####Extraer las variables requeridas
l.extraer_variables_lote_completo(["MODIS/MOD13Q1", ]) ## extraer variables listadas para todo el lote (nombre GEE)

#####Procesar el IV sacado de MOD13Q1
l.aplicar_a_puntos("procesar_IV_MODIS") ## Aplicar procesamiento a todos los puntos del lote