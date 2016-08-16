#!/usr/bin/python
import os.path
import logging
import handlers
import tornado.ioloop

from tornado.options import define
from tornado.options import options
from tornado.web import StaticFileHandler

define("port", default="8000")

this_dir = os.path.dirname(__file__)

def main():

    tornado.options.parse_command_line()
    print tornado.options.options.port

    this_dir = os.path.dirname(__file__)

    app_handlers = [
            (r'/',          handlers.Index),
            (r'/login',     handlers.Login),
            (r'/register',  handlers.Register),
            (r'/logout',    handlers.Logout),
            (r'/upload',    handlers.Upload),
            (r'/open',      handlers.Open),
            (r'/delete',    handlers.Delete),
            (r'/docs/(.*)', handlers.ServeFile, {'path':
                '/home/jallison/TaxAssessor/website/uploads/'}),
            (r'/close',     handlers.Close),
            (r'/inspect',   handlers.InspectReads),
            (r'/saveSet',   handlers.SaveSet),
            (r'/getSet',    handlers.GetSetList),
            (r'/compare',   handlers.CompareSets),
            (r'/getCoverage',   handlers.GetCoverage),
            (r'/filterGene',   handlers.FilterGene),
            (r'/exportSeqData',   handlers.ExportSeqData),
            (r'/uploadReadFile', handlers.UploadReadFile),
            (r'/deleteReadFile', handlers.DeleteReadFile),
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
            (r'/(.+)',      handlers.ServeReports)
    ]

    options = { 'debug':            True,
                'template_path':    os.path.join(this_dir,'templates'),
                'static_path':      os.path.join(this_dir,'static'),
                'cookie_secret':    "2sH6$OurX;v-{S?Llo7r+cL}PJH-!v",
                'xsrf_cookies':     True,
                'login_url':        '/login'
    }

    app = handlers.TaxAssessor(app_handlers,**options)
    app.listen(tornado.options.options.port,max_buffer_size=(4*1024**3))

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
