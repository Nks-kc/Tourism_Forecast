import sys, json, hmac, hashlib, base64, time, urllib.request, urllib.error
sys.path.insert(0, 'backend')

secret = 'change-this-jwt-secret-in-production'
payload = {'user_id': 1, 'username': 'test', 'email': 'test@test.com', 'exp': int(time.time()) + 3600}

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

header = b64url(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
body_enc = b64url(json.dumps(payload).encode())
sig_input = f'{header}.{body_enc}'.encode()
sig = b64url(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
token = f'{header}.{body_enc}.{sig}'

print("=== Testing /predict/country ===")
req = urllib.request.Request(
    'http://localhost:5000/predict/country',
    data=json.dumps({'country': 'Australia', 'horizon': 3}).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=60)
    d = json.loads(resp.read())
    print('STATUS: OK', list(d.get('predictions',{}).keys()))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, json.loads(e.read()))

print("\n=== Testing /predict (total) ===")
req2 = urllib.request.Request(
    'http://localhost:5000/predict',
    data=json.dumps({'horizon': 3}).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
    method='POST'
)
try:
    resp2 = urllib.request.urlopen(req2, timeout=60)
    d2 = json.loads(resp2.read())
    print('STATUS: OK', list(d2.get('predictions',{}).keys()))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, json.loads(e.read()))
