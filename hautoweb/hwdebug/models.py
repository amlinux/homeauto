from django.db import models
from hautoweb.l10n import _

class ProcessPerms(models.Model):
    class Meta:
        permissions = [
            ("demo", _("Demo scenarios"))
        ]
