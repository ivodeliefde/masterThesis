import requests
from xml.etree import ElementTree

# Requesting the Belgian SOS IRCELINE
r = requests.get('http://sos.irceline.be/sos?service=SOS&request=GetCapabilities')

# Requesting the Dutch SOS from RIVM
# r = requests.get('http://inspire.rivm.nl/sos/eaq/service?service=AQD&version=1.0.0&request=GetCapabilities')


tree = ElementTree.fromstring(r.content)

if (__name__ == "__main__"):
	print(r.url)
	# print type(r)
	# print type(tree)
	# print tree[4][0][0][0][5][0][0].tag, tree[4][0][0][0][5][0][0].text
	# print tree[4][0][0][0][5][0][1].tag, tree[4][0][0][0][5][0][1].text

	upperCorner = set()
	for level1 in tree:
		# print "level 1", level1.tag
		for level2 in level1:
			# print "level 2", level2.tag
			for level3 in level2:
				# print "level 3", level3.tag
				for level4 in level3:
					# print "level 4", level4.tag, 
					for level5 in level4:
						# print "level 5", level5.tag
						for level6 in level5:
							# print "level 6", level6.tag, level6.attrib
							for level7 in level6:
								if ('upperCorner' in level7.tag):
									upperCorner.add(level7.text)
									# print level7.text
	print 'no. of unique envelope-upperCorners: ', len(upperCorner)
	for each in upperCorner:
		print each


								