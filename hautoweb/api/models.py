from django.db import models
from hautoweb.l10n import _

class ApiPerms(models.Model):
    class Meta:
        permissions = [
            ("monitor", _("Monitoring"))
        ]

