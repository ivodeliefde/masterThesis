import requests
from lxml import etree
from datetime import datetime, timedelta

try:
	import cPickle as pickle
except:
	import pickle

class SOS:

	def __init__(self, url, name="", organisation="", costs="", accessConstraints="", version=set(), responseFormat=set()):
		self.error = False

		# Information that needs to be retrieved from the SOS
		self.name = name
		self.organisation = organisation
		self.costs = costs 
		self.accessConstraints = accessConstraints
		self.version = version
		self.responseFormat = responseFormat 
		self.procedure = {} # contains dictionary instances with structure 'ID': {'offerings': [], 'obsProperty': '...' ,'FOI': set() }
		self.featureofinterest = {} # contains dictionary instance with structure 'ID': {'coords': [coords, crs], 'offerings': [] }

		
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
		print GetCapabilities

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
		# self.minTime = tree.find(".//ows:Parameter[@name='temporalFilter']/ows:AllowedValues/ows:Range/ows:MinimumValue", nsm).text
		
		versions = tree.findall('.//ows:ServiceTypeVersion', nsm)
		for version in versions:
			self.version.add(version.text)

		FOI = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='featureOfInterest']/ows:AllowedValues", nsm)
		for feature in FOI:
			if feature.text in featureofinterest:
				print feature.text, 'already exists'
			else:
				self.featureofinterest[feature.text] = {}
		
		procedures = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='procedure']/ows:AllowedValues", nsm)
		for procedure in procedures:
			self.procedure[procedure.text] = {'offerings': [], 'obsProperty': '', 'FOI': set()}

		responseformat = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='responseFormat']/ows:AllowedValues", nsm)
		for format in responseformat:
			self.responseFormat.add(format.text)

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
		

		GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest'.format(self.url)

		r = requests.get(GetFeatureOfInterest)
		
		tree = etree.fromstring(r.content)
		for section in tree:
			if 'exception' in section.tag.lower():	
				GetFeatureOfInterest += '&featureOfInterest=allFeatures'
				r = requests.get(GetFeatureOfInterest)
				tree = etree.fromstring(r.content)
				break

		print GetFeatureOfInterest

		self.log("Get request: {0}".format(GetFeatureOfInterest))

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

					self.featureofinterest[currentFOI]['coords'] = [coords, CRS]
					self.featureofinterest[currentFOI]['offerings'] = []
				# else:
				# 	print info.tag

		#-------------------------------------------------------------------------------#
		# GetObservation --> retrieve small amounts of data to link a procedure to a FOI
		#-------------------------------------------------------------------------------#
			
		# HAVE TO CHANGE THIS TO DESCRIBESENSOR REQUESTS!

		yesterday = (datetime.now() - timedelta(days=1)).isoformat()
		temporalFilter = '&temporalFilter=om:resultTime,after,{0}'.format(yesterday)

		# i = 0 

		for procedure in self.procedure:

			for offering in self.procedure[procedure]['offerings']:
				
				GetObservation = '{0}service=SOS\&version=2.0.0\&request=DescribeSensor\&procedure={1}\&proceduredescriptionformat=http://www.opengis.net/sensorML/2.0'.format(self.url, procedure)
				temporalFilterUsed = True
				GetObservationWtempfilter = GetObservation + temporalFilter
				try:
					r = requests.get(GetObservationWtempfilter)
					tree = etree.fromstring(r.content)
				except:
					self.log("Could not send the request with temporal filter: {0}".format(GetObservationWtempfilter))
					r = requests.get(GetObservation)
					tree = etree.fromstring(r.content)
					temporalFilterUsed = False

				nsm = tree.nsmap

				# Print the request URL
				if temporalFilterUsed:
					self.log("Get request: {0}".format(GetObservation+temporalFilter))
					print GetObservationWtempfilter
				else:
					self.log("Get request: {0}".format(GetObservation))
					print GetObservation

				# print etree.tostring(tree, pretty_print=True)
				
				try:
					FOI = tree.findall(".//om:featureOfInterest", nsm)
					# print "no. om:featureofinterest",len(FOI), FOI
					for feature in FOI:
						try:
							for attribute, value in feature.attrib.iteritems():
								if value in self.featureofinterest:
									self.procedure[procedure]['FOI'].add(value)
									self.featureofinterest[value]['offerings'].append(offering)
									continue
	
						except:
							pass
						
						self.log("featureofinterest not in attributes")
						# print "featureofinterest not in attributes"

						value = tree.findall(".//om:featureOfInterest/sams:SF_SpatialSamplingFeature/gml:identifier", nsm)
						# print "no. gml:identifier", len(value)
						if len(value) > 0:
							for each in value:
								self.procedure[procedure]['FOI'].add(each.text)
								self.featureofinterest[each.text]['offerings'].append(offering)
								# print "new: ", self.procedure[procedure]['FOI']
						# else:
							# print "no observations available"

				except:
					self.log("no observations available")
					# print "not an observations available"
				
			
			
			# if i > 3:
			# 	return
			# else:
			# 	i += 1

		return

	def printInformation(self):
		# prints the variables of a SOS instance
		if self.error == False:
			results = "Information for {0}\n\tProvided by: {1}\n\tCosts: {2}\n\tAccess constraints: {3}\n\tSupported version: {4}\n\tSupported response formats: {5}\n".format(self.name, self.organisation, self.costs, self.accesConstraints, self.version, self.responseFormat)
			print results 
		else:
			print "I'm in a state of error!"
		
		return


	def log(self, event):
		# logs an event to the log.txt file
		with open('log.txt', 'a') as f:
			f.write("at {0}\t-->\t{1}\n".format(datetime.now().isoformat(), event))

		return

	def store(self):
		# stores the SOS instance and it's variables
		pickle.dump(self, open( "{0}.p".format(self.name), "wb" ) )

		return


if (__name__ == "__main__"):
# # 	Requesting the Dutch SOS from RIVM
 	RIVM_SOS = SOS('http://inspire.rivm.nl/sos/eaq/service?')
 	RIVM_SOS.store()
 	# RIVM_SOS = pickle.load(open( "RIVM SOS Service Air Quality.p", "rb") )
 	RIVM_SOS.printInformation()
 	print RIVM_SOS.procedure, "\n"
 	


# # 	Requesting the Belgian SOS IRCELINE	
	IRCELINE_SOS = SOS('http://sos.irceline.be/sos?')
	IRCELINE_SOS.store()
	# IRCELINE_SOS = pickle.load(open( "SOS of IRCEL - CELINE.p", "rb") )
	IRCELINE_SOS.printInformation()
	print IRCELINE_SOS.procedure
