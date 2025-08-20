#!/usr/bin/env python3
"""
Minimal test server to verify Cloud Run deployment works
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def root():
    return {'status': 'ok', 'message': 'Test server is running'}

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'test-server'}

if __name__ == '__main__':
    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"🚀 Starting test server on {host}:{port}")
    print(f"🌍 Environment PORT: {os.environ.get('PORT', 'not set')}")
    
    app.run(host=host, port=port, debug=False) 