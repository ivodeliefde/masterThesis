import requests

session = requests.Session()

payload = {'id': 'admin', 'passwd': 'password'}
r = session.post('http://localhost:8099/admin/login/login-submit.bsh', data=payload)

headers = {'Content-Type': 'application/xml'}
XML = open('purlBatch.xml').read()

r = session.post('http://localhost:8099/admin/purl', data=XML, headers=headers)
print r
print r.text