#!/usr/bin/python
import os.path
import logging
import handlers
import tornado.ioloop

from tornado.options import define, options


app_port = 2222


def main():

    this_dir = os.path.dirname(__file__)

    app_handlers = [
            (r'/',          handlers.Index),
            (r'/login',     handlers.Login),
            (r'/register',  handlers.Register),
            (r'/logout',    handlers.Logout)
    ]

    options = { 'debug':            True,
                'template_path':    os.path.join(this_dir,'templates'),
                'static_path':      os.path.join(this_dir,'static'),
                'cookie_secret':    "2sH6$OurX;v-{S?Llo7r+cL}PJH-!v",
                'xsrf_cookies':     True,
                'login_url':        '/login'
    }

    app = handlers.TaxAssessor(app_handlers,**options)
    app.listen(app_port)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
