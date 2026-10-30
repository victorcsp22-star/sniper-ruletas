import requests
import lxml.html

r = requests.get('https://ruletactiva.com.ve/', timeout=10)
doc = lxml.html.fromstring(r.text)
print("Title:", doc.xpath('//title/text()'))
links = doc.xpath('//a/@href')
print("Links:", links[:15])
tables = doc.xpath('//table')
print("Tables:", len(tables))
