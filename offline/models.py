from __future__ import unicode_literals
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

from oscar.core.loading import get_model

PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventType = get_model('order', 'PaymentEventType')


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
    __original_status = None

    notes = models.TextField(null=True, blank=True)

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

    def __init__(self, *args, **kwargs):
        super(OfflineTransaction, self).__init__(*args, **kwargs)
        self.__original_status = self.status

    def save(self, *args, **kwargs):
        if self.status != self.__original_status:
            if self.status in ("failed", "settled", "received"):
                event_type, _ = PaymentEventType.objects.get_or_create(
                    name="Initiated"
                )
                payment_event = PaymentEvent.objects.get(
                    event_type=event_type, reference=self.txnid
                )
                order = payment_event.order
                event_type, _ = PaymentEventType.objects.get_or_create(
                    name=self.status.capitalize()
                )
                PaymentEvent(
                    order=order, amount=self.amount,
                    event_type=event_type,
                    reference=self.txnid
                ).save()
        super(OfflineTransaction, self).save(*args, **kwargs)
        self.__original_status = self.status
