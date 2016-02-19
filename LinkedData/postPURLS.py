# -*- coding: utf-8 -*-
import requests
from lxml import etree
import cgi
import unicodedata

endpoint = 'http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/'


def postPURLbatch(fileName, username, password):
	payload = {'id': username, 'passwd': password}
	session = requests.Session()
	r = session.post('http://localhost:8099/admin/login/login-submit.bsh', data=payload)

	with open(fileName,'r') as f:
		for line in f:
			XML = line.replace('\n','')
			tree = etree.fromstring(XML)
			nsm = tree.nsmap

			data = u'type={0}&target={1}&maintainers='.format(tree[1].text, tree[3][0].text)
			url = u'http://localhost:8099/admin/purl{}'.format(tree[0].text)
			# print url
			# print data
			headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'content-length':'{0}'.format(len(XML)), }

			r = session.post(url, data=data, headers=headers)
			# print r
			# print r.text
	return


def CreatePurls(UriList, purlBatch):
	global endpoint

	if UriList == 'open':
		with open(purlBatch,'w') as f:
			f.write('')
	else:
		purls = ''
		for each in UriList:
			each = unicodedata.normalize('NFKD', each).encode('ascii', 'ignore')
			cleanURI = cgi.escape(each)
			purls += u'<purl> <id>{0}</id> <type>303</type> <maintainers> <uid>IdeLiefde</uid> </maintainers> <target> <url>{1}Describe?view=HTML&amp;handle=download&amp;format=turtle&amp;submit=describe&amp;query=DESCRIBE%20&lt;{0}&gt;</url> </target> </purl>\n'.format(cleanURI, endpoint)
		with open(purlBatch,'a') as f:
			f.write(purls)

	return


if (__name__ == "__main__"): 
	postPURLbatch('purlBatch.xml', 'admin', 'password')