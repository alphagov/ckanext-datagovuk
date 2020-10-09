from ckan.lib import mailer
import ckan.model as model

log = __import__('logging').getLogger(__name__)


def send_password_alert(user):
    try:
        body = "Your password has been changed, if you haven't done it yourself, let us know"
        mailer.mail_user(user, 'Your data.gov.uk publisher password has changed', body)
        log.info('Sent email to alert password change')
    except mailer.MailerException as e:
        log.error('Could not send email to alert password change: %s' % unicode(e))
