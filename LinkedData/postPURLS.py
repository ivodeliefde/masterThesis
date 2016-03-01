# -*- coding: utf-8 -*-
import requests
from lxml import etree
import cgi
import unicodedata

endpoint = 'http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/'
lineCount = 0
fileCount = 0

def postPURLbatch(fileName, username, password):
	global fileCount

	payload = {'id': username, 'passwd': password}
	session = requests.Session()
	r = session.post('http://localhost:8099/admin/login/login-submit.bsh', data=payload)

	for i in range(fileCount+1):
		with open('{0}{1}.xml'.format(fileName, i),'r') as f:
			print 'open', i
			# for line in f:
				# XML = line.replace('\n','')
				# tree = etree.fromstring(XML)
				# nsm = tree.nsmap

				# data = u'type={0}&target={1}&maintainers='.format(tree[1].text, tree[3][0].text)
				# url = u'http://localhost:8099/admin/purl{}'.format(tree[0].text)
				# print url
				# print data
			data = f.read()
			url = 'http://localhost:8099/admin/purls'
			headers = {'Content-Type': 'application/XML; charset=UTF-8' }

			r = session.post(url, data=data, headers=headers)
			print r
			print r.text
	print 'Finished posting PURLS' 
	return


def CreatePurls(UriList, purlBatch):
	global endpoint
	global lineCount 
	global fileCount

	if UriList == 'open':
		root = etree.Element("purls")
		string = etree.tostring(root, pretty_print=True)
		with open( '{0}{1}.xml'.format(purlBatch,fileCount), 'w' ) as f:
			f.write(string)

	else:
		tree = etree.parse('{0}{1}.xml'.format(purlBatch,fileCount))
		root = tree.getroot()

		for each in UriList:
			each = unicodedata.normalize('NFKD', each).encode('ascii', 'ignore')

			purl = etree.Element( 'purl' ) 
			purl.attrib['id'] = each.replace('http://localhost:8099','')
			purl.attrib['type'] = '302'
			maint = etree.SubElement(purl, 'maintainers')
			etree.SubElement(maint, 'uid').text = 'admin'
			etree.SubElement(purl, 'target').attrib['url'] = "{0}Describe?view=HTML&handle=download&format=turtle&submit=describe&query=DESCRIBE <{1}>".format(endpoint, each)
			root.append( purl )

			lineCount += 1
		if lineCount > 100:
			string = etree.tostring(root, pretty_print=True)
			with open( '{0}{1}.xml'.format(purlBatch,fileCount), 'w' ) as f:
				f.write(string)

			fileCount += 1
			newRoot = etree.Element("purls")
			string = etree.tostring(newRoot, pretty_print=True)
			with open( '{0}{1}.xml'.format(purlBatch,fileCount), 'w' ) as f:
				f.write(string)
			lineCount = 0
		else:
			string = etree.tostring(root, pretty_print=True)
			with open( '{0}{1}.xml'.format(purlBatch,fileCount), 'w' ) as f:
				f.write(string)


	return


if (__name__ == "__main__"): 
	postPURLbatch('purlBatch.xml', 'admin', 'password')