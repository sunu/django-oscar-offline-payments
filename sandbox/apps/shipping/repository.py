from decimal import Decimal as D

from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.repository import Repository as CoreRepository


class Repository(CoreRepository):
    def get_available_shipping_methods(
                self, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method instances for a given
        basket, address etc.
        """
        methods = [Free(), FixedPrice(D('10.00'), D('10.00'))]
        return methods
