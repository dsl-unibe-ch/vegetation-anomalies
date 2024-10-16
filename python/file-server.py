import http.server
import os
from http.server import SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    # Set the working directory to where your tiles are located
    tiles_directory = '/home/viktor/Work/Projects/UniBe/GIUB/vegetation-anomalies/vegetation-anomalies/data/cubes_demo_output'
    os.chdir(tiles_directory)

    # Start the server
    http.server.test(HandlerClass=CORSRequestHandler, port=8080)
