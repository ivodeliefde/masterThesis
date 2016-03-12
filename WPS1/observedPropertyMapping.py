import requests
from rdflib import Graph

endpoint = "http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/Store"


def sendMappingScriptToEndpoint(mappingscript):
	global endpoint


	payload = {'dbname': 'endpoint', 'username': 'Ivo', 'password':'gps', 'port':'5432', 'hostname':'localhost', 'dbengine':'postgis'}
	session = requests.Session()

	r = session.post(endpoint, data={'view':'HTML', 'format':'Turtle', 'url':(mappingscript), 'fromurl':'Store from URI' }) 

	# if str(r) != '<Response [200]>':
	# 	print "Response: {0}".format(r)
	# 	print query
	# 	print r.text


	return

if __name__ == "__main__":
	sendMappingScriptToEndpoint("file:///H:\Ivo\Geomatics\Year 2\Thesis\Thesis Template\WPS1\observedPropertyMapping.ttl")