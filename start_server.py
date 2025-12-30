#!/usr/bin/env python3
"""
GoldenIT Microsoft Entra v-1.2 - Server Startup Script
Starts the Flask web server
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize database if needed
print("Initializing database...")
from database import db
print("Database initialized successfully!")

# Start server
print("Starting GoldenIT Microsoft Entra Web Server...")
print("Access the admin panel at: http://localhost:5000")
print("Default credentials: admin / admin123")
print("\nPress Ctrl+C to stop the server")

from server import app
app.run(host='0.0.0.0', port=5000, debug=False)
