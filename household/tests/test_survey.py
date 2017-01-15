from django.test import TestCase, tag

from survey.site_surveys import site_surveys

from .mixin import HouseholdMixin


class TestSurvey(HouseholdMixin, TestCase):

    """Tests to assert survey attrs."""

    def test_household_structure(self):
        self.survey_schedule = self.get_survey_schedule(0)
        self.household_structure = self.make_household_structure(
            survey_schedule=self.survey_schedule)

        self.assertIsNotNone(self.household_structure.survey_schedule)
        self.assertIsNotNone(self.household_structure.survey_schedule_object)
        self.assertRaises(
            AttributeError, getattr, self.household_structure, 'survey')
        self.assertRaises(
            AttributeError, getattr, self.household_structure, 'survey_object')

    @tag('erik')
    def test_household_structure_survey_schedule_set_correctly(self):

        survey_schedules = site_surveys.get_survey_schedules(group_name='example-survey')

        if not survey_schedules:
            raise AssertionError('survey_schedules is unexpectedly None')

        for index, survey_schedule in enumerate(survey_schedules):
            household_structure = self.make_household_structure(
                survey_schedule=survey_schedule)
            self.assertEqual(
                household_structure.survey_schedule,
                'example-survey.example-survey-{}.test_community'.format(index + 1))
            self.assertEqual(
                household_structure.survey_schedule_object.field_value,
                'example-survey.example-survey-{}.test_community'.format(index + 1))
            self.assertEqual(
                household_structure.survey_schedule_object.name,
                'example-survey-{}'.format(index + 1))
            self.assertEqual(
                household_structure.survey_schedule_object.group_name,
                'example-survey')
            self.assertEqual(
                household_structure.survey_schedule_object.short_name,
                'example-survey.example-survey-{}'.format(index + 1))
