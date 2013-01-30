import cherrypy

class App():
    @cherrypy.expose
    def index(self):
        return open('assets/html/index.html')

    def upload(self, dex, ping, yfd):
        out = """<html>
        <body>
            dex length: %s<br />
            dex filename: %s<br />
            dex mime-type: %s
        </body>
        </html>"""

        # Although this just counts the file length, it demonstrates
        # how to read large files in chunks instead of all at once.
        # CherryPy reads the uploaded file into a temporary file;
        # dex.file.read reads from that.
        size = 0
        while True:
            data = dex.file.read(8192)
            if not data:
                break
            size += len(data)

        return out % (size, dex.filename, dex.content_type)
    upload.exposed = True

if __name__ == '__main__':

    cherrypy.quickstart(App(), '/', 'app.conf')