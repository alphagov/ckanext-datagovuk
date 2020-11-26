from ckan import model

# to prevent all tables from being deleted
model.repo.tables_created_and_initialised = True
