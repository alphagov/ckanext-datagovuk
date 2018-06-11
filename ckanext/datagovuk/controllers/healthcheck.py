from ckan.controllers.group import GroupController

class HealthcheckController(GroupController):
    def healthcheck(self):
        return "OK"
