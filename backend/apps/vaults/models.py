from django.db import models


class RoleChoices(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    CONTRIBUTOR = 'CONTRIBUTOR', 'Contributor'
    VIEWER = 'VIEWER', 'Viewer'


ROLE_WEIGHTS = {
    RoleChoices.OWNER: 3,
    RoleChoices.CONTRIBUTOR: 2,
    RoleChoices.VIEWER: 1,
}
