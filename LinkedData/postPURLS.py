import requests
from lxml import etree

def postPURLbatch(fileName, username, password):
	XML = open(fileName,'r').read().replace('\n','')
	# print type(XML)
	tree = etree.fromstring(XML)
	nsm = tree.nsmap

	session = requests.Session()

	payload = {'id': username, 'passwd': password}
	r = session.post('http://localhost:8099/admin/login/login-submit.bsh', data=payload)

	for purl in tree.findall('.//purl',nsm):
		data = u'type={0}&target={1}&maintainers='.format(purl[1].text, purl[3][0].text)
		url = u'http://localhost:8099/admin/purl{}'.format(purl[0].text)
		print url
		print data
		headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'content-length':'{0}'.format(len(XML)), }

		r = session.post(url, data=data, headers=headers)
		print r
		print r.text

if (__name__ == "__main__"): 
	postPURLbatch('purlBatch.xml', 'admin', 'password')