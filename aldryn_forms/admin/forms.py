# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ..models import FormData, FormSubmission


def form_choices(modelClass):
    form_names = modelClass.objects.values_list('name', flat=True).distinct()

    for name in form_names.order_by('name'):
        yield (name, name)


class BaseFormExportForm(forms.Form):
    excel_limit = 65536
    export_filename = 'export-{language}-{form_name}-%Y-%m-%d'

    form_name = forms.ChoiceField(choices=[])
    from_date = forms.DateField(
        label=_('from date'),
        required=False,
        widget=AdminDateWidget
    )
    to_date = forms.DateField(
        label=_('to date'),
        required=False,
        widget=AdminDateWidget
    )
    language = forms.ChoiceField(
        label=_('language'),
        choices=settings.LANGUAGES
    )

    def __init__(self, *args, **kwargs):
        super(BaseFormExportForm, self).__init__(*args, **kwargs)
        self.fields['form_name'].choices = form_choices(modelClass=self.model)

    def clean(self):
        if self.errors:
            return self.cleaned_data

        queryset = self.get_queryset()

        if queryset.count() >= self.excel_limit:
            error_message = _("Export failed! More then 65,536 entries found, exceeded Excel limitation!")
            raise forms.ValidationError(error_message)

        return self.cleaned_data

    def get_filename(self):
        data = self.cleaned_data
        form_name = data['form_name'].lower()
        filename = self.export_filename.format(
            form_name=slugify(form_name),
            language=data['language'],
        )
        return timezone.now().strftime(filename)

    def get_queryset(self):
        data = self.cleaned_data
        from_date, to_date = data.get('from_date'), data.get('to_date')

        queryset = self.model.objects.filter(
            name=data['form_name'],
            language=data['language'],
        )

        if from_date:
            lower = datetime(*from_date.timetuple()[:6]) # inclusive
            queryset = queryset.filter(sent_at__gte=lower)

        if to_date:
            upper = datetime(*to_date.timetuple()[:6]) + timedelta(days=1) # exclusive
            queryset = queryset.filter(sent_at__lt=upper)

        return queryset


class FormDataExportForm(BaseFormExportForm):
    model = FormData


class FormSubmissionExportForm(BaseFormExportForm):
    model = FormSubmission