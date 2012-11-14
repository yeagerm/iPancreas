import cherrypy

class App():
	@cherrypy.expose
	def index(self):
		return open('assets/html/index.html')

if __name__ == '__main__':

    cherrypy.quickstart(App(), '/', 'app.conf')