import http.server
import os
from http.server import SimpleHTTPRequestHandler
from io import BytesIO

from PIL import Image


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Check if the file exists
        if not os.path.exists(self.translate_path(self.path)):
            # File not found, send a blank 256x256 PNG image
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()

            # Create a blank PNG image
            blank_image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
            img_bytes = BytesIO()
            blank_image.save(img_bytes, format='PNG')
            self.wfile.write(img_bytes.getvalue())
        else:
            # If the file exists, serve it as usual
            super().do_GET()

if __name__ == '__main__':
    # Set the working directory to where your tiles are located
    tiles_directory = '../data/cubes_demo_output'
    os.chdir(tiles_directory)

    # Start the server
    http.server.test(HandlerClass=CORSRequestHandler, port=8080)
