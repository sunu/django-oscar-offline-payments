from django.forms import ModelForm

from ..models import OfflineTransaction


class TransactionUpdateForm(ModelForm):
    class Meta:
        model = OfflineTransaction
        fields = ['status', 'notes']
