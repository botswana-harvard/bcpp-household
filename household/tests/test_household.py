from dateutil.relativedelta import relativedelta
from model_mommy import mommy

from django.test import TestCase, tag

from plot.models import Plot

from ..constants import (
    NO_HOUSEHOLD_INFORMANT, ELIGIBLE_REPRESENTATIVE_ABSENT,
    ELIGIBLE_REPRESENTATIVE_PRESENT, REFUSED_ENUMERATION)
from ..exceptions import HouseholdAssessmentError
from ..forms import HouseholdLogEntryForm
from ..models import (
    Household, HouseholdLogEntry, HouseholdRefusal,
    HouseholdStructure, HouseholdLog)

from .mixin import HouseholdMixin


class TestHousehold(HouseholdMixin, TestCase):

    def test_creates_household_structure(self):
        """Asserts household structure instances are created when households are created."""
        plot = self.make_confirmed_plot(household_count=2)
        # each household needs 3 household_structures
        # based on example_survey.surveys and survey.AppConfig
        self.assertEqual(HouseholdStructure.objects.filter(household__plot=plot).count(), 6)

    def test_deletes_household_structure(self):
        """Asserts deletes household structure instances households are deleted."""
        plot = self.make_confirmed_plot(household_count=2)
        self.assertEqual(Household.objects.filter(plot=plot).count(), 2)
        for household in Household.objects.filter(plot=plot):
            self.assertEqual(HouseholdStructure.objects.filter(household=household).count(), 3)
        plot.household_count = 1
        plot.save()
        self.assertEqual(Household.objects.filter(plot=plot).count(), 1)
        for household in Household.objects.filter(plot=plot):
            self.assertEqual(HouseholdStructure.objects.filter(household=household).count(), 3)

    def test_cannot_delete_household_with_household_log_entry(self):
        """Asserts PROTECT will prevent plot from deleting existing households
        on save."""

        household_structure = self.make_household_structure(
            household_count=5, attempts=1)
        plot = household_structure.household.plot
        self.assertEqual(plot.household_count, 5)
        self.assertEqual(HouseholdLogEntry.objects.filter(
            household_log__household_structure__household__plot=plot).count(), 5)

        # try removing households
        plot.household_count = 1
        plot.save()

        # assert deletion failed
        plot = Plot.objects.get(pk=plot.pk)
        self.assertEqual(HouseholdLogEntry.objects.filter(
            household_log__household_structure__household__plot=plot).count(), 5)
        self.assertEqual(Household.objects.filter(plot=plot).count(), 5)

        # assert plot value was not changed
        self.assertEqual(plot.household_count, 5)

    def test_cannot_only_delete_households_without_household_log_entry(self):
        household_structure = self.make_household_structure(
            household_count=3, attempts=1)
        plot = household_structure.household.plot
        self.assertEqual(plot.household_count, 3)

        self.assertEqual(HouseholdLogEntry.objects.filter(
            household_log__household_structure__household__plot=plot).count(), 3)
        plot.household_count = 1
        plot.save()

        plot = Plot.objects.get(pk=plot.pk)
        self.assertEqual(HouseholdLogEntry.objects.filter(
            household_log__household_structure__household__plot=plot).count(), 3)
        self.assertEqual(Household.objects.filter(plot=plot).count(), 3)

        # assert plot value was not changed
        self.assertEqual(plot.household_count, 3)

    def test_can_delete_household_without_household_log_entry(self):
        plot = self.make_confirmed_plot(household_count=2)
        plot.household_count = 1
        plot.save()
        self.assertEqual(Household.objects.filter(plot=plot).count(), 1)

    def test_household_with_refused_enumeration_by_log_entry(self):
        household_structure = self.make_household_structure()
        household_structure = self.add_failed_enumeration_attempt(
            household_structure=household_structure,
            household_status=REFUSED_ENUMERATION)

        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.assertEqual(
                household_log_entry.household_log.last_log_status, REFUSED_ENUMERATION)
            self.assertEqual(
                household_log_entry.household_log.household_structure.failed_enumeration_attempts, 1)
            self.assertFalse(
                household_log_entry.household_log.household_structure.refused_enumeration)

    def test_household_with_refused_enumeration_confirmed(self):
        household_structure = self.make_household_structure(
            household_status=REFUSED_ENUMERATION)
        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.make_household_refusal(household_log_entry=household_log_entry)
            self.assertEqual(
                household_log_entry.household_log.household_structure.failed_enumeration_attempts, 1)
            self.assertTrue(
                household_log_entry.household_log.household_structure.refused_enumeration)

    def test_delete_refused_enumeration_confirmed_updates_household_structure(self):
        household_structure = self.make_household_structure(
            household_status=REFUSED_ENUMERATION)
        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.make_household_refusal(household_log_entry=household_log_entry)
        HouseholdRefusal.objects.all().delete()
        household_log_entrys = HouseholdLogEntry.objects.filter(
            household_log=household_log_entry.household_log)
        for household_log_entry in household_log_entrys:
            self.assertEqual(
                household_log_entry.household_log.household_structure.failed_enumeration_attempts, 1)
            self.assertFalse(
                household_log_entry.household_log.household_structure.refused_enumeration)

    def test_household_with_no_informant(self):
        household_structure = self.make_household_structure(
            household_status=NO_HOUSEHOLD_INFORMANT)
        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.assertEqual(household_log_entry.household_log.last_log_status, NO_HOUSEHOLD_INFORMANT)

    def test_household_with_no_representative(self):
        household_structure = self.make_household_structure(
            household_status=ELIGIBLE_REPRESENTATIVE_ABSENT)
        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.assertEqual(household_log_entry.household_log.last_log_status, ELIGIBLE_REPRESENTATIVE_ABSENT)

    def test_household_log_entry_updates_household_log_last_log_status(self):

        # first log entry
        household_structure = self.make_household_structure(
            household_status=NO_HOUSEHOLD_INFORMANT)
        for household_log_entry in household_structure.householdlog.householdlogentry_set.all():
            self.assertEqual(
                household_log_entry.household_log.last_log_status,
                NO_HOUSEHOLD_INFORMANT)

        # next log entry
        last = household_structure.householdlog.householdlogentry_set.all().order_by(
            'report_datetime').last()
        household_log_entry = self.add_enumeration_attempt2(
            household_structure,
            household_status=ELIGIBLE_REPRESENTATIVE_ABSENT,
            report_datetime=last.report_datetime + relativedelta(hours=1))
        self.assertEqual(
            household_log_entry.household_log.last_log_status,
            ELIGIBLE_REPRESENTATIVE_ABSENT)

        # next log entry
        last = household_structure.householdlog.householdlogentry_set.all().order_by(
            'report_datetime').last()
        household_log_entry = self.add_enumeration_attempt2(
            household_structure,
            household_status=ELIGIBLE_REPRESENTATIVE_ABSENT,
            report_datetime=last.report_datetime + relativedelta(hours=2))
        self.assertEqual(
            household_log_entry.household_log.last_log_status,
            ELIGIBLE_REPRESENTATIVE_ABSENT)

        # next log entry
        last = household_structure.householdlog.householdlogentry_set.all().order_by(
            'report_datetime').last()
        household_log_entry = self.add_enumeration_attempt2(
            household_structure,
            household_status=REFUSED_ENUMERATION,
            report_datetime=last.report_datetime + relativedelta(hours=2))
        self.assertEqual(
            household_log_entry.household_log.last_log_status,
            REFUSED_ENUMERATION)

    def test_household_assessment_needs_three_enumeration_attempts(self):

        household_structure = self.make_household_structure(
            household_status=REFUSED_ENUMERATION)

        self.assertEqual(household_structure.enumeration_attempts, 1)
        self.assertEqual(household_structure.failed_enumeration_attempts, 1)

        # fail to create, needs more enumeration_attempts
        self.assertRaises(
            HouseholdAssessmentError,
            mommy.make_recipe,
            'household.householdassessment',
            household_structure=household_structure)

        household_structure = self.add_failed_enumeration_attempt(
            household_structure=household_structure,
            household_status=REFUSED_ENUMERATION,
            report_datetime=self.get_utcnow() + relativedelta(hours=1))
        household_structure = self.add_failed_enumeration_attempt(
            household_structure=household_structure,
            household_status=REFUSED_ENUMERATION,
            report_datetime=self.get_utcnow() + relativedelta(hours=2))

        try:
            mommy.make_recipe(
                'household.householdassessment',
                household_structure=household_structure)
        except HouseholdAssessmentError:
            self.fail('HouseholdAssessmentError unexpectedly NOT raised')

    def test_household_assessment_updates_failed_enumeration(self):
        household_structure = self.make_household_structure()
        household_structure = self.fail_enumeration(household_structure)
        self.assertTrue(household_structure.failed_enumeration)

    def test_household_assessment_updates_no_informant(self):
        household_structure = self.make_household_structure()
        household_structure = self.fail_enumeration(household_structure)
        self.assertTrue(household_structure.no_informant)

    def test_household_assessment_updates_failed_enumeration_on_delete(self):
        household_structure = self.make_household_structure()
        for _ in range(0, 3):
            household_structure = self.add_failed_enumeration_attempt(household_structure)
        household_structure = HouseholdStructure.objects.get(
            pk=household_structure.pk)
        self.assertFalse(household_structure.failed_enumeration)

    def test_household_assessment_updates_no_informant_on_delete(self):
        household_structure = self.make_household_structure()
        for _ in range(0, 3):
            household_structure = self.add_failed_enumeration_attempt(household_structure)
        household_structure = HouseholdStructure.objects.get(
            pk=household_structure.pk)
        self.assertFalse(household_structure.no_informant)

    def test_refused_enumeration_fails_members_exist(self):
        household_structure = self.make_household_structure()
        self.add_enumeration_attempt(household_structure,
                                     report_datetime=self.get_utcnow())

        mommy.make_recipe(
            'member.representativeeligibility',
            household_structure=household_structure
        )
        mommy.make_recipe(
            'member.householdmember',
            household_structure=household_structure,)
        household_log = HouseholdLog.objects.get(
            household_structure=household_structure)

        options = {
            'household_status': REFUSED_ENUMERATION,
            'household_log': household_log.id,
        }
        form = HouseholdLogEntryForm(data=options)
        self.assertFalse(form.is_valid())

    def test_eligible_member_present_saves(self):
        household_structure = self.make_household_structure()
        self.add_enumeration_attempt(household_structure,
                                     report_datetime=self.get_utcnow())

        mommy.make_recipe(
            'member.representativeeligibility',
            household_structure=household_structure
        )
        mommy.make_recipe(
            'member.householdmember',
            household_structure=household_structure,)
        household_log = HouseholdLog.objects.get(
            household_structure=household_structure)

        options = {
            'household_status': ELIGIBLE_REPRESENTATIVE_PRESENT,
            'household_log': household_log.id,
        }
        form = HouseholdLogEntryForm(data=options)
        self.assertFalse(form.is_valid())
