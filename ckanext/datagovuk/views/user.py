from six import text_type

from ckan.common import g
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.logic as logic
import ckan.model as model
from ckan.plugins.toolkit import _, redirect_to, abort
from ckan.views.user import (
    before_request,
    EditView,
    RegisterView,
    RequestResetView,
)

from ckanext.datagovuk.schema import user_edit_form_schema


class _UserBeforeRequestMixin(object):
    """
    Use with MethodViews to ensure ckan.views.user.before_request is
    called before processing requests when view is not a member of the
    ckan.views.user.user blueprint to which it is normally applied.
    """
    def dispatch_request(self, *args, **kwargs):
        ret = before_request()
        return ret or super(_UserBeforeRequestMixin, self).dispatch_request(*args, **kwargs)


class DGUUserEditView(_UserBeforeRequestMixin, EditView):
    """
    An EditView that adds extra password policy policing
    """
    def _prepare(self, *args, **kwargs):
        context, id_ = super(DGUUserEditView, self)._prepare(*args, **kwargs)
        context[u"schema"] = user_edit_form_schema()
        return context, id_


class DGUUserRegisterView(_UserBeforeRequestMixin, RegisterView):
    """
    A RegisterView that disables the POST view
    """
    def post(self, *args, **kwargs):
        abort(403)
