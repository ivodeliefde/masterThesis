import requests
from lxml import etree
from datetime import datetime, timedelta

class SOS:

	def __init__(self, url, name="", organisation="", costs="", accessConstraints="", version="", responseFormat=[]):
		self.error = False

		# Information that needs to be retrieved from the SOS
		self.name = name
		self.organisation = organisation
		self.costs = costs 
		self.accessConstraints = accessConstraints
		self.version = version
		self.responseFormat = responseFormat 
		self.procedure = {} # contains dictionary instances with structure 'ID': {'offerings': [], 'obsProperty': '...' ,'FOI': [] }
		self.featureofinterest = {} # contains dictionary instance with structure 'ID': {'coords': [], 'CRS': '...' }

		
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
		nsm = tree.nsmap

		# Check for errors
		if len(tree.findall('.//ows:Exception', nsm)) >= 1:
			print 'The server responded with an error message'
			error = etree.tostring(tree, pretty_print=True)
			self.log('ERROR url: {0} \n response:\n{1}'.format(GetCapabilities, etree.tostring(tree, pretty_print=True)))
			self.error = True
			return

		# Retrieving information from the capabilities document 
		self.costs = tree.find('.//ows:Fees', nsm).text
		self.name = tree.find('.//ows:Title', nsm).text
		self.accesConstraints = tree.find('.//ows:AccessConstraints', nsm).text
		self.organisation = tree.find('.//ows:ProviderName', nsm).text	
		self.minTime = tree.find(".//ows:Parameter[@name='temporalFilter']/ows:AllowedValues/ows:Range/ows:MinimumValue", nsm).text
		
		FOI = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='featureOfInterest']/ows:AllowedValues", nsm)
		for feature in FOI:
			if feature.text in featureofinterest:
				print feature.text, 'already exists'
			else:
				featureofinterest[feature.text] = {}
		
		procedures = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='procedure']/ows:AllowedValues", nsm)
		for procedure in procedures:
			self.procedure[procedure.text] = {'offerings': [], 'obsProperty': '', 'FOI': []}

		responseformat = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='responseFormat']/ows:AllowedValues", nsm)
		for format in responseformat:
			self.responseFormat.append(format.text)

		contents = tree.findall(".//sos:ObservationOffering", nsm)
		for offering in contents:
			currentOffering = offering.find('.//swes:identifier', nsm).text
			obsProperty = offering.find('.//swes:observableProperty', nsm).text
			procedure = offering.find('.//swes:procedure', nsm).text

			self.procedure[procedure]['offerings'].append(currentOffering)		
			if len(self.procedure[procedure]['obsProperty']) == 0: 
				self.procedure[procedure]['obsProperty'] = obsProperty	

		#-------------------------------------------------------------------------------#
		# GetFeatureOfInterest --> retrieve the features-of-interest per procedure
		#-------------------------------------------------------------------------------#
		
		for procedure in self.procedure:
			for offering in self.procedure[procedure]['offerings']:
				GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest&procedure={1}&offering={2}'.format(self.url, procedure, offering)
				
				try:
					r = requests.get(GetFeatureOfInterest)
				except:
					self.log("Could not send the request: {0}".format(GetCapabilities))
				
				# Print the request URL
				self.log("Get request: {0}".format(GetFeatureOfInterest))
				print "Get request: {0}".format(GetFeatureOfInterest)
				break







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
		if self.error == False:
			results = "Information for {0}\n\tProvided by: {1}\n\tCosts: {2}\n\tAccess constraints: {3}\n\tData available since: {4}\n\tSupported version: {5}\n\tSupported response formats: {6}\n".format(self.name, self.organisation, self.costs, self.accesConstraints, self.minTime, self.version, self.responseFormat)
			print results 
		
		return


	def log(self, event):
		with open('log.txt', 'a') as f:
			f.write("at {0}\t-->\t{1}\n".format(datetime.now().isoformat(), event))
		# pass
		return



if (__name__ == "__main__"):
# 	Requesting the Belgian SOS IRCELINE	
	IRCELINE_SOS = SOS('http://sos.irceline.be/sos?')
	IRCELINE_SOS.printInformation()

# # 	Requesting the Dutch SOS from RIVM
#  	RIVM_SOS = SOS('http://inspire.rivm.nl/sos/eaq/service?')
#  	RIVM_SOS.printInformation()