from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2
import  progressbar
import time

BaseURI = "data:"
outputFile = "test"

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

	return data

# dminUnitTable2RDF takes a table with administrative units which all have a name and a geometry as input and stores it in an RDF file
def AdminUnitTable2RDF(table, country, AdmUnitType):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

	# Create a graph
	g = Graph()
	
	global outputFile

	try:
		# Check if the file already exist, in which case the new triples will be appended to it
		g.parse("{0}.ttl".format(outputFile), format="turtle")
		#print g.serialize(format='turtle')
		# print len(g.serialize(format='turtle'))
	except:
		pass

	global BaseURI
	# Add administrative units with links to the graph
	print "Creating linked data from {0} {1} dataset".format(AdmUnitType, country)
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		for i, row in enumerate(table):
			geometry = row[1]
			name = row[0].lower().replace(' ', '_')

			if AdmUnitType.lower() == "province":
				thing = URIRef('{0}{1}/province/{2}.html'.format( BaseURI, country, name ) )
				URIgeometry = URIRef('{0}{1}/province/{2}_geometry.html'.format( BaseURI, country, name ) )

				g.add( (thing, RDF.type, dbpedia.Province) )
			elif AdmUnitType.lower() == "municipality":
				thing = URIRef( '{0}{1}/municipality/{2}.html'.format( BaseURI, country, name ) )
				URIgeometry = URIRef( '{0}{1}/municipality/{2}_geometry.html'.format( BaseURI, country, name ) )

				g.add( (thing, RDF.type, dbpedia.Municipality) )

			g.add( (URIgeometry, RDF.type, geom.Geometry) )
			g.add( (thing, FOAF.name, Literal(row[0])) )
			g.add( (URIgeometry, RDFS.Datatype, geom.wktLiteral) )
			g.add( (URIgeometry, RDFS.Literal, Literal(geometry) ) )
			g.add( (thing, geom.hasGeometry, URIgeometry) )
			
			bar.update(i)
		
	#print g.serialize(format='turtle')

	# Write the graph to a RDF file in the turtle format
	g.serialize("{0}.ttl".format(outputFile), format='turtle')
	# print len(g.serialize(format='turtle'))
	return

# LandcoverTable2RDF takes a table with landcover data which all have a name and a geometry as input and stores it in an RDF file
def LandcoverTable2RDF(table):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

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

	try:
		# Check if the file already exist, in which case the new triples will be appended to it
		g.parse("{0}.ttl".format(outputFile), format="turtle")
		#print g.serialize(format='turtle')
		# print len(g.serialize(format='turtle'))
	except:
		pass
	
	global BaseURI

	print "Creating linked data from CORINE 2012 Legend"
	for key, value in CLC_legend.iteritems():
		# Linking URI as subclass of Landcover definition on DBPedia
		g.add( ( URIRef("{0}landcover/legend/CLC_{1}.html".format(BaseURI, key) ), RDFS.subClassOf , dbpedia.Land_cover ) )
		g.add( ( URIRef("{0}landcover/legend/CLC_{1}.html".format(BaseURI, key) ), FOAF.name , Literal(value) ) )

	print "Creating linked data from CORINE 2012 dataset"
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		for i, row in enumerate(table):
			ID, Landcover, geometry = row

			thing = URIRef("{0}landcover/{1}.html".format( BaseURI, ID ) )
			URIgeometry = URIRef("{0}landcover/{1}_geometry.html".format( BaseURI, ID ) )

			g.add( (thing, RDF.type, URIRef("{0}landcover/legend/CLC_{1}.html".format(BaseURI, Landcover) ) ) )
			g.add( (URIgeometry, RDFS.Datatype, geom.wktLiteral) )
			g.add( (URIgeometry, RDFS.Literal, Literal(geometry) ) )
			g.add( (thing, geom.hasGeometry, URIgeometry) )

			g.serialize("{0}.ttl".format(outputFile), format='turtle')

			if i % 100 == 0:
				bar.update(i)

	return

if (__name__ == "__main__"):

# Create linked data of provinces
	NL_provinces = getData("Masterthesis", "nl_provinces", "postgres", "")
	AdminUnitTable2RDF(NL_provinces, 'Netherlands', 'province')
	BE_provinces = getData("Masterthesis", "be_provinces", "postgres", "")
	AdminUnitTable2RDF(BE_provinces, 'Belgium', 'province')

# Create linked data of municipalities
	# NL_municipalities = getData("Masterthesis", "nl_municipalities", "postgres", "")
	# AdminUnitTable2RDF(NL_municipalities, 'Netherlands', 'municipality')
	# BE_municipalities = getData("Masterthesis", "be_munacipalities", "postgres", "")
	# AdminUnitTable2RDF(BE_municipalities, 'Belgium', 'municipality')	

# Create linked data of landcover
	Landcover = getData("Masterthesis", "corine_nl_be", "postgres", "", False)
	LandcoverTable2RDF(Landcover)

