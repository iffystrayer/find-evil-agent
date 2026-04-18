#!/usr/bin/env python3
"""Quick launcher for Find Evil Agent web interface.

Usage:
    python launch_web.py
    python launch_web.py --port 17001
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from find_evil_agent.web.gradio_app import launch_app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Launch Find Evil Agent web interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=17000, help="Port to run on")
    parser.add_argument("--share", action="store_true", help="Create public share link")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print(f"🚀 Launching Find Evil Agent Web Interface...")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"⏹️  Press Ctrl+C to stop\n")

    launch_app(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        debug=args.debug
    )
