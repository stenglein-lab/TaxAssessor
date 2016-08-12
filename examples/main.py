#!/usr/bin/python
import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options
import os.path

define("port", default=2222, help="run on the given port", type=int)
settings = {
        "static_path": os.path.join(os.path.dirname(__file__), 
            "/home/jallison/TaxAssessor/html/"),
        "debug":True
        }

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("home.html")

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/",tornado.web.StaticFileHandler,dict(path=settings['static_path']))
        ], **settings) 
    http_server = tornado.httpserver.HTTPServer(app) 
    http_server.listen(options.port) 
    tornado.ioloop.IOLoop.instance().start()
