# coding: utf-8
import json

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from fci.index import models


class ResourceAPITestCase(APITestCase):
    """ Resource viewset test case."""

    maxDiff = None

    def setUp(self):
        super(ResourceAPITestCase, self).setUp()
        self.root = models.Directory.objects.create(name='/')
        self.dir = models.Directory.objects.create(parent=self.root,
                                                   name='dir')
        self.file = models.File.objects.create(parent=self.root,
                                               name='file.txt')

    def url(self, path=''):
        return reverse('resource-detail', kwargs={'path': path})

    def dump_resource(self, res, extra=()):
        data = {
            'id': res.id,
            'name': res.name,
            'parent': res.parent_id,
            'created': res.created.isoformat().replace('+00:00', 'Z'),
            'modified': res.modified.isoformat().replace('+00:00', 'Z'),
            'url': self.url(res.path),
            'is_collection': res.is_collection,
            'metadata': res.metadata
        }
        for f in extra:
            data[f] = getattr(res, f)
        return data

    def testGetRootInfo(self):
        """ Check resource api GET request."""
        response = self.client.get(self.url(), format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data
        descendants = data.pop('descendants', None)
        expected = self.dump_resource(self.root)
        self.assertDictEqual(data, expected)
        self.assertIsNotNone(descendants)
        self.assertEqual(len(descendants), 2)
        d = descendants[0]
        expected = self.dump_resource(self.dir)
        self.assertDictEqual(d, expected)

        f = descendants[1]
        expected = self.dump_resource(self.file)
        self.assertDictEqual(f, expected)

    def testGetChildDir(self):
        """ Check detail view for child directories."""
        response = self.client.get(self.url(path=self.dir.path), format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['id'], self.dir.id)
        self.dir2 = models.Directory.objects.create(name='d2', parent=self.dir)
        response = self.client.get(self.url(path=self.dir2.path), format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['id'], self.dir2.id)

    def testFileResourceDoesNotExist(self):
        """ Check that detail view correctly handles unexistent files."""
        response = self.client.get(self.url(path='dir/not_exists.txt'),
                                   format='json')
        self.assertEqual(response.status_code, 404)

    def testDirLeafResourceDoesNotExist(self):
        """
        Check that detail view correctly handles unexistent dirs while
        parent dir exists.
        """
        response = self.client.get(self.url(path='dir/dir_not_exists'),
                                   format='json')
        self.assertEqual(response.status_code, 404)

    def testInnerResourceDoesNotExist(self):
        """ Check that detail view correctly handles unexistent dirs inside
        resource path.
        """
        response = self.client.get(self.url(path='dir/not_exists/file.txt'),
                                   format='json')
        self.assertEqual(response.status_code, 404)

    def testCreateDir(self):
        """ Test directory creation."""
        data = {'a': 'b'}
        response = self.client.post(self.url(self.dir.path), data={
            'is_collection': True, 'name': 'new_dir', 'metadata': data
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(models.Directory.objects.filter(
            parent=self.dir, name='new_dir').exists())
        new = models.Directory.objects.get(parent=self.dir, name='new_dir')

        expected = self.dump_resource(new)
        self.assertDictEqual(response.data, expected)

    def testCreateFile(self):
        """ Test directory creation."""
        data = {'a': 'b'}
        response = self.client.post(self.url(self.dir.path), data={
            'is_collection': False, 'name': 'new_file', 'metadata': data
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(models.File.objects.filter(
            parent=self.dir, name='new_file').exists())
        new = models.File.objects.get(parent=self.dir, name='new_file')

        expected = self.dump_resource(new, extra=['size'])
        self.assertDictEqual(response.data, expected)

    def testRootAsAPIView(self):
        """ Checks that root resource works correctly with API format."""
        response = self.client.get(self.url(), data={'format': 'api'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Resource Instance", response.content)

    def testRootAPITrailingSlash(self):
        """ Checks redirect to root resource with trailing slash."""
        response = self.client.get(self.url().rstrip('/'),
                                   data={'format': 'api'})
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url.replace('http://testserver', ''), self.url())

    def testValidation(self):
        """ Checks validation while creating resource."""
        response = self.client.post(self.url(self.file.path), data={
            'is_collection': True, 'name': 'new/dir'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, {
            'name': ["Enter a valid value."],
            'parent': ["Parent must be a collection"],
            'metadata': ["This field is required."]
        })

    def testMove(self):
        """ Checks move resource to other parent."""
        response = self.client.patch(self.url(self.file.path), data={
            "parent": self.dir.id
        })
        self.assertEqual(response.status_code, 200)

        self.file.refresh_from_db()
        self.assertEqual(self.file.parent_id, self.dir.id)

    def testMoveValidateCollection(self):
        """ Checks that parent must be a collection on move."""
        response = self.client.patch(self.url(self.dir.path), data={
            "parent": self.file.id
        })
        self.assertEqual(response.status_code, 400)
        error = 'Invalid pk "%s" - object does not exist.' % self.file.id
        self.assertDictEqual(response.data, {'parent': [error]})

    def testChangeResourceTypeForbidden(self):
        """ Checks that is_collection flag can't be changed by PATCH request."""
        response = self.client.patch(self.url(self.dir.path), data={
            "is_collection": False
        })
        self.assertEqual(response.status_code, 400)
        error = 'Resource type cannot be changed after creation'
        self.assertDictEqual(response.data, {'is_collection': [error]})

    def testChangeMetadata(self):
        """ Checks metadata update via PATCH request."""
        meta = {"new": "data"}
        response = self.client.patch(self.url(self.dir.path), data={
            'metadata': meta
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.dir.refresh_from_db()
        self.assertDictEqual(self.dir.metadata, meta)

    def testChangeMetadataViaJSONEncodedForm(self):
        """ Checks that metadata can be passed as JSON string."""
        meta = {"new": "data"}
        response = self.client.patch(self.url(self.dir.path), data={
            'metadata': json.dumps(meta)})
        self.assertEqual(response.status_code, 200)
        self.dir.refresh_from_db()
        self.assertDictEqual(self.dir.metadata, meta)


