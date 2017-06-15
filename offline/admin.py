from django.contrib import admin
from . import models


class OfflineTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'txnid', 'status',
                    'payment_type', 'date_created',
                    'basket_id', 'email']
    readonly_fields = [
        'user',
        'amount',
        'currency',
        'txnid',
        'payment_type',
        'date_created',
        'basket_id',
        'email'
    ]

admin.site.register(models.OfflineTransaction, OfflineTransactionAdmin)
