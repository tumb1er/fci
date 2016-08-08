# coding: utf-8
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from fci.index import models


class ResourceAPITestCase(APITestCase):
    """ Resource viewset test case."""

    maxDiff = None

    def setUp(self):
        super(ResourceAPITestCase, self).setUp()
        self.root = models.Directory.objects.create(name='/')

    def url(self, path=''):
        return reverse('resource-detail', kwargs={'path': path})

    def testGetRootInfo(self):
        """ Check resource api GET request."""
        self.dir = models.Directory.objects.create(parent=self.root,
                                                   name='dir')
        self.file = models.File.objects.create(parent=self.root,
                                               name='file.txt')
        response = self.client.get(self.url(), format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data
        print(data)
        expected = {
            'id': self.root.id,
            'name': self.root.name,
            'parent': None,
            'created': self.root.created.isoformat().replace('+00:00', 'Z'),
            'modified': self.root.modified.isoformat().replace('+00:00', 'Z'),
            'url': self.url(self.root.path),
            'is_collection': True,
            'metadata': {}
        }
        descendants = data.pop('descendants', None)
        self.assertDictEqual(data, expected)
        self.assertIsNotNone(descendants)
        self.assertEqual(len(descendants), 2)
        d = descendants[0]
        expected = {
            'id': self.dir.id,
            'name': self.dir.name,
            'parent': self.root.id,
            'created': self.dir.created.isoformat().replace('+00:00', 'Z'),
            'modified': self.dir.modified.isoformat().replace('+00:00', 'Z'),
            'url': self.url(self.dir.path),
            'is_collection': True,
            'metadata': {}
        }
        self.assertDictEqual(d, expected)

        f = descendants[1]
        expected = {
            'id': self.file.id,
            'name': self.file.name,
            'parent': self.root.id,
            'created': self.file.created.isoformat().replace('+00:00', 'Z'),
            'modified': self.file.modified.isoformat().replace('+00:00', 'Z'),
            'url': self.url(self.file.path),
            'is_collection': False,
            'metadata': {}
        }
        self.assertDictEqual(f, expected)


