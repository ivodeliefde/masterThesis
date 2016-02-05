# -*- coding:iso-8859-1 -*-
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2
import  progressbar
import time
import os
import unicodedata

BaseURI = "http://localhost:3030/masterThesis/"

def getData(dbms_name, table, user, password, AdmUnit=True):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

	if AdmUnit == True:
		# Retrieve the names and geometries of the administrative unites
		cur.execute("select name, ST_astext(geom) from {0};".format(table))
	else:
		# Retrieve the ID, landcover type and geometries of the CORINE dataset
		cur.execute("select id, code_12, ST_astext(geom) from {0};".format(table))

	data = cur.fetchall()

	cur.close()
	conn.close()
	
	return data

# dminUnitTable2RDF takes a table with administrative units which all have a name and a geometry as input and stores it in an RDF file
def AdminUnitTable2RDF(table, country, AdmUnitType):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.com.com/resource/")
	
	# Create a graph
	g = Graph()
	
	global outputFile

	try:
		# Check if the file already exist, in which case the new triples will be appended to it
		g.parse("{0}_adminUnits.ttl".format(outputFile), format="turtle")
		#print g.serialize(format='turtle')
		# print len(g.serialize(format='turtle'))
	except:
		pass

	global BaseURI
	# Add administrative units with links to the graph
	print "Creating linked data from {0} {1} dataset".format(AdmUnitType, country)
	with progressbar.ProgressBar(max_value=len(table)) as bar:

		if not os.path.exists('{0}/'.format( AdmUnitType.lower() ) ):
			os.makedirs('{0}/'.format( AdmUnitType.lower() ))

		for i, row in enumerate(table):
			geometry = row[1]
			# print row
			try:
				name = row[0].lower()
				if '"' in name:
					name = name.replace('"', '')
				name = name.replace(' ', '_')
			except:
				print 'error:',row[0]

			# try:
			# 	unicode(name)
				
			# except:
			# 	name = name.replace('è', 'e')
			
			thing = URIRef('{0}/{1}/{2}'.format( BaseURI, AdmUnitType.lower(), name ) )

			if AdmUnitType.lower() == "country":
				g.add( (thing, RDF.type, dbpedia.Country) )
			elif AdmUnitType.lower() == "province":
				g.add( (thing, RDF.type, dbpedia.Province) )
			elif AdmUnitType.lower() == "municipality":
				g.add( (thing, RDF.type, dbpedia.Municipality) )

			g.add( (thing, FOAF.name, Literal(row[0])) )
			
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral ) ) )
			
			bar.update(i)
		
			#print g.serialize(format='turtle')

			# Write the graph to a RDF file in the turtle format
			
			g.serialize('{0}/{1}'.format( AdmUnitType.lower(), name ) , format='turtle')
			g = Graph()
	
	return

# LandcoverTable2RDF takes a table with landcover data which all have a name and a geometry as input and stores it in an RDF file
def LandcoverTable2RDF(table):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.com/resource/")

	# Read the CORINE Land cover legend file and store it in a Python dictionary
	CLC_legend = {}
	with open("clc_legend.csv", 'r') as legend:
		for i, line in enumerate(legend):
			if i > 0:
				lineList = line.split(';')
				CLC_legend[lineList[1]] = lineList[2]
	legend.close()

	# Create a graph
	g = Graph()
	
	global outputFile
	global BaseURI

	print "Creating linked data from CORINE 2012 Legend"
	if not os.path.exists('landcover/legend/'):
		os.makedirs('landcover/legend/')

	i = 0
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		for key, value in CLC_legend.iteritems():
			# Linking URI as subclass of Landcover definition on DBPedia
			g.add( ( URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, key) ), RDFS.subClassOf , dbpedia.Land_cover ) )
			g.add( ( URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, key) ), FOAF.name , Literal(value) ) )
			g.serialize("landcover/legend/CLC_{0}".format(key), format='turtle')
			g = Graph()
			bar.update(i)
			i += 1


	print "Creating linked data from CORINE 2012 dataset"
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		for i, row in enumerate(table):
			ID, Landcover, geometry = row

			thing = URIRef("{0}landcover/{1}".format( BaseURI, ID ) )

			g.add( (thing, RDF.type, URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, Landcover) ) ) )
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258> {0}^^geo:wktLiteral".format(geometry) ) ) )

			g.serialize("{0}.ttl".format(outputFile), format='turtle')
			g = Graph()

			if i % 500 == 0:
				bar.update(i)
	
	return

if (__name__ == "__main__"):

# Create linked data of provinces
	NL_provinces = getData("Masterthesis", "nl_provinces", "postgres", "")
	AdminUnitTable2RDF(NL_provinces, 'Netherlands', 'province')
	BE_provinces = getData("Masterthesis", "be_provinces", "postgres", "")
	AdminUnitTable2RDF(BE_provinces, 'Belgium', 'province')

# Create linked data of municipalities
	NL_municipalities = getData("Masterthesis", "nl_municipalities", "postgres", "")
	AdminUnitTable2RDF(NL_municipalities, 'Netherlands', 'municipality')
	BE_municipalities = getData("Masterthesis", "be_municipalities", "postgres", "")
	AdminUnitTable2RDF(BE_municipalities, 'Belgium', 'municipality')

# # Create linked data of landcover
  	Landcover = getData("Masterthesis", "corine_nl_be", "postgres", "", False)
  	LandcoverTable2RDF(Landcover)

