import logging

from zope.interface import implements
from repoze.who.interfaces import IAuthenticator

from ckan.model import User
from ckan.lib.authenticator import UsernamePasswordAuthenticator

log = logging.getLogger(__name__)


class UsernamePasswordAuthenticator(UsernamePasswordAuthenticator):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        if not ('login' in identity and 'password' in identity):
            return None

        login = identity['login']
        user = User.by_name(login)
        if user is None:
          user = User.by_email(login)[0]

        if user is None:
            log.debug('Login failed - username %r not found', login)
        elif not user.is_active():
            log.debug('Login as %r failed - user isn\'t active', login)
        elif not user.validate_password(identity['password']):
            log.debug('Login as %r failed - password not valid', login)
        else:
            return user.name

        return None

