from django.test import TestCase, tag
from django.apps import apps as django_apps

from edc_sync.test_mixins import SyncTestSerializerMixin

from edc_sync.models import OutgoingTransaction

from ..sync_models import sync_models

from .test_mixins import HouseholdMixin


class TestNaturalKey(SyncTestSerializerMixin, HouseholdMixin, TestCase):

    def test_natural_key_attrs(self):
        self.sync_test_natural_key_attr('household')

    def test_get_by_natural_key_attr(self):
        self.sync_test_get_by_natural_key_attr('household')

    def test_sync_test_natural_keys(self):
        household_structure = self.make_household_structure_ready_for_enumeration()
        household_structure = self.add_failed_enumeration_attempt(household_structure)
        verbose = False
        model_objs = []
        completed_model_objs = {}
        completed_model_lower = []
        for outgoing_transaction in OutgoingTransaction.objects.all():
            if outgoing_transaction.tx_name in sync_models:
                model_cls = django_apps.get_app_config('household').get_model(
                    outgoing_transaction.tx_name.split('.')[1])
                obj = model_cls.objects.get(pk=outgoing_transaction.tx_pk)
                if outgoing_transaction.tx_name in completed_model_lower:
                    continue
                model_objs.append(obj)
                completed_model_lower.append(outgoing_transaction.tx_name)
        completed_model_objs.update({'household': model_objs})
        self.sync_test_natural_keys(completed_model_objs, verbose=verbose)
