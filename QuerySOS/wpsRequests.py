import requests
from lxml import etree
from datetime import datetime, timedelta

def Request(url):
	# Parameters we're interested in:
	organisation = False
	costs = False
	acccesConstraints = False
	minTime = False
	version = [] 
	responseformat = []

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

							elif "featureofinterest" in each.attrib['name'].lower():
								for allowedvalues in each:
									for feature in allowedvalues:
										if feature.text in featureofinterest:
											print feature.text, 'already exists'
										else:
											featureofinterest[feature.text] = {}

							elif "observedproperty" in each.attrib['name'].lower():
								for allowedvalues in each:
									for obsProperty in allowedvalues:
										observableProperty.append(obsProperty.text)

							elif "responseformat" in each.attrib['name'].lower():
								for format in each[0]:
									responseformat.append(format.text)

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
					offerings[currentOffering] = {'obsProperty': [obsProperty]}
					offerings[currentOffering]['FOI'] = []
					offerings[currentOffering]['procedure'] = []


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
				featureofinterest[currentFOI]['procedure'] = []
				featureofinterest[currentFOI]['obsProperty'] = []
			# else:
			# 	print info.tag

	#----------------------------------------------------------------------#
	# GetObservation
	#----------------------------------------------------------------------#

	# A small amount of data will be requested from every offering to retrieve 
	# some missing links that are not always found in the previous documents: 
	# Which features of interest are observed by which offering and with which
	# procedure.  

	yesterday = datetime.now() - timedelta(hours=6)
	yesterday = yesterday.isoformat()

	# for key in offerings:
	# key = 'NL.RIVM.AQ/STA-NL00929/8'
	key = '62101 - TT_._99920'
	responseformat = 'http://www.opengis.net/om/2.0'
	GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&offering={1}&responseformat={2}&temporalFilter=om:resultTime,after,{3}'.format(url, key, responseformat, yesterday)
	r = requests.get(GetObservation)

	print GetObservation

	tree = etree.fromstring(r.content)
	for featureMember in tree:
		if "observationdata" in featureMember.tag.lower():
			for observation in featureMember[0]:
					
					if "procedure" in observation.tag.lower():
						for data in observation.attrib:
							if 'href' in data.lower():
								procedureKey = data
						if observation.attrib[procedureKey] not in offerings[key]['procedure']:
							offerings[key]['procedure'].append(observation.attrib[procedureKey])
					
					elif "featureofinterest" in observation.tag.lower():
						for data in observation.attrib:
							if 'href' in data.lower():
								FOIKey = data

						if observation.attrib[FOIKey] not in offerings[key]['FOI']:
							offerings[key]['FOI'].append(observation.attrib[FOIKey])

						for each in offerings[key]['procedure']:
							if each not in featureofinterest[observation.attrib[FOIKey]]['procedure']:
								featureofinterest[observation.attrib[FOIKey]]['procedure'].append(each)
						for each in offerings[key]['obsProperty']:
							if each not in featureofinterest[observation.attrib[FOIKey]]['obsProperty']:
								featureofinterest[observation.attrib[FOIKey]]['obsProperty'].append(each)

	print offerings[key]
	print featureofinterest[FOIKey]


	#----------------------------------------------------------------------#
	# Results
	#----------------------------------------------------------------------#

	print "\n	Provided by: {0}".format(organisation)
	print "	Costs: {0}".format(costs)
	print "	Acccess constraints: {0}".format(acccesConstraints)
	print "	Data available from: {0}".format(minTime)
	print "	Available versions: {0}".format(version)
	print "	Available response formats: {0}".format(responseformat)
	print "	There are {0} features of interest".format(len(featureofinterest))
	print "	There are {0} observable properties".format(len(observableProperty)) 
	print "\nFeatures of interest: \n",featureofinterest
	print "Offerings: \n", offerings, "\n"

	return organisation, costs, acccesConstraints, minTime, featureofinterest, observableProperty, offerings

if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	Request('http://sos.irceline.be/sos?')
# 	Requesting the Dutch SOS from RIVM
	Request('http://inspire.rivm.nl/sos/eaq/service?')



