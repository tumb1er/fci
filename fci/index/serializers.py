# coding: utf-8
import json

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from fci.index import models


class PlainResourceSerializer(serializers.ModelSerializer):

    # noinspection PyPep8Naming
    @property
    def Meta(self):
        """
        Dynamically choose models class for ModelSerializer.Meta on
        self.instance value.
        """
        if hasattr(self, '_meta'):
            return getattr(self, '_meta')

        if self.instance:
            model_class = type(self.instance)
        else:
            model_class = models.Resource

        class Meta:
            model = model_class
         #   read_only_fields = ('parent',)

        setattr(self, '_meta', Meta)
        return Meta

    is_collection = serializers.BooleanField()

    url = serializers.SerializerMethodField()

    metadata = serializers.JSONField()

    @staticmethod
    def get_url(obj):
        return reverse('resource-detail', kwargs={'path': obj.path})

    @staticmethod
    def validate_parent(value):
        if not value.is_collection:
            raise ValidationError("Parent must be a collection")
        return value

    def validate_is_collection(self, value):
        if self.instance and self.instance.is_collection != value:
            raise ValidationError(
                "Resource type cannot be changed after creation")
        return value

    def validate_metadata(self, value):
        return json.loads(value)


class DirectorySerializer(PlainResourceSerializer):
    class Meta:
        model = models.Directory


class FileSerializer(PlainResourceSerializer):
    class Meta:
        model = models.File


class ResourceSerializer(PlainResourceSerializer):

    def get_fields(self):
        fields = super(ResourceSerializer, self).get_fields()
        if self.instance and self.instance.is_collection:
            kwargs = dict(source='resource_set.all', many=True, read_only=True)
            fields['descendants'] = PlainResourceSerializer(**kwargs)
        if self.instance:
            fields['parent'].read_only = False
            fields['parent'].queryset = models.Resource.objects.filter(
                is_collection=True)
        return fields
