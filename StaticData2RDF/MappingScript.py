from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2

def getData(dbms_name, user, password):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

	# Retrieve the names and geometries of the provinces
	cur.execute("select provincien, ST_astext(geom) from provinces")
	table = cur.fetchall()

	return table

def table2RDF(table):
	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

	# Create a graph
	g = Graph()

	# Add provinces with links to the graph
	for province in provinces:
		# Name and geometry should still get URIs assigned to them
		thing = BNode() #Literal(province[0])
		geometry = BNode() #Literal(province[1])
		# Create links
		g.add( (thing, RDF.type, dbpedia.Province) )
		g.add( (geometry, RDF.type, geom.Geometry ) )
		g.add( (thing, FOAF.name, Literal(province[0])) )
		g.add( (geometry, RDFS.Datatype, geom.wktLiteral) )
		g.add( (thing, geom.hasGeometry, Literal(province[1])) )
		
	print g.serialize(format='turtle')

	# Write the graph to a RDF file in the turtle format
	g.serialize("test.ttl", format='turtle')


if (__name__ == "__main__"):
	provinces = getData("Masterthesis", "postgres", "")
	table2RDF(provinces)

