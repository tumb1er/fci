# coding: utf-8
from rest_framework import exceptions, viewsets, status
from rest_framework.response import Response

from fci.index import models, serializers


class ResourceView(viewsets.ModelViewSet):
    serializer_class = serializers.ResourceSerializer

    queryset = models.Resource.objects.all()
    lookup_field = 'path'
    lookup_value_regex = '.*'
    #
    # def get_queryset(self):
    #     resource = self.get_object()
    #     return type(resource).objects.get_queryset()

    def get_object(self):
        path = self.kwargs.get('path') or None
        root = models.Directory.objects.get(parent=None)
        parts = path.strip('/').split('/') if path is not None else []
        resource = root
        i = 0
        for part in parts:
            try:
                resource = models.Directory.objects.get(parent=resource,
                                                        name=part)
                i += 1
            except models.Directory.DoesNotExist:
                break

        if i < len(parts) - 1:
            # не дошли до конца
            raise exceptions.NotFound()
        elif i < len(parts):
            try:
                resource = models.File.objects.get(parent=resource,
                                                   name=parts[-1])
            except models.File.DoesNotExist:
                raise exceptions.NotFound()
        return resource

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        resp = super(ResourceView, self).retrieve(request, *args, **kwargs)
        # resp.data.serializer.instance = None
        return resp

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.initial_data['parent'] = self.get_object().pk
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['is_collection']:
            serializer = serializers.DirectorySerializer(data=request.data)
        else:
            serializer = serializers.FileSerializer(data=request.data)
        serializer.initial_data['parent'] = self.get_object().pk
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        resp = Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)
        return resp
