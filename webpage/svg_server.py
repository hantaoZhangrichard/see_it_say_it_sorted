"""
Main server entry point.
Imports the Flask app from routes and starts the server.
"""

import sys
import argparse
from routes import app


def config_argparser():
    """Configure command line argument parser"""
    parser = argparse.ArgumentParser(description='SVG Editor Server')
    parser.add_argument('-p', '--port', 
                       type=int,
                       default=8080,
                       help='Port number to run the server on (default: 8080)')
    return parser.parse_args()


def main():
    """
    Main entry point for the server application.
    Parses command line arguments and starts the Flask server.
    """
    args = config_argparser()

    try:
        port = int(args.port)
        if not 0 <= port <= 65535:
            print("Error: Port number must be between 0 and 65535.", file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print("Invalid port number", file=sys.stderr)
        sys.exit(1)

    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
