from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2

def getData(dbms_name, table, user, password):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

	# Retrieve the names and geometries of the provinces
	cur.execute("select name, ST_astext(geom) from {0};".format(table))
	table = cur.fetchall()

	return table

# table2RDF takes a table with spatial objects which have a name and a geometry as input and creates an RDF file from it
def table2RDF(table, country, AdmUnitType):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

	# Create a graph
	g = Graph()
	
	try:
		g.parse("test.ttl", format="turtle")
		#print g.serialize(format='turtle')
		print len(g.serialize(format='turtle'))
	except:
		pass

	# Add provinces with links to the graph
	for row in table:
		if AdmUnitType.lower() == "province":
			# Name and geometry should still get URIs assigned to them
			thing = URIRef('http://example.com/{0}/province/{1}'.format(country, row[0].lower().replace(' ', '_') ) )
			geometry = URIRef('http://example.com/{0}/province/{1}#geometry'.format(country, row[0].lower() ).replace(' ', '_') )
			# Create links
			g.add( (thing, RDF.type, dbpedia.Province) )
		elif AdmUnitType.lower() == "municipality":
			# Name and geometry should still get URIs assigned to them
			thing = URIRef('http://example.com/{0}/municipality/{1}'.format(country, row[0].lower() ) )
			geometry = URIRef('http://example.com/{0}/municipality/{1}#geometry'.format(country, row[0].lower() ) )
			# Create links
			g.add( (thing, RDF.type, dbpedia.Municipality) )
		g.add( (geometry, RDF.type, geom.Geometry) )
		g.add( (thing, FOAF.name, Literal(row[0])) )
		g.add( (geometry, RDFS.Datatype, geom.wktLiteral) )
		g.add( (geometry, RDFS.Literal, Literal(row[1]) ) )
		g.add( (thing, geom.hasGeometry, geometry) )
		
	#print g.serialize(format='turtle')

	# Write the graph to a RDF file in the turtle format
	g.serialize("test.ttl", format='turtle')
	print len(g.serialize(format='turtle'))
	return

if (__name__ == "__main__"):
	provinces = getData("Masterthesis", "nl_provinces","postgres", "")
	table2RDF(provinces, 'Netherlands', 'province')

