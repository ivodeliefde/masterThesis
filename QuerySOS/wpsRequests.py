import requests
from lxml import etree
from datetime import datetime, timedelta

class SOS:

	def __init__(self, url, name="", organisation="", costs="", acccesConstraints="", version="", responseFormat=[]):
		# Information that needs to be retrieved from the SOS
		self.name = name
		self.organisation = organisation
		self.costs = costs 
		self.acccesConstraints = acccesConstraints
		self.version = version
		self.responseFormat = responseFormat 

		self.log("SOS instance created")
		# Check if the user input URL is correct
		url = self.checkURL(url)
		
		if url == False:
			return "The input URL is invalid. Could not create SOS instance"
		else:
			# Store the approved url
			self.url = url

		return self.Request()

	def checkURL(self, url):
		if type(url) != str:
			self.log("input URL is not of type string")
			try:
				url = str(url)
				self.log("Input URL converted to string")
			except:
				self.log("Could not convert input URL to string")
				return False

		if url[:4] != "http":
			self.log("Input URL is not an HTTP address")
			return False 

		self.log("URL '{0}' is valid".format(url))

		return url

	def Request(self):
		# observableProperty = {}  --> each item should be dictionary as well, containing 'procedure', 'offerings' and 'FOI'

		featureofinterest = {} # contains all the features of interest and their location
		observableProperty = [] # list of all observable properties
		offerings = {} # An offering is the equivalent of a layer in a WMS. It contains information on which sensors observe a specific observable property. 

		#-------------------------------------------------------------------------------#
		# Get Capabilities --> find the general metadata and the offerings per procedure
		#-------------------------------------------------------------------------------#

		# Retrieve the GetCapabilities document
		GetCapabilities = '{0}service=SOS&request=GetCapabilities'.format(self.url)
		
		try:
			r = requests.get(GetCapabilities)
		except:
			self.log("Could not send the request: {0}".format(GetCapabilities))

		# Print the request URL
		self.log("Get request: {0}".format(GetCapabilities))

		# Store the retrieved document as an etree object
		tree = etree.fromstring(r.content)

		# Loop trough the capabilities document 
		for section in tree:
			# Section: service identification 
			if "serviceidentification" in section.tag.lower():
				for info in section:
					# print "		->		"+info.tag
					if "fees" in info.tag.lower():
							self.costs = info.text
					elif "accessconstraints" in info.tag.lower():
						self.acccesConstraints = info.text
			
			# Section: service provider
			elif "serviceprovider" in section.tag.lower():
				for details in section:
					if "providername" in details.tag.lower():
						self.organisation = details.text 

			# Section: operations metadata		
			elif "operationsmetadata" in section.tag.lower():
				for info in section:
					if "getobservation" in info.attrib['name'].lower():
						for each in info:
							try:
								if "temporalfilter" in each.attrib['name'].lower():
									self.minTime = each[0][0][0].text

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
										self.responseFormat.append(format.text)

							except:
								pass
			
			# Section: contents
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


		#-------------------------------------------------------------------------------#
		# GetFeatureOfInterest --> retrieve the features-of-interest per procedure
		#-------------------------------------------------------------------------------#

		# GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest'.format(self.url)
		

		# r = requests.get(GetFeatureOfInterest)
		
		# tree = etree.fromstring(r.content)
		# for section in tree:
		# 	if 'exception' in section.tag.lower():	
		# 		GetFeatureOfInterest += '&featureOfInterest=allFeatures'
		# 		r = requests.get(GetFeatureOfInterest)
		# 		tree = etree.fromstring(r.content)
		# 		break

		# self.log("Get request: {0}".format(GetFeatureOfInterest))

		# for featureMember in tree:
		# 	currentFOI = False
		# 	for info in featureMember:
		# 		if 'sf_spatialsamplingfeature' in info.tag.lower():
		# 			for attributes in info:
		# 				if 'identifier' in attributes.tag.lower():
		# 					currentFOI = attributes.text
		# 				elif 'shape' in attributes.tag.lower():
		# 					coords = attributes[0][0].text
		# 					CRS = attributes[0][0].attrib['srsName']

		# 			featureofinterest[currentFOI]['coords'] = [coords, CRS]
		# 			featureofinterest[currentFOI]['procedure'] = []
		# 			featureofinterest[currentFOI]['obsProperty'] = []
		# 		# else:
		# 		# 	print info.tag


		#-------------------------------------------------------------------------------#
		# Results
		#-------------------------------------------------------------------------------#

		# print "	There are {0} features of interest".format(len(featureofinterest))
		# print "	There are {0} observable properties".format(len(observableProperty)) 
		# print "\nFeatures of interest: \n",featureofinterest
		# print "Offerings: \n", offerings, "\n"

		return

	def printInformation(self):
		results = "Information for {0}\n\tProvided by: {1}\n\tCosts: {2}\n\tAcccess constraints: {3}\n\tData available since: {4}\n\tSupported version: {5}\n\tSupported response formats: {6}\n".format(self.name, self.organisation, self.costs, self.acccesConstraints, self.minTime, self.version, self.responseFormat)
		print results 
		
		return


	def log(self, event):
		with open('log_{0}'.format(self.name), 'a') as f:
			f.write("at {0}\t-->\t{1}\n".format(datetime.now().isoformat(), event))
		
		return



if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	IRCELINE_SOS = SOS('http://sos.irceline.be/sos?')
	IRCELINE_SOS.printInformation()

# 	Requesting the Dutch SOS from RIVM
 	RIVM_SOS = SOS('http://inspire.rivm.nl/sos/eaq/service?')
 	RIVM_SOS.printInformation()
	
	