import requests
from lxml import etree

def Request(url):
	# Parameters we're interested in:
	organisation = False
	costs = False
	acccesConstraints = False
	minTime = False

	featureofinterest = {} # contains all the features of interest and their location
	observableProperty = [] # list of all observable properties
	offerings = {} # An offering is the equivalent of a layer in a WMS. It contains information on which sensors observe a specific observable property. 

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
	for section in tree:
		if "serviceidentification" in section.tag.lower():
			for info in section:
				# print "		->		"+info.tag
				if "fees" in info.tag.lower():
						costs = info.text
				elif "accessconstraints" in info.tag.lower():
					acccesConstraints = info.text
			
		elif "serviceprovider" in section.tag.lower():
			for details in section:
				if "providername" in details.tag.lower():
					organisation = details.text 

		elif "operationsmetadata" in section.tag.lower():
			for info in section:
				if "getobservation" in info.attrib['name'].lower():
					for each in info:
						try:
							if "temporalfilter" in each.attrib['name'].lower():
								minTime = each[0][0][0].text

							if "featureofinterest" in each.attrib['name'].lower():
								for allowedvalues in each:
									for feature in allowedvalues:
										if feature.text in featureofinterest:
											print feature.text, 'already exists'
										else:
											featureofinterest[feature.text] = {}

							if "observedproperty" in each.attrib['name'].lower():
								for allowedvalues in each:
									for obsProperty in allowedvalues:
										observableProperty.append(obsProperty.text)

						except:
							pass

		elif "contents" in section.tag.lower():
			for offering in section[0]:
				if "observationoffering" in offering[0].tag.lower():
					for info in offering[0]:
						if "identifier" in info.tag.lower():
							currentOffering = info.text
						elif "observableproperty" in info.tag.lower():
							obsProperty = info.text
					offerings[currentOffering] = {'obsProperty': obsProperty}


		# else:
		# 	print section.tag.lower()


	#----------------------------------------------------------------------#
	# GetFeatureOfInterest
	#----------------------------------------------------------------------#

	GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest'.format(url)
	

	r = requests.get(GetFeatureOfInterest)
	
	tree = etree.fromstring(r.content)
	for section in tree:
		if 'exception' in section.tag.lower():	
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

				featureofinterest[currentFOI]['coords'] = [coords, CRS]
			else:
				print info.tag

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
	print "Offerings: \n", offerings, "\n"


	return organisation, costs, acccesConstraints, minTime, featureofinterest, observableproperty, offerings

if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	Request('http://sos.irceline.be/sos?')
# 	Requesting the Dutch SOS from RIVM
	Request('http://inspire.rivm.nl/sos/eaq/service?')

