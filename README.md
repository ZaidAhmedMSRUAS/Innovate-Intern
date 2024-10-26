# Secure Online Auction System

A secure auction system implemented in Python using only standard library components. The system includes user authentication, secure password storage, and real-time bidding functionality.

## Features

- User registration and authentication with secure password hashing
- Create and manage auctions
- Real-time bidding system
- Session-based security
- Concurrent auction handling
- RESTful API endpoints

## API Endpoints

### Authentication
- POST `/register` - Register a new user
- POST `/login` - Login and receive a session token

### Auctions
- GET `/auctions` - List all active auctions
- GET `/auction?id={auction_id}` - Get specific auction details
- POST `/create_auction` - Create a new auction
- POST `/bid` - Place a bid on an auction

## Security Features

- Password hashing with salt using SHA-256
- Session-based authentication
- Thread-safe operations
- Secure random token generation
- Input validation and sanitization

## Usage

1. Start the server:
   ```bash
   python auction_system.py
   ```

2. The server will start on port 8000

3. Use the API endpoints to interact with the system