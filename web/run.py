#!/usr/bin/env python3
"""
Production-ready runner for the Flask web application
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from web.app import create_app
from web.config import config

def main():
    """Main entry point for the web application"""
    
    # Get environment configuration
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(env, config['default'])
    
    # Create application
    app = create_app(config_class)
    config_class.init_app(app)
    
    # Get server configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    
    print(f"🚀 Starting German Thesis Correction Tool Web Server")
    print(f"🌍 Environment: {env}")
    print(f"📍 Server: http://{host}:{port}")
    print(f"🔧 Debug: {'ON' if debug else 'OFF'}")
    
    if env == 'production':
        print("⚠️  For production deployment, use a WSGI server like Gunicorn:")
        print(f"   gunicorn -w 4 -b {host}:{port} web.run:app")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )

if __name__ == '__main__':
    main()