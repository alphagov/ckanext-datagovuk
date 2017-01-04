def validate_password(self, password):
    from ckan.model.user import User

    if not password or not self.password:
        return False

    # Is it a Drupal password hash?
    if self.password[:3] in ('$S$', '$H$', '$P$'):
        # yes, upgrade it
        return _verify_password_and_upgrade_from_drupal7(self, password)

    # Fall back to existing logic
    return User.validate_password_original(self, password)


def _verify_password_and_upgrade_from_drupal7(self, password):
    if isinstance(password, unicode):
        password = password.encode('ascii', 'ignore')

    from ckanext.datagovuk.lib.drupal_password import user_check_password
    if user_check_password(password, self.password):
        #we've passed the old drupal check, upgrade our password
        self._set_password(password)
        self.save()
        return True
    else:
        return False

import ckan.model.user
ckan.model.user.User.validate_password_original = ckan.model.user.User.validate_password
ckan.model.user.User.validate_password = validate_password