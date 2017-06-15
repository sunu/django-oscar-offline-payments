from __future__ import unicode_literals
import logging

from django.views.generic import RedirectView, View
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from oscar.apps.payment.exceptions import UnableToTakePayment
from oscar.core.loading import get_class, get_model

from . import facade
from .exceptions import (
    EmptyBasketException, MissingShippingAddressException,
    MissingShippingMethodException, InvalidBasket, OfflineError)

# Load views dynamically
PaymentDetailsView = get_class('checkout.views', 'PaymentDetailsView')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')

ShippingAddress = get_model('order', 'ShippingAddress')
Country = get_model('address', 'Country')
Basket = get_model('basket', 'Basket')
Repository = get_class('shipping.repository', 'Repository')
Selector = get_class('partner.strategy', 'Selector')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')


Applicator = get_class('offer.applicator', 'Applicator')

logger = logging.getLogger('offline')


class PaymentView(CheckoutSessionMixin, View):
    """
    Show the offline payment page and record the start of a transaction.
    """

    template_name = 'offline/payment.html'

    def get(self, request, *args, **kwargs):
        try:
            self.payment_method = request.GET['payment_method']
            assert self.payment_method in ["DD", "CHEQUE", "ET", "MO"]
        except (KeyError, AssertionError):
            logger.warning("Missing or invalid GET params on payment page")
            messages.error(
                self.request,
                _("Unable to determine offline transaction type"))
            return HttpResponseRedirect(reverse('basket:summary'))
        try:
            basket = self.build_submission()['basket']
            if basket.is_empty:
                raise EmptyBasketException()
        except InvalidBasket as e:
            messages.warning(self.request, six.text_type(e))
            return reverse('basket:summary')
        except EmptyBasketException:
            messages.error(self.request, _("Your basket is empty"))
            return reverse('basket:summary')
        except MissingShippingAddressException:
            messages.error(
                self.request, _("A shipping address must be specified"))
            return reverse('checkout:shipping-address')
        except MissingShippingMethodException:
            messages.error(
                self.request, _("A shipping method must be specified"))
            return reverse('checkout:shipping-method')
        else:
            # Freeze the basket so it can't be edited while the customer is
            # making the payment
            basket.freeze()

            logger.info("Starting payment for basket #%s", basket.id)
            context = self._start_offline_txn(basket)
            return render(request, self.template_name, context)

    def _start_offline_txn(self, basket, **kwargs):
        """
        Record the start of a transaction.
        """
        if basket.is_empty:
            raise EmptyBasketException()
        order_total = self.build_submission()['order_total']
        user = self.request.user
        amount = order_total.incl_tax
        if self.request.user.is_authenticated():
            email = self.request.user.email
        else:
            email = self.build_submission()['order_kwargs']['guest_email']
            user = None
        txn = facade.start_offline_txn(
            basket, amount, self.payment_method, user, email
        )
        context = {
            "basket": basket,
            "amount": int(amount),
            "txn_id": txn.txnid,
            "payment_method": self.payment_method,
            "store": settings.OFFLINE_STORE,
            "etrans_details": settings.OFFLINE_ETRANS_DETAILS
        }
        return context


class CancelResponseView(RedirectView):
    permanent = False

    def get(self, request, *args, **kwargs):
        basket = get_object_or_404(Basket, id=kwargs['basket_id'],
                                   status=Basket.FROZEN)
        basket.thaw()
        logger.info("Payment cancelled - basket #%s thawed", basket.id)
        return super(CancelResponseView, self).get(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        messages.error(self.request, _("Offline transaction cancelled"))
        return reverse('basket:summary')


class SuccessResponseView(PaymentDetailsView):
    preview = True

    @property
    def pre_conditions(self):
        return []

    def get(self, request, *args, **kwargs):
        """
        Fetch details about the successful transaction and place
        an order.
        """
        try:
            self.txn_id = request.GET['txn_id']
        except KeyError:
            # Manipulation - redirect to basket page with warning message
            logger.warning("Missing GET params on success response page")
            messages.error(
                self.request,
                _("Unable to determine transaction details"))
            return HttpResponseRedirect(reverse('basket:summary'))

        try:
            self.txn = facade.fetch_transaction_details(self.txn_id)
        except OfflineError:
            messages.error(
                self.request,
                _("A problem occurred while processing payment - "
                  "please try again later"))
            return HttpResponseRedirect(reverse('basket:summary'))

        # Reload frozen basket which is specified in the URL
        kwargs['basket'] = self.load_frozen_basket(kwargs['basket_id'])
        if not kwargs['basket']:
            logger.warning(
                "Unable to load frozen basket with ID %s", kwargs['basket_id'])
            messages.error(
                self.request,
                _("No basket was found that corresponds to your  transaction"))
            return HttpResponseRedirect(reverse('basket:summary'))

        logger.info(
            "Basket #%s - showing preview payment id %s",
            kwargs['basket'].id, self.txn.txnid)

        basket = kwargs['basket']
        submission = self.build_submission(basket=basket)
        return self.submit(**submission)

    def load_frozen_basket(self, basket_id):
        # Lookup the frozen basket that this txn corresponds to
        try:
            basket = Basket.objects.get(id=basket_id, status=Basket.FROZEN)
        except Basket.DoesNotExist:
            return None
        # Assign strategy to basket instance
        if Selector:
            basket.strategy = Selector().strategy(self.request)
        # Re-apply any offers
        Applicator().apply(request=self.request, basket=basket)
        return basket

    def build_submission(self, **kwargs):
        submission = super(
            SuccessResponseView, self).build_submission(**kwargs)
        # Pass the user email so it can be stored with the order
        submission['order_kwargs']['guest_email'] = self.txn.email
        # Pass PP params
        submission['payment_kwargs']['txn'] = self.txn
        return submission

    def handle_payment(self, order_number, total, **kwargs):
        """
        Capture the money from the initial transaction.
        """
        txn = kwargs["txn"]
        # Record payment source and event
        source_type, is_created = SourceType.objects.get_or_create(
            name=txn.payment_type)
        source = Source(source_type=source_type,
                        currency=txn.currency,
                        amount_allocated=txn.amount,
                        amount_debited=txn.amount,
                        reference=txn.txnid)
        self.add_payment_source(source)
        self.add_payment_event('Initiated', txn.amount,
                               reference=txn.txnid)
