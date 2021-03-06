# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, lurl
from tg import request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.exceptions import HTTPFound
from tg import predicates, session
from puzzlesweb import model
from puzzlesweb.model import DBSession, User, Competition
from tgext.admin.controller import AdminController
from puzzlesweb.config.app_cfg import AdminConfig

from puzzlesweb.lib.base import BaseController
from puzzlesweb.controllers.error import ErrorController
from puzzlesweb.controllers.puzzles import PuzzlesController
from puzzlesweb.controllers.grade import GradeAnswersController
from puzzlesweb.controllers.competitions import CompetitonsController
from puzzlesweb.controllers.pref import PreferencesController

import datetime

__all__ = ['RootController']

class RootController(BaseController):
    """
    The root controller for the puzzlesweb application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    admin = AdminController(model, DBSession, config_type=AdminConfig)
    error = ErrorController()
    puzzles = PuzzlesController()
    grade = GradeAnswersController()
    competitions = CompetitonsController()
    pref = PreferencesController()

    def _before(self, *args, **kw):
        tmpl_context.project_name = "puzzlesweb"

    @expose('puzzlesweb.templates.index')
    def index(self):
        """Handle the front-page."""
        competitions = DBSession.query(Competition).order_by(Competition.open_time)
        active = competitions\
                .filter(Competition.open_time <= datetime.datetime.now())\
                .filter(Competition.close_time > datetime.datetime.now()).all()
        upcoming = competitions\
                .filter(Competition.open_time > datetime.datetime.now()).all()

        return dict(page='index', active=active, upcoming=upcoming)

    @expose('puzzlesweb.templates.login')
    def login(self, came_from=lurl('/'), failure=None, login=''):
        """Start the user login."""
        if failure is not None:
            if failure == 'user-not-found':
                flash(_('User not found'), 'error')
            elif failure == 'invalid-password':
                flash(_('Invalid Password'), 'error')

        login_counter = request.environ.get('repoze.who.logins', 0)
        if failure is None and login_counter > 0:
            flash(_('Wrong credentials'), 'warning')

        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from, login=login)

    @expose()
    def post_login(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)

        # Do not use tg.redirect with tg.url as it will add the mountpoint
        # of the application twice.
        return HTTPFound(location=came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        return HTTPFound(location=came_from)

