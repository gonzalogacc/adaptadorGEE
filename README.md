# adaptadorGEE

Pandas (http://pandas.pydata.org/)
Google earth engine API (https://code.google.com/p/earthengine-api/wiki/Installation)

##### USO: #####
l = Lote(WKT, fasa, faco) ## multipolygon WKT en coords modis

l.construir_puntos_modis() ## extraer pixeles modis del lote

l.extraer_variables_lote_completo(["MODIS/MOD13Q1", ]) ## extraer variables listadas para todo el lote (nombre GEE)

l.aplicar_a_puntos("procesar_IV_MODIS") ## Aplicar procesamiento a todos los puntos del lote
