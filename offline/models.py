from __future__ import unicode_literals
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible


def generate_id():
    return uuid4().hex[:28]


@python_2_unicode_compatible
class OfflineTransaction(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    CHEQUE, DD, MO, ET = "CHEQUE", "DD", "MO", "ET"

    payment_type = models.CharField(max_length=32, choices=(
        (CHEQUE, "Cheque"), (DD, "Demand Draft"), (MO, "Money Order"),
        (ET, "Electronic Transfer")
    ))

    email = models.EmailField(null=True, blank=True)
    txnid = models.CharField(
        max_length=32, db_index=True, default=generate_id
    )
    basket_id = models.CharField(
        max_length=12, null=True, blank=True, db_index=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True,
                                 blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)

    INITIATED, RECEIVED, SETTLED, FAILED = (
        "initiated", "received", "settled", "failed")
    status = models.CharField(max_length=32, choices=(
        (INITIATED, INITIATED), (RECEIVED, RECEIVED), (SETTLED, SETTLED),
        (FAILED, FAILED)
    ))

    class Meta:
        ordering = ('-date_created',)
        app_label = 'offline'

    @property
    def is_successful(self):
        return self.status == self.SETTLED

    @property
    def is_pending(self):
        return self.status in (self.INITIATED, self.RECEIVED)

    @property
    def is_failed(self):
        return self.status == self.FAILED

    def __str__(self):
        return 'offline payment (%s): %s' % (self.payment_type, self.txnid)
