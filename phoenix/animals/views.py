import datetime
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.db.models import Q
from smartmin.views import SmartCRUDL, SmartView, SmartCreateView, SmartReadView, SmartUpdateView, SmartListView
from phoenix.records.views import NoteCRUDL
from phoenix.health.views import TreatmentCRUDL
from .models import Animal, Breed, Service, PregnancyCheck, MilkProduction, Color, Dam, Sire, Breeder
from .forms import AnimalForm, ServiceForm, PregnancyCheckForm, MilkProductionForm, SireForm, DamForm


class ServiceCRUDL(SmartCRUDL):
    model = Service
    actions = ('create', 'read', 'update', 'list')

    class Create(SmartCreateView):
        form_class = ServiceForm
        fields = ('method', 'sire', 'date', 'notes',)

        def get(self, request, *args, **kwargs):
            animal_id = request.GET.get('animal', None)

            if animal_id:
                try:
                    Animal.objects.get(id=animal_id)
                except Animal.DoesNotExist:
                    messages.warning(request, 'Animal Id is required')
                    return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            else:
                messages.error(request, 'Animal Id is required')
                return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            return super(ServiceCRUDL.Create, self).get(request, *args, **kwargs)

        def pre_save(self, obj):
            animal = Animal.objects.get(id=self.request.GET.get('animal'))
            obj.animal = animal
            return super(ServiceCRUDL.Create, self).pre_save(obj)

        def post_save(self, obj):
            obj.animal.served()
            obj.animal.save()
            return super(ServiceCRUDL.Create, self).post_save(obj)

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal')])

    class Read(SmartReadView):
        fields = ('id', 'method', 'sire', 'date', 'notes', 'created_on', 'created_by')

        def get_context_data(self, **kwargs):  # pragma: no cover
            context_data = super(ServiceCRUDL.Read, self).get_context_data(**kwargs)
            self.request.service = self.get_object()

            pregnancychecks_response = PregnancyCheckCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(pregnancychecks_response, 'context_data'):
                context_data['pregnancychecks'] = render_to_string('animals/pregnancycheck_related_list.html', pregnancychecks_response.context_data, RequestContext(self.request))
            return context_data

    class List(SmartListView):
        fields = ('id', 'method', 'sire', 'date', 'status', 'notes')
        default_order = '-id'

        def get_status(self, obj):
            if obj.pregnancy_checks.all():
                return PregnancyCheck.RESULT_CHOICES[obj.pregnancy_checks.latest('created_on').result]
            return ''

        def get_queryset(self, **kwargs):
            queryset = super(ServiceCRUDL.List, self).get_queryset(**kwargs)
            if hasattr(self.request, 'animal'):
                queryset = queryset.filter(animal=self.request.animal)
            return queryset

        def get_context_data(self, **kwargs):
            context_data = super(ServiceCRUDL.List, self).get_context_data(**kwargs)
            if hasattr(self.request, 'animal'):
                context_data['animal'] = self.request.animal
            return context_data

        def get_method(self, obj):
            if obj.method:
                return Service.METHOD_CHOICES[obj.method]
            return ''


class PregnancyCheckCRUDL(SmartCRUDL):
    model = PregnancyCheck

    class Create(SmartCreateView):
        form_class = PregnancyCheckForm
        fields = ('service', 'result', 'check_method', 'date')

        def get(self, request, *args, **kwargs):
            animal_id = request.GET.get('animal', None)

            if animal_id:
                try:
                    Animal.objects.get(id=animal_id)
                except Animal.DoesNotExist:
                    messages.warning(request, 'Animal Id is required')
                    return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            else:
                messages.error(request, 'Animal Id is required')
                return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            return super(PregnancyCheckCRUDL.Create, self).get(request, *args, **kwargs)

        def pre_save(self, obj):
            animal = Animal.objects.get(id=self.request.GET.get('animal'))
            obj.animal = animal

            # Getting the last service for the animal
            try:
                service = animal.animal_services.latest('created_on')
            except Service.DoesNotExist:
                pass
            else:
                obj.service = service

            return super(PregnancyCheckCRUDL.Create, self).pre_save(obj)

        def post_save(self, obj):
            if obj.result == PregnancyCheck.RESULT_CHOICES.pregnant:
                obj.animal.pregnant()
            elif obj.result == PregnancyCheck.RESULT_CHOICES.open:
                obj.animal.open()
            obj.animal.save()
            return super(PregnancyCheckCRUDL.Create, self).post_save(obj)

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal')])

    class Read(SmartReadView):
        fields = ('id', 'check_method', 'result', 'date', 'created', 'modified')

    class List(SmartListView):
        fields = ('id', 'check_method', 'result', 'date')
        default_order = '-id'

        def get_check_method(self, obj):
            if obj.check_method:
                return PregnancyCheck.CHECK_METHOD_CHOICES[obj.check_method]
            return ''

        def get_result(self, obj):
            return PregnancyCheck.RESULT_CHOICES[obj.result]

        def get_queryset(self, **kwargs):
            queryset = super(PregnancyCheckCRUDL.List, self).get_queryset(**kwargs)
            if hasattr(self.request, 'animal'):
                queryset = queryset.filter(animal=self.request.animal)
            if hasattr(self.request, 'service'):
                queryset = queryset.filter(service=self.request.service)
            return queryset

        def get_context_data(self, **kwargs):
            context_data = super(PregnancyCheckCRUDL.List, self).get_context_data(**kwargs)
            if hasattr(self.request, 'animal'):
                context_data['animal'] = self.request.animal
            return context_data


class AnimalNoteCRUDL(NoteCRUDL):

    class Create(NoteCRUDL.Create):

        def get(self, request, *args, **kwargs):
            animal_id = request.GET.get('animal', None)
            if animal_id:
                try:
                    Animal.objects.get(id=animal_id)
                except Animal.DoesNotExist:
                    messages.error(request, 'Animal Id is required')
                    return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            else:
                messages.error(request, 'Animal Id is required')
                return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            return super(NoteCRUDL.Create, self).get(request, *args, **kwargs)

        def post_save(self, obj):
            obj = super(NoteCRUDL.Create, self).post_save(obj)
            animal_id = self.request.GET.get('animal', None)
            animal = Animal.objects.get(id=animal_id)
            obj.animals.add(animal)
            return obj

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal', None)])

    class List(NoteCRUDL.List):
        fields = ('id', 'date', 'file', 'details')

        def get_queryset(self, **kwargs):
            queryset = super(NoteCRUDL.List, self).get_queryset(**kwargs)
            queryset = queryset.filter(animals=self.request.animal)
            return queryset


class AnimalTreatmentCRUDL(TreatmentCRUDL):

    class Create(TreatmentCRUDL.Create):
        fields = ('date', 'description', 'notes')

        def get(self, request, *args, **kwargs):
            animal_id = request.GET.get('animal', None)
            if animal_id:
                try:
                    Animal.objects.get(id=animal_id)
                except Animal.DoesNotExist:
                    messages.error(request, 'Animal Id is required')
                    return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            else:
                messages.error(request, 'Animal Id is required')
                return redirect(request.META.get('HTTP_REFERER', reverse('animals.animal_list')))
            return super(AnimalTreatmentCRUDL.Create, self).get(request, *args, **kwargs)

        def post_save(self, obj):
            obj = super(AnimalTreatmentCRUDL.Create, self).post_save(obj)
            animal_id = self.request.GET.get('animal', None)
            animal = Animal.objects.get(id=animal_id)
            obj.animals.add(animal)
            return obj

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal', None)])

    class Update(TreatmentCRUDL.Update):
        fields = ('date', 'description', 'notes',)

        def get_success_url(self):
            animal_id = self.object.animals.all()[0].id
            return reverse('animals.animal_read', args=[animal_id])

    class List(TreatmentCRUDL.List):
        fields = ('id', 'type', 'date', 'description', 'notes')

        def get_queryset(self, **kwargs):
            queryset = super(AnimalTreatmentCRUDL.List, self).get_queryset(**kwargs)
            queryset = queryset.filter(animals=self.request.animal)
            return queryset


class BreedCRUDL(SmartCRUDL):
    model = Breed
    permissions = False


class ColorCRUDL(SmartCRUDL):
    model = Color
    permissions = False


class MilkProductionCRUDL(SmartCRUDL):
    model = MilkProduction
    actions = ('create', 'list')

    class Create(SmartCreateView):
        form_class = MilkProductionForm

        def customize_form_field(self, name, field):
            field = super(MilkProductionCRUDL.Create, self).customize_form_field(name, field)
            if name == 'date':
                field.initial = datetime.date.today()
            return field

        def get_success_url(self):
            return reverse('animals.milkproduction_create')

    class List(SmartListView):
        fields = ('id', 'animal', 'time', 'amount', 'butterfat_ratio')
        default_order = '-id'

        def get_time(self, obj):
            return MilkProduction.TIME_CHOICES[obj.time]

        def get_context_data(self, **kwargs):
            context_data = super(MilkProductionCRUDL.List, self).get_context_data(**kwargs)
            if hasattr(self.request, 'animal'):
                context_data['animal'] = self.request.animal
            return context_data


class AnimalMilkProductionCRUDL(MilkProductionCRUDL):
    actions = ('animal_create', 'animal_list')

    class AnimalCreate(MilkProductionCRUDL.Create):
        form_class = MilkProductionForm
        fields = ('date', 'time', 'amount', 'butterfat')

        def customize_form_field(self, name, field):
            field = super(AnimalMilkProductionCRUDL.Create, self).customize_form_field(name, field)
            if name == 'date':
                field.initial = datetime.date.today()
            return field

        def pre_save(self, obj):
            obj = super(AnimalMilkProductionCRUDL.Create, self).pre_save(obj)
            animal_id = self.request.GET.get('animal')
            obj.animal = Animal.objects.get(id=animal_id)
            return obj

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal', None)])

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^{}/animal/create/$'.format(path, action)

    class AnimalList(MilkProductionCRUDL.List):
        fields = ('id', 'time', 'amount', 'butterfat_ratio')
        default_order = '-id'

        def get_time(self, obj):
            return MilkProduction.TIME_CHOICES[obj.time]

        def get_context_data(self, **kwargs):
            context_data = super(AnimalMilkProductionCRUDL.List, self).get_context_data(**kwargs)
            if hasattr(self.request, 'animal'):
                context_data['animal'] = self.request.animal
            return context_data

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^{}/animal/$'.format(path)


class AnimalCRUDL(SmartCRUDL):
    model = Animal
    actions = ('create', 'read', 'update', 'list', 'add_sire', 'add_offspring', 'dashboard')

    class FormMixin(object):

        def __init__(self, **kwargs):
            self.form_class = AnimalForm
            super(AnimalCRUDL.FormMixin, self).__init__(**kwargs)

    class Create(FormMixin, SmartCreateView):

        def pre_save(self, obj):
            obj = super(AnimalCRUDL.Create, self).pre_save(obj)
            obj.farm = self.request.user
            return obj

    class Dashboard(SmartView, DetailView):

        def get_context_data(self, **kwargs):
            context_data = super(AnimalCRUDL.Dashboard, self).get_context_data(**kwargs)
            animal = self.get_object()

            # Milk Production graph data
            graph_data = MilkProduction.get_graph_data(animal)
            xdata = [data[0] for data in graph_data]
            ydata = [data[1] for data in graph_data]

            extra_serie1 = {"tooltip": {"y_start": "", "y_end": " cal"}}
            chartdata = {
                'x': xdata, 'name1': '', 'y1': ydata, 'extra1': extra_serie1,
            }

            context_data['charttype'] = 'discreteBarChart'
            context_data['chartcontainer'] = 'discretebarchart_container'
            context_data['chartdata'] = chartdata
            context_data['extra'] = {'x_is_date': True, 'x_axis_format': '%U', 'tag_script_js': True, 'jquery_on_ready': True, }

            return context_data

        @classmethod
        def derive_url_pattern(cls, path, action):
            """
            Returns the URL pattern for this view.
            """
            return r'^%s/%s/(?P<pk>\d+)/$' % (path, action)

    class AddSire(FormMixin, SmartCreateView):
        fields = ('name', 'color', 'breed', 'sire', 'dam',
                  'birth_date', 'birth_weight', 'breeder')

    class AddOffspring(FormMixin, SmartCreateView):

        def get(self, request, *args, **kwargs):
            animal_id = request.GET.get('animal', None)
            if animal_id:
                try:
                    Animal.objects.get(id=animal_id)
                except Animal.DoesNotExist:
                    messages.error(request, 'Animal Id is required')
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            else:
                messages.error(request, 'Animal Id is required')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            return super(AnimalCRUDL.AddOffspring, self).get(request, *args, **kwargs)

        def customize_form_field(self, name, field):
            field = super(AnimalCRUDL.AddOffspring, self).customize_form_field(name, field)
            animal_id = self.request.GET.get('animal')
            animal = Animal.objects.get(id=animal_id)

            if name == 'birth_date':
                field.initial = datetime.date.today()

            try:
                service = animal.animal_services.latest('created_on')
            except Service.DoesNotExist:
                pass
            else:
                if name == 'sire':
                    field.initial = service.sire
                if name == 'dam':
                    field.initial = animal

            return field

        #def pre_save(self, obj):
         #   obj = super(AnimalCRUDL.AddOffspring, self).pre_save(obj)
          #  animal_id = self.request.GET.get('animal')
            #obj.dam = Animal.objects.get(id=animal_id)
            #eturn obj

        def pre_save(self, obj):
            obj = super(AnimalCRUDL.AddOffspring, self).pre_save(obj)
            obj.farm = self.request.user
            return obj

        def post_save(self, obj):
            obj.lactating()
            obj.save()
            return super(AnimalCRUDL.AddOffspring, self).post_save(obj)

        def get_success_url(self):
            return reverse('animals.animal_read', args=[self.request.GET.get('animal')])

    class Read(SmartReadView):
        fields = ('ear_tag', 'name', 'birth_date', 'color', 'sex', 'breed', 'sire', 'dam',)

        def get_breed(self, obj):
            if obj.breed:
                return obj.breed
            return ''

        def get_sire(self, obj):
            if obj.sire:
                return obj.sire
            return ''

        def get_dam(self, obj):
            if obj.dam:
                return obj.dam
            return ''

        def get_context_data(self, **kwargs):
            context_data = super(AnimalCRUDL.Read, self).get_context_data(**kwargs)

            # Add related lists
            self.request.animal = self.object

            # fertile
            context_data['fertile'] = False
            if self.object.sex == Animal.SEX_CHOICES.female:
                context_data['fertile'] = True

            service_response = ServiceCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(service_response, 'context_data'):
                context_data['services'] = render_to_string('animals/service_related_list.html', service_response.context_data, RequestContext(self.request))

            pregnancy_response = PregnancyCheckCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(pregnancy_response, 'context_data'):
                context_data['pregnancies'] = render_to_string('animals/pregnancycheck_related_list.html', pregnancy_response.context_data, RequestContext(self.request))

            treatment_response = AnimalTreatmentCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(treatment_response, 'context_data'):
                treatment_response.context_data['add_url'] = reverse('animals.treatment_create') + '?animal=' + str(self.request.animal.id)
                context_data['treatment'] = render_to_string('health/treatment_related_list.html', treatment_response.context_data, RequestContext(self.request))

            note_response = NoteCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(note_response, 'context_data'):
                note_response.context_data['add_url'] = reverse('animals.note_create') + '?animal=' + str(self.request.animal.id)
                context_data['notes'] = render_to_string('records/note_related_list.html', note_response.context_data, RequestContext(self.request))

            context_data['animal_documents'] = render_to_string('records/animaldocument_form.html', {'animal': self.request.animal}, RequestContext(self.request))

            milkproduction_response = AnimalMilkProductionCRUDL().view_for_action('animal_list').as_view()(self.request)
            if hasattr(milkproduction_response, 'context_data'):
                context_data['milkproduction'] = render_to_string('animals/animal_milkproduction_related_list.html', milkproduction_response.context_data, RequestContext(self.request))

            self.request.offsprings = True
            offspring_response = AnimalCRUDL().view_for_action('list').as_view()(self.request)
            if hasattr(offspring_response, 'context_data'):
                context_data['offsprings'] = render_to_string('animals/offspring_related_list.html', offspring_response.context_data, RequestContext(self.request))

            return context_data

    class Update(FormMixin, SmartUpdateView):
        pass

    class List(SmartListView):
        fields = ('id', 'ear_tag', 'name', 'breed', 'sex', 'sire', 'dam')
        search_fields = ('name', 'breed__name', 'dam__name', 'sire__name', 'ear_tag')

        def get_queryset(self, **kwargs):
            queryset = super(AnimalCRUDL.List, self).get_queryset(**kwargs)
            queryset = queryset.filter(farm=self.request.user)
            if hasattr(self.request, 'offsprings') and self.request.offsprings:
                queryset = queryset.filter(Q(dam__animal=self.request.animal))

            if hasattr(self.request, 'group') and self.request.group:
                queryset = self.request.group.get_animals_queryset()

            return queryset

        def get_context_data(self, **kwargs):
            context_data = super(AnimalCRUDL.List, self).get_context_data(**kwargs)
            if hasattr(self.request, 'animal'):
                context_data['animal'] = self.request.animal
            return context_data

        def get_breed(self, obj):
            if obj.breed:
                return obj.breed
            return ''

        def get_sire(self, obj):
            if obj.sire:
                return obj.sire
            return ''

        def get_dam(self, obj):
            if obj.dam:
                return obj.dam
            return ''


class SireCRUDL(SmartCRUDL):
    model = Sire

    class List(SmartListView):
        fields = ('id', 'name', 'code', 'breeder')


class DamCRUDL(SmartCRUDL):
    model = Dam

    class Create(SmartCreateView):
        form_class = DamForm

    class List(SmartListView):
        fields = ('id', 'name', 'code', 'breeder')


class BreederCRUDL(SmartCRUDL):
    model = Breeder

    class Create(SmartCreateView):
        form_class = SireForm

    class List(SmartListView):
        fields = ('id', 'name')
