from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF
import rdflib
import psycopg2

def getData(dbms_name, user, password):
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

	cur.execute("select provincien, ST_astext(geom) from provinces")
	table = cur.fetchall()
	return table

def table2RDF(table):
	RDF.type 
	# = rdflib.term.URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')

	geom = rdflib.Namespace("http://geovocab.org/geometry#")
	dbpedia = rdflib.Namespace("http://dbpedia/resource/")

	g = Graph()

	for province in provinces:
		name = Literal(province[0])
		geometry = Literal(province[1])
		g.add( (name, RDF.type, dbpedia.Province) )
		g.add( (geometry, RDF.type, geom.MultiPolygon) )
		g.add( (name, geom.Geometry, geometry) )
	g.serialize("test.rdf", format='turtle')


if (__name__ == "__main__"):
	provinces = getData("Masterthesis", "postgres", "")
	table2RDF(provinces)

