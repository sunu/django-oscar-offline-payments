from django.views import generic
from django.shortcuts import redirect

from .. import models
from . import forms


class TransactionListView(generic.ListView):
    model = models.OfflineTransaction
    template_name = 'offline/dashboard/transaction_list.html'
    context_object_name = 'transactions'


class TransactionDetailView(generic.DetailView):
    model = models.OfflineTransaction
    template_name = 'offline/dashboard/transaction_detail.html'
    context_object_name = 'txn'

    def get_context_data(self, **kwargs):
        context = super(
            TransactionDetailView, self
        ).get_context_data(**kwargs)
        context['form'] = forms.TransactionUpdateForm(instance=self.object)
        return context

    def post(self, request, pk):
        txn = models.OfflineTransaction.objects.get(pk=pk)
        form = forms.TransactionUpdateForm(request.POST, instance=txn)
        if form.is_valid():
            form.save()
        return redirect("offline-detail", pk=pk)
