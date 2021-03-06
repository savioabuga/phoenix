from datetime import date
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from model_mommy import mommy
from phoenix.animals.models import Animal, PregnancyCheck, Service, Dam
from phoenix.animals import views
from phoenix.utils import test_utils


class AnimalCRUDLTestCase(TestCase):
    def setUp(self):
        self.bull = mommy.make('animals.Sire')
        self.cow = mommy.make('animals.Dam')
        self.animal = mommy.make('animals.Animal', name='Dufour', birth_date=date.today(), sex=Animal.SEX_CHOICES.female)

    def test_creating_animal(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_create'))
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        post_data = {
            'ear_tag': '201',
            'name': 'Saldana',
            'sex': Animal.SEX_CHOICES.male,
            'birth_date': date.today()

        }
        url = reverse('animals.animal_create')
        response = self.client.post(url, post_data, follow=True)
        self.assertContains(response, 'Your new animal has been created.')
        self.assertRedirects(response, reverse('animals.animal_list'))

    def test_animal_read(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='service_list'))
        user.user_permissions.add(Permission.objects.get(codename='pregnancycheck_list'))
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='note_list'))
        user.user_permissions.add(Permission.objects.get(codename='milkproduction_list'))

        dufour = mommy.make('animals.Animal', name='Dufour', birth_date=date.today(), sex=Animal.SEX_CHOICES.female)
        dufour_dam = Dam.objects.create(name='Dam', created_by=user, modified_by=user)
        # add services
        mommy.make('animals.Service', animal=dufour, sire=self.bull, date=date.today(), notes="Dufour's service")
        # add pregnancycheck
        mommy.make('animals.PregnancyCheck', animal=dufour, result=PregnancyCheck.RESULT_CHOICES.pregnant)
        mommy.make('animals.Animal', ear_tag='56', sire=self.bull, name='Dufour calf', sex=Animal.SEX_CHOICES.male, dam=dufour_dam)
        # add note
        mommy.make('records.Note', details='Dufour note', animals=[dufour])
        # add milk production
        mommy.make('animals.MilkProduction', amount=20, animal=dufour)

        url = reverse('animals.animal_read', args=[dufour.id])
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Dufour's service")
        self.assertContains(response, 'Pregnant')
        #self.assertContains(response, 'Dufour calf')
        self.assertContains(response, '20')

    def test_offspring_animal_id_and_service(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='animal_add_offspring'))

        # without the animal id
        url = reverse('animals.animal_add_offspring')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # non existent animal id
        url = reverse('animals.animal_add_offspring') + '?animal=100'
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # existing animal but with no service, proceed as normal
        dufour = mommy.make('animals.Animal', name='Dufour', birth_date=date.today(), sex=Animal.SEX_CHOICES.female)

        url = reverse('animals.animal_add_offspring') + '?animal=' + str(dufour.id)
        response = self.client.get(url, follow=True)
        self.assertNotContains(response, 'Animal Id is required')

        # existing animal with service
        service = mommy.make('animals.Service', sire=self.bull, animal=dufour)
        url = reverse('animals.animal_add_offspring') + '?animal=' + str(dufour.id)
        response = self.client.get(url, follow=True)

        form_fields = response.context_data['form'].fields
        self.assertEqual(form_fields['birth_date'].initial, date.today())
        self.assertEqual(form_fields['dam'].initial, dufour)
        self.assertEqual(form_fields['sire'].initial, service.sire)

    def test_adding_offspring(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='animal_add_offspring'))

        post_data = {
            'ear_tag': '104M',
            'sex': Animal.SEX_CHOICES.male,
            'name': 'Sasha',
            'birth_date': date.today()
        }

        url = reverse('animals.animal_add_offspring') + '?animal=' + str(self.animal.id)
        self.client.post(url, post_data, follow=True)
        offspring = Animal.objects.latest('created_on')
        self.assertEqual(offspring.ear_tag, '104M')


class ServiceCRUDLTestCase(TestCase):
    def setUp(self):
        self.shauna = mommy.make('animals.Animal', ear_tag='123', name='shauna', sex=Animal.SEX_CHOICES.female)
        self.bull = mommy.make('animals.Sire', name='sire')
        self.service = mommy.make('animals.Service', animal=self.shauna, method=Service.METHOD_CHOICES.artificial_insemination,
                                  sire=self.bull)

    def test_offspring_animal_id(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='service_list'))
        user.user_permissions.add(Permission.objects.get(codename='service_create'))

        # without the animal id
        url = reverse('animals.service_create')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # non existent animal id
        url = reverse('animals.service_create') + '?animal=100'
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # existing animal but with no service, proceed as normal
        url = reverse('animals.service_create') + '?animal=' + str(self.shauna.id)
        response = self.client.get(url, follow=True)
        self.assertNotContains(response, 'Animal Id is required')

    def test_adding_service(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='animal_create'))
        user.user_permissions.add(Permission.objects.get(codename='service_create'))
        user.user_permissions.add(Permission.objects.get(codename='service_list'))

        self.phoenix = mommy.make('animals.Animal', ear_tag='PNX', sex=Animal.SEX_CHOICES.female)

        post_data = {
            'method': Service.METHOD_CHOICES.artificial_insemination,
            'sire': self.bull.id,
            'date': date.today()
        }

        url = reverse('animals.service_create') + '?animal=' + str(self.phoenix.id)
        response = self.client.post(url, post_data, follow=True)
        service = Service.objects.latest('created_on')
        self.assertEqual(service.animal, self.phoenix)
        self.assertRedirects(response, reverse('animals.animal_read', args=[self.phoenix.id]))
        self.assertContains(response, 'Artificial Insemination')

    def test_service_read(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='service_read'))
        user.user_permissions.add(Permission.objects.get(codename='pregnancycheck_list'))
        pregnancy_check = mommy.make('animals.PregnancyCheck', animal=self.shauna, result=PregnancyCheck.RESULT_CHOICES.open, service=self.service)
        url = reverse('animals.service_read', args=[self.service.id])
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Open')
        self.assertContains(response, pregnancy_check.id)


class PregnancyCheckCRDULTestCase(TestCase):
    def setUp(self):
        self.laryn = mommy.make('animals.Animal', ear_tag='456', sex=Animal.SEX_CHOICES.female)
        self.shauna = mommy.make('animals.Animal', ear_tag='123', sex=Animal.SEX_CHOICES.female)
        self.shauna_pd = mommy.make('animals.PregnancyCheck', animal=self.shauna, result=PregnancyCheck.RESULT_CHOICES.open)

        self.factory = RequestFactory()

    def test_animal_id_required(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='pregnancycheck_list'))
        user.user_permissions.add(Permission.objects.get(codename='pregnancycheck_create'))

        # without the animal id
        url = reverse('animals.pregnancycheck_create')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # non existent animal id
        url = reverse('animals.pregnancycheck_create') + '?animal=100'
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')

        # existing animal but with no service, proceed as normal
        url = reverse('animals.pregnancycheck_create') + '?animal=' + str(self.shauna.id)
        response = self.client.get(url, follow=True)
        self.assertNotContains(response, 'Animal Id is required')

    def test_service_list(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='pregnancycheck_list'))
        request = self.factory.get(reverse('animals.animal_read', args=[self.shauna.id]))
        request.user = user
        request.animal = self.shauna
        pregnancy_response = views.PregnancyCheckCRUDL().view_for_action('list').as_view()(request)
        self.assertIn(self.shauna_pd, pregnancy_response.context_data['pregnancycheck_list'])

        url = reverse('animals.animal_read', args=[self.shauna.id])
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Open')

        # pregnancy check with a service
        service = mommy.make('animals.Service', animal=self.shauna)
        mommy.make('animals.PregnancyCheck', animal=self.shauna, result=PregnancyCheck.RESULT_CHOICES.pregnant, service=service)
        url = reverse('animals.animal_read', args=[self.shauna.id])
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Pregnant')


class TreatmentCRUDLTestCase(TestCase):
    def setUp(self):
        self.laryn = mommy.make('animals.Animal', ear_tag='456', sex=Animal.SEX_CHOICES.female)
        self.shauna = mommy.make('animals.Animal', ear_tag='123', sex=Animal.SEX_CHOICES.female)
        self.treatment = mommy.make('health.Treatment')
        self.treatment.animals.add(self.shauna, self.laryn)

    def test_creating_animal_treatment(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='animal_list'))
        user.user_permissions.add(Permission.objects.get(codename='animal_read'))
        user.user_permissions.add(Permission.objects.get(codename='treatment_create'))
        user.user_permissions.add(Permission.objects.get(codename='treatment_list'))
        # animal id is required
        url = reverse('animals.treatment_create')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')
        # non-existent animal
        url = reverse('animals.treatment_create') + '?animal=10'
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Animal Id is required')
        # existing animal
        url = reverse('animals.treatment_create') + '?animal=' + str(self.shauna.id)
        response = self.client.get(url, follow=True)
        self.assertNotContains(response, 'Animal Id is required')
        # creating an treatment
        post_data = {
            'date': '2015-04-30',
            'description': 'A test description',
            'notes': 'Nothing much to say'
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertContains(response, 'Your new treatment has been created.')
        self.assertRedirects(response, reverse('animals.animal_read', args=[self.shauna.id]))

    def test_treatment_read(self):
        user = test_utils.create_logged_in_user(self)
        user.user_permissions.add(Permission.objects.get(codename='treatment_read'))
        url = reverse('animals.treatment_read', args=[self.treatment.id])
        response = self.client.get(url, follow=True)
        self.assertContains(response, reverse('animals.animal_read', args=[self.shauna.id]))
        self.assertContains(response, reverse('animals.animal_read', args=[self.laryn.id]))
