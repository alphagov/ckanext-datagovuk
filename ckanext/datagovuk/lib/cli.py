import csv
import sys

from ckan.lib.cli import CkanCommand, query_yes_no
from ckan.lib.mailer import create_reset_key

class PasswordResetsCommand(CkanCommand):
    '''Resets the passwords of all users

     Resets the passwords of all users and generates a CSV
     containing a list of of email->resetkeys

        paster passwords_reset <output-filename>
    '''
    summary = __doc__.split('\n')[0]
    usage = '\n'.join(__doc__.split('\n')[1:])
    max_args = None
    min_args = 1

    def command(self):
        output_file = self.args[0]

        msg = "Are you sure you want to reset ALL of the user passwords?"

        confirm = query_yes_no(msg, default='no')
        if confirm == 'no':
            sys.stderr.write("Aborting...\n")
            sys.exit(1)

        self._load_config()
        import ckan.model as model
        import ckan.lib.search as search

        with open(output_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'email-address', 'reset-key'])

            for user in model.User.all():
                create_reset_key(user)
                user.save()

                writer.writerow([user.id, user.email, user.reset_key])