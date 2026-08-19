import urllib.request
import urllib.parse
import json

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="num_classes"\r\n\r\n'
    '6\r\n'
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="file"; filename="test.csv"\r\n'
    'Content-Type: text/csv\r\n\r\n'
    'a,b\n1,2\r\n'
    '--' + boundary + '--\r\n'
)

req = urllib.request.Request('http://localhost:8000/api/datasets/upload')
req.add_header('Content-Type', 'multipart/form-data; boundary=' + boundary)
try:
    response = urllib.request.urlopen(req, body.encode('utf-8'))
    print(response.read().decode())
except Exception as e:
    print(e)
