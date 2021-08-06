import base64
from http.server import BaseHTTPRequestHandler


class AuthRequestHandler(BaseHTTPRequestHandler):
    def verify_auth(self):
        if self.config['auth']:
            ok = False
            if 'Authorization' in self.headers:
                auth = base64.b64encode(f'{self.config["username"]}:{self.config["password"]}'.encode()).decode()
                correct = f'Basic {auth}'
                if self.headers['Authorization'] == correct:
                    ok = True

            if not ok:
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="OpenSwitcher"')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('Authentication required'.encode())
                return False
        return True
