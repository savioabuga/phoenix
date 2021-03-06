from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from smartmin.models import SmartModel
from model_utils import Choices
from model_utils.models import TimeStampedModel
from django_fsm import FSMField, transition


class Breed(SmartModel):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


class Color(SmartModel):
    # http://www.sss-mag.com/fernhill/cowcolor.html
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Breeder(SmartModel):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


class Sire(SmartModel):
    name = models.CharField(max_length=30, blank=False)
    code = models.CharField(max_length=10, blank=True)
    breed = models.ForeignKey(Breed, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    breeder = models.ForeignKey(Breeder, null=True, blank=True, related_name='sire_breeder')

    def __unicode__(self):
        return self.name


class Dam(SmartModel):
    name = models.CharField(max_length=30)
    breed = models.ForeignKey(Breed, null=True, blank=True)
    code = models.CharField(max_length=10, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    animal = models.ForeignKey('animals.Animal', null=True, blank=True, related_name='dam_animal')
    breeder = models.ForeignKey(Breeder, null=True, blank=True, related_name='dam_breeder')

    def __unicode__(self):
        return self.name


class Animal(SmartModel):

    state = FSMField(default='open')

    @transition(field=state, source='*', target='open')
    def open(self):
        pass

    @transition(field=state, source='*', target='served')
    def served(self):
        pass

    @transition(field=state, source='*', target='pregnant')
    def pregnant(self):
        pass

    @transition(field=state, source='*', target='lactating')
    def lactating(self):
        pass

    @transition(field=state, source='*', target='disposed')
    def disposed(self):
        pass

    # Choices
    SEX_CHOICES = Choices((None, '------'), ('female', _('Female')), ('male', _('Male')), )

    # Identification
    ear_tag = models.CharField(max_length=30, blank=False)
    name = models.CharField(max_length=30, blank=False)

    # Description
    color = models.ForeignKey(Color, null=True, blank=True)
    sex = models.CharField(choices=SEX_CHOICES, max_length=20)
    breed = models.ForeignKey(Breed, null=True, blank=True)
    sire = models.ForeignKey(Sire, null=True, blank=True, related_name='sire')
    dam = models.ForeignKey(Dam, null=True, blank=True, related_name='dam')

    # Calfhood
    birth_date = models.DateField(null=True, blank=True)
    birth_weight = models.IntegerField(null=True, blank=True)
    weaning_date = models.DateField(null=True, blank=True)
    weaning_weight = models.IntegerField(null=True, blank=True)
    yearling_date = models.DateField(null=True, blank=True)
    yearling_weight = models.IntegerField(null=True, blank=True)
    farm = models.ForeignKey('users.User', null=True, blank=True)

    def __unicode__(self):
        return '%s-%s' % (self.ear_tag, self.name)

    @property
    def date_of_first_service(self):
        try:
            date = self.animal_services.earliest('date').date
        except Service.DoesNotExist:
            date = ''
        return date

    @property
    def number_of_services(self):
        return self.animal_services.count()

    @property
    def number_of_successful_services(self):
        return self.pregnancy_checks.filter(result=PregnancyCheck.RESULT_CHOICES.pregnant).exclude(service=None).count()

    @property
    def number_of_failed_services(self):
        return self.pregnancy_checks.filter(result=PregnancyCheck.RESULT_CHOICES.open).exclude(service=None).count()

    @property
    def all_time_production(self):
        return self.milkproduction.aggregate(Sum('amount'))['amount__sum']


@receiver(post_save, sender=Animal)
def add_dam(sender, **kwargs):
    animal = kwargs['instance']

    if animal.sex == Animal.SEX_CHOICES.female:
        Dam.objects.create(animal=animal, name=animal.name, breed=animal.breed, birth_date=animal.birth_date, created_by=animal.created_by,
                           modified_by=animal.modified_by)


class MilkProduction(SmartModel):
    # Choices
    TIME_CHOICES = Choices(('am', _('Morning')), ('pm', _('Evening')))

    animal = models.ForeignKey(Animal, null=False, blank=False, related_name='milkproduction')
    time = models.CharField(choices=TIME_CHOICES, max_length=10, null=False, blank=False)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    butterfat = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    date = models.DateField()


class Service(SmartModel):
    # Choices
    METHOD_CHOICES = Choices(('artificial_insemination', _('Artificial Insemination')), ('natural_service', _('Natural Service')),)

    animal = models.ForeignKey(Animal, null=False, blank=False, related_name='animal_services')
    method = models.CharField(choices=METHOD_CHOICES, max_length=30, default=METHOD_CHOICES.artificial_insemination, blank=False)
    sire = models.ForeignKey(Sire, null=False, blank=False, related_name='sire_services')
    date = models.DateField()
    notes = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return 'Sire: ' + str(self.sire)


class PregnancyCheck(SmartModel):
    # Choices
    RESULT_CHOICES = Choices(('pregnant', _('Pregnant')), ('open', _('Open')),)
    CHECK_METHOD_CHOICES = Choices(('palpation', _('Palpation')), ('ultrasound', _('Ultrasound')), ('observation', _('Observation')), ('blood', _('Blood')))

    service = models.ForeignKey(Service, null=True, blank=True, related_name='pregnancy_checks')
    animal = models.ForeignKey(Animal, null=False, blank=False, related_name='pregnancy_checks')
    result = models.CharField(choices=RESULT_CHOICES, max_length=20)
    check_method = models.CharField(choices=CHECK_METHOD_CHOICES, max_length=20)
    date = models.DateField()


class LactationPeriod(SmartModel):
    animal = models.ForeignKey(Animal, null=False, blank=False, related_name='animal_lactation_periods')
    calves = models.ManyToManyField(Animal, null=False, blank=False, related_name='calf_lactation_periods')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)




