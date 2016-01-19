import requests
from lxml import etree

def Request(url):
	# Parameters we're interested in:
	organisation = False
	costs = False
	acccesConstraints = False
	minTime = False

	featureofinterest = {}
	observableProperty = []

	sensors = {} # dictionary with structure: sensor[ID]: [phenomenon, location, etc.]


	print "Get requests:"

	#----------------------------------------------------------------------#
	# Get Capabilities
	#----------------------------------------------------------------------#

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

		elif "operationsmetadata" in level1.tag.lower():
			for info in level1:
				if "getobservation" in info.attrib['name'].lower():
					for each in info:
						try:
							if "temporalfilter" in each.attrib['name'].lower():
								minTime = each[0][0][0].text

							if "featureofinterest" in each.attrib['name'].lower():
								for allowedvalues in each:
									for feature in allowedvalues:
										featureofinterest[feature.text] = []

							if "observedproperty" in each.attrib['name'].lower():
								for allowedvalues in each:
									for obsProperty in allowedvalues:
										observableProperty.append(obsProperty.text)

						except:
							pass

						
		# else:
		# 	print level1.tag


	#----------------------------------------------------------------------#
	# GetFeatureOfInterest
	#----------------------------------------------------------------------#

	GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest'.format(url)
	

	r = requests.get(GetFeatureOfInterest)
	
	tree = etree.fromstring(r.content)
	for level1 in tree:
		if 'exception' in level1.tag.lower():	
			GetFeatureOfInterest += '&featureOfInterest=allFeatures'
			r = requests.get(GetFeatureOfInterest)
			tree = etree.fromstring(r.content)
			break

	print GetFeatureOfInterest

	for featureMember in tree:
		currentFOI = False
		for info in featureMember:
			if 'sf_spatialsamplingfeature' in info.tag.lower():
				for attributes in info:
					if 'identifier' in attributes.tag.lower():
						currentFOI = attributes.text
					elif 'shape' in attributes.tag.lower():
						coords = attributes[0][0].text
						CRS = attributes[0][0].attrib['srsName']

			featureofinterest[currentFOI].extend([coords, CRS])
			# else:
			# 	print info.tag

	#----------------------------------------------------------------------#
	# DescribeSensor
	#----------------------------------------------------------------------#

	#----------------------------------------------------------------------#
	# Results
	#----------------------------------------------------------------------#

	print "\n	Provided by: {0}".format(organisation)
	print "	Costs: {0}".format(costs)
	print "	Acccess constraints: {0}".format(acccesConstraints)
	print "	Data available from: {0}".format(minTime)
	print "	There are {0} features of interest".format(len(featureofinterest))
	print "	There are {0} observable properties".format(len(observableProperty))
	print 
	print "features of interest: \n",featureofinterest

	return

if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	# Request('http://sos.irceline.be/sos?')
# 	Requesting the Dutch SOS from RIVM
	Request('http://inspire.rivm.nl/sos/eaq/service?')

# http://sos.irceline.be/sos?REQUEST=GetFeatureOfInterest&service=SOS&version=2.0.0&featureOfInterest=allFeatures
# http://inspire.rivm.nl/sos/eaq/service?REQUEST=GetFeatureOfInterest&service=SOS&version=2.0.0&featureOfInterest=NL.RIVM.AQ/SPO_F-NL00131_00046_101_101