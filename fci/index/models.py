# coding: utf-8
from collections import defaultdict

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django_extensions.db.fields.json import JSONField
from django_extensions.db.models import TimeStampedModel


class Resource(TimeStampedModel):
    """ Resource model."""

    class Meta:
        unique_together = ('name', 'parent')

    name = models.CharField(max_length=255,
                            validators=[RegexValidator(r"^[^/]+$")])
    is_collection = models.BooleanField(blank=True, editable=False)
    # parent may be null only for root resource
    parent = models.ForeignKey('Resource', null=True, blank=True)

    @property
    def path(self):
        """ Returns full path from root to resource."""
        parts = [self.name]
        parts.extend(p.name for p in self.parents)
        return '/'.join(reversed(parts)).strip('/')

    @property
    def parents(self):
        """ Yields parent dirs up to root resource."""
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def __str__(self):
        return self.path

    def clean(self):
        super(Resource, self).clean()
        errors = {}
        errors.update(self.clean_parent())
        if errors:
            raise ValidationError(errors)

    def clean_parent(self):
        errors = defaultdict(list)
        if not self.parent.is_collection:
            errors['parent'].append('Parent must be a collection')
        if not self.pk:
            return errors
        for p in self.parents:
            if p.pk == self.pk:
                errors['parent'].append("Resource is a parent of itself")
                break
        return errors

    @property
    def metadata(self):
        if hasattr(self, '_metadata'):
            return self._metadata
        ct = ContentType.objects.get_for_model(self)
        try:
            meta = Metadata.objects.get(object_id=self.pk, content_type=ct)
        except Metadata.DoesNotExist:
            return {}
        self._metadata = meta.data
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(Resource, self).save(force_insert, force_update, using,
                                   update_fields)
        if hasattr(self, '_metadata'):
            self.save_metadata()

    def save_metadata(self):
        data = self._metadata
        ct = ContentType.objects.get_for_model(self)
        try:
            meta = Metadata.objects.get(
                object_id=self.pk, content_type=ct)
        except Metadata.DoesNotExist:
            meta = Metadata(object_id=self.pk, content_type=ct)

        if data:
            meta.data = data
            meta.save()
        elif meta.pk:
                meta.delete()

class Directory(Resource):
    """ Directory model."""

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not update_fields or 'is_collection' in update_fields:
            # Directory.is_collection is ALWAYS True
            self.is_collection = True
        super(Directory, self).save(force_insert, force_update, using,
                                    update_fields)


class File(Resource):
    """ File model."""
    size = models.IntegerField(blank=True, default=0)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not update_fields or 'is_collection' in update_fields:
            # File.is_collection is ALWAYS False
            self.is_collection = False
        super(File, self).save(force_insert, force_update, using,
                               update_fields)


class Metadata(models.Model):
    resource = GenericForeignKey()
    object_id = models.IntegerField()
    content_type = models.ForeignKey('contenttypes.ContentType')
    data = JSONField()
