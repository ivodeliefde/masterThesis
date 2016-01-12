from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2
import os

LocalhostPath = "D:/URI_test"

def getData(dbms_name, table, user, password):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

	# Retrieve the names and geometries of the provinces
	cur.execute("select name, ST_astext(geom) from {0};".format(table))
	table = cur.fetchall()

	return table

def createURI(name, location, value=""):
	# create a basic HTML file which will serve as an URI in the form of an URL
	content = "<!DOCTYPE html><html><head><title>{0}</title></head><body><h1>{0}</h1><p>{1}</p></body></html>".format(name, value)
	
	global LocalhostPath
	filename = "{0}/{1}/{2}.html".format(LocalhostPath, location, name)
	# Check if the directories already exist. If not create the directories to store the files in.
	if not os.path.exists(os.path.dirname(filename)):
		print "Create URI directories"
		os.makedirs(os.path.dirname(filename))

	# Store the HTML file in the proper location on the server and host it to establish the new URI
	with open(filename, 'w') as f:
		f.write(content)
	f.close()

	return


# table2RDF takes a table with spatial objects which have a name and a geometry as input and creates an RDF file from it
def table2RDF(table, country, AdmUnitType):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

	# Create a graph
	g = Graph()
	
	try:
		# Check if the file already exist, in which case the new triples will be appended to it
		g.parse("test.ttl", format="turtle")
		#print g.serialize(format='turtle')
		# print len(g.serialize(format='turtle'))
	except:
		pass

	# Add administrative units with links to the graph
	for row in table:
		geometry = row[1]
		if AdmUnitType.lower() == "province":
			name = row[0].lower().replace(' ', '_')
			# Create the URI to be used for the administrative unit 
			createURI( name , "{0}/province".format( country ) )
			# Create RDF link that uses the new URI
			thing = URIRef('http://localhost:8000/{0}/province/{1}'.format( country, name ) )
			# Create the URI to be used for the geometry of the administrative unit 
			createURI( "{0}_geometry".format(name) ,"{0}/province".format( country), geometry )
			# Create RDF link that uses the new URI
			geometry = URIRef('http://localhost:8000/{0}/province/{1}_geometry'.format(country, name ) )
			# Add links to graph
			g.add( (thing, RDF.type, dbpedia.Province) )
		elif AdmUnitType.lower() == "municipality":
			name = row[0].lower()
			# Create the URI to be used for the administrative unit 
			createURI( name , "{0}/municipality".format( country ) )
			# Create RDF link that uses the new URI
			thing = URIRef( 'http://localhost:8000/{0}/municipality/{1}'.format( country, name ) )
			# Create the URI to be used for the geometry of the administrative unit 
			createURI( "{0}_geometry".format(name)  , "{0}/municipality".format( country ), geometry )
			# Create RDF link that uses the new URI
			geometry = URIRef( 'http://localhost:8000/{0}/municipality/{1}_geometry'.format( country, name ) )
			# Create links
			g.add( (thing, RDF.type, dbpedia.Municipality) )
		g.add( (geometry, RDF.type, geom.Geometry) )
		g.add( (thing, FOAF.name, Literal(row[0])) )
		g.add( (geometry, RDFS.Datatype, geom.wktLiteral) )
		g.add( (geometry, RDFS.Literal, Literal(geometry) ) )
		g.add( (thing, geom.hasGeometry, geometry) )
		
	#print g.serialize(format='turtle')

	# Write the graph to a RDF file in the turtle format
	g.serialize("test.ttl", format='turtle')
	print len(g.serialize(format='turtle'))
	return

if (__name__ == "__main__"):
	provinces = getData("Masterthesis", "nl_provinces","postgres", "")
	table2RDF(provinces, 'Netherlands', 'province')
	
