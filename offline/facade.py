from __future__ import unicode_literals
from uuid import uuid4
import logging

from django.conf import settings

from .models import OfflineTransaction as Transaction
from .exceptions import OfflineError

logger = logging.getLogger('offline')


def start_offline_txn(basket, amount, payment_type, user=None, email=None):
    """
    Record the start of a transaction and calculate costs etc.
    """
    if basket.currency:
        currency = basket.currency
    else:
        currency = getattr(settings, 'OFFLINE_CURRENCY', 'INR')
    transaction = Transaction(
        user=user, amount=amount, currency=currency, status="initiated",
        basket_id=basket.id, txnid=uuid4().hex[:28], email=email,
        payment_type=payment_type
    )
    transaction.save()
    return transaction


def fetch_transaction_details(txn_id):
    try:
        txn = Transaction.objects.get(txnid=txn_id)
    except Transaction.DoesNotExist as e:
        logger.warning(
            "Unable to find transaction details for txnid %s: %s",
            txn_id, e)
        raise OfflineError
    return txn
