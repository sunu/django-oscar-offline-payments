from django.views import generic

from .. import models


class TransactionListView(generic.ListView):
    model = models.OfflineTransaction
    template_name = 'offline/dashboard/transaction_list.html'
    context_object_name = 'transactions'


class TransactionDetailView(generic.DetailView):
    model = models.OfflineTransaction
    template_name = 'offline/dashboard/transaction_detail.html'
    context_object_name = 'txn'
