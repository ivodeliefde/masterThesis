import requests
from lxml import etree

def Request(url):
	# Parameters we're interested in:
	organisation = False
	costs = False
	acccesConstraints = False
	sensors = {} # dictionary with structure: sensor[ID]: [phenomenon, location, etc.]

	# Retrieve the GetCapabilities document
	GetCapabilities = '{0}service=SOS&request=GetCapabilities'.format(url)
	r = requests.get(GetCapabilities)

	# Print the request URL
	print GetCapabilities

	# Store the retrieved document as an etree object
	tree = etree.fromstring(r.content)

	# Loop trough the first level of the document to find the branches that we need 
	for level1 in tree:
		if "serviceidentification" in level1.tag.lower():
			for info in level1:
				# print "		->		"+info.tag
				if "fees" in info.tag.lower():
						costs = info.text
				elif "accessconstraints" in info.tag.lower():
					acccesConstraints = info.text
			
		elif "serviceprovider" in level1.tag.lower():
			for details in level1:
				if "providername" in details.tag.lower():
					organisation = details.text 




	print "Provided by: {0}".format(organisation)
	print "Costs: {0}".format(costs)
	print "Acccess constraints: {0}".format(acccesConstraints)

	return

if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	Request('http://sos.irceline.be/sos?')
# 	Requesting the Dutch SOS from RIVM
	# Request('http://inspire.rivm.nl/sos/eaq/service?')
								