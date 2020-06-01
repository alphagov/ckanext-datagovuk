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


class DGUUserRequestResetView(_UserBeforeRequestMixin, RequestResetView):
    """
    A RequestResetView that will also allow password to be reset by
    providing email address, not just username
    """
    def post(self):
        context, data_dict = self._prepare()
        id = data_dict[u'id']

        context = {u'model': model, u'user': g.user}
        user_obj = None
        try:
            logic.get_action(u'user_show')(context, data_dict)
            user_obj = context[u'user_obj']
        except logic.NotFound:
            # Try getting the user by email
            user_accounts = model.User.by_email(id)
            if user_accounts:
                user_obj = user_accounts[0]

        if not user_obj:
            # Try searching the user
            if id and len(id) > 2:
                user_list = logic.get_action(u'user_list')(context, {
                    u'id': id
                })
                if len(user_list) == 1:
                    # This is ugly, but we need the user object for the
                    # mailer,
                    # and user_list does not return them
                    data_dict[u'id'] = user_list[0][u'id']
                    logic.get_action(u'user_show')(context, data_dict)
                    user_obj = context[u'user_obj']
                elif len(user_list) > 1:
                    h.flash_error(_(u'"%s" matched several users') % (id))
                else:
                    h.flash_error(_(u'No such user: %s') % id)
            else:
                h.flash_error(_(u'No such user: %s') % id)

        if user_obj:
            try:
                # FIXME: How about passing user.id instead? Mailer already
                # uses model and it allow to simplify code above
                mailer.send_reset_link(user_obj)
                h.flash_success(
                    _(u'Please check your inbox for '
                      u'a reset code.'))
                return h.redirect_to(u'home.index')
            except mailer.MailerException as e:
                h.flash_error(_(u'Could not send reset link: %s') %
                              text_type(e))
        return self.get()


def me():
    """
    A slight variation on the default me() which prefers `dashboard.datasets`
    over `dashboard.index`
    """
    route = u'dashboard.datasets' if g.user else u'user.login'
    return redirect_to(route)
