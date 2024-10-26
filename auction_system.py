import json
import hashlib
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import secrets
import base64

# Secure storage for auctions and users
class AuctionStore:
    def __init__(self):
        self.auctions = {}
        self.users = {}
        self.sessions = {}
        self._lock = threading.Lock()

    def create_auction(self, item, start_price, end_time, seller):
        auction_id = secrets.token_urlsafe(16)
        with self._lock:
            self.auctions[auction_id] = {
                'item': item,
                'start_price': float(start_price),
                'current_price': float(start_price),
                'end_time': float(end_time),
                'seller': seller,
                'bids': [],
                'winner': None
            }
        return auction_id

    def place_bid(self, auction_id, bidder, amount):
        with self._lock:
            if auction_id not in self.auctions:
                return False, "Auction not found"
            
            auction = self.auctions[auction_id]
            if time.time() > auction['end_time']:
                return False, "Auction has ended"
                
            if float(amount) <= auction['current_price']:
                return False, "Bid must be higher than current price"
                
            auction['bids'].append({
                'bidder': bidder,
                'amount': float(amount),
                'time': time.time()
            })
            auction['current_price'] = float(amount)
            return True, "Bid placed successfully"

    def register_user(self, username, password):
        with self._lock:
            if username in self.users:
                return False, "Username already exists"
            
            salt = secrets.token_hex(16)
            hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
            
            self.users[username] = {
                'salt': salt,
                'password_hash': hashed_password
            }
            return True, "User registered successfully"

    def authenticate_user(self, username, password):
        if username not in self.users:
            return False
            
        user = self.users[username]
        hashed_password = hashlib.sha256((password + user['salt']).encode()).hexdigest()
        return hashed_password == user['password_hash']

# HTTP Request Handler
class AuctionHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.auction_store = auction_store
        super().__init__(*args, **kwargs)

    def do_GET(self):
        routes = {
            '/auctions': self.get_auctions,
            '/auction': self.get_auction
        }
        
        path = urllib.parse.urlparse(self.path).path
        if path in routes:
            routes[path]()
        else:
            self.send_error(404)

    def do_POST(self):
        routes = {
            '/register': self.register_user,
            '/login': self.login_user,
            '/create_auction': self.create_auction,
            '/bid': self.place_bid
        }
        
        path = urllib.parse.urlparse(self.path).path
        if path in routes:
            routes[path]()
        else:
            self.send_error(404)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def get_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode())

    def get_auctions(self):
        active_auctions = {
            id: auction for id, auction in self.auction_store.auctions.items()
            if auction['end_time'] > time.time()
        }
        self.send_json_response({'auctions': active_auctions})

    def get_auction(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auction_id = params.get('id', [None])[0]
        
        if not auction_id or auction_id not in self.auction_store.auctions:
            self.send_json_response({'error': 'Auction not found'}, 404)
            return
            
        self.send_json_response({'auction': self.auction_store.auctions[auction_id]})

    def register_user(self):
        data = self.get_post_data()
        success, message = self.auction_store.register_user(
            data['username'],
            data['password']
        )
        status = 200 if success else 400
        self.send_json_response({'message': message}, status)

    def login_user(self):
        data = self.get_post_data()
        if self.auction_store.authenticate_user(data['username'], data['password']):
            session_token = secrets.token_urlsafe(32)
            self.auction_store.sessions[session_token] = data['username']
            self.send_json_response({'token': session_token})
        else:
            self.send_json_response({'error': 'Invalid credentials'}, 401)

    def create_auction(self):
        data = self.get_post_data()
        token = self.headers.get('Authorization')
        
        if not token or token not in self.auction_store.sessions:
            self.send_json_response({'error': 'Unauthorized'}, 401)
            return
            
        seller = self.auction_store.sessions[token]
        auction_id = self.auction_store.create_auction(
            data['item'],
            data['start_price'],
            time.time() + float(data['duration']),
            seller
        )
        self.send_json_response({'auction_id': auction_id})

    def place_bid(self):
        data = self.get_post_data()
        token = self.headers.get('Authorization')
        
        if not token or token not in self.auction_store.sessions:
            self.send_json_response({'error': 'Unauthorized'}, 401)
            return
            
        bidder = self.auction_store.sessions[token]
        success, message = self.auction_store.place_bid(
            data['auction_id'],
            bidder,
            data['amount']
        )
        status = 200 if success else 400
        self.send_json_response({'message': message}, status)

# Initialize the auction store
auction_store = AuctionStore()

# Start the server
def run_server(port=8000):
    server = HTTPServer(('localhost', port), AuctionHandler)
    print(f'Starting server on port {port}...')
    server.serve_forever()

if __name__ == '__main__':
    run_server()