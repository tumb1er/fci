# coding: utf-8
import mock
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from fci.index import models


class ResourceTestCaseBase(TestCase):
    def setUp(self):
        super(ResourceTestCaseBase, self).setUp()
        self.root = models.Resource.objects.create(name='/', is_collection=True)


class ResourceModelTestCase(ResourceTestCaseBase):

    def testResourceCircularReference(self):
        """ Checks Directory can't become a parent of itself."""
        a = models.Resource.objects.create(parent=self.root, name='a', 
                                           is_collection=True)
        b = models.Resource.objects.create(parent=a, name='b',
                                           is_collection=True)
        a.parent = b
        with self.assertRaises(ValidationError) as e:
            a.clean()

        self.assertDictContainsSubset(
            {'parent': ["Resource is a parent of itself"]},
            e.exception.message_dict)

    def testCleanRootResource(self):
        """ Checks root resource clean."""
        self.root.clean()

    def testResourceCircularReferenceDirect(self):
        """ Checks Directory can't become a direct parent of itself."""
        a = models.Resource.objects.create(parent=self.root, name='a',
                                           is_collection=True)
        a.parent = a
        with self.assertRaises(ValidationError) as e:
            a.clean()

        self.assertDictContainsSubset(
            {'parent': ["Resource is a parent of itself"]},
            e.exception.message_dict)

    def testResourcePath(self):
        """ Checks correctness of resource path."""
        a = models.Resource.objects.create(parent=self.root, name='a',
                                           is_collection=True)
        b = models.Resource.objects.create(parent=a, name='b',
                                           is_collection=True)
        c = models.Resource.objects.create(parent=b, name='c',
                                           is_collection=False)
        self.assertEqual(c.path, 'a/b/c')

    def testRootPathIsOK(self):
        """ Checks that root path is returned correctly."""
        self.assertEqual(self.root.path, '')

    def testResourceToStr(self):
        """ Check Resource.__str__ method."""
        a = models.Resource.objects.create(parent=self.root, name='a',
                                           is_collection=True)
        self.assertEqual(str(a), a.path)

    def testResourceParentIsCollection(self):
        """ Checks that resource parent must be a colleciton."""
        a = models.Resource.objects.create(parent=self.root, name='a',
                                           is_collection=False)
        b = models.Resource(parent=a, name='b')

        with self.assertRaises(ValidationError) as e:
            b.clean()

        self.assertDictContainsSubset(
            {'parent': ["Parent must be a collection"]},
            e.exception.message_dict)

    def testResourceNameValidation(self):
        """ Checks resource name validation."""
        a = models.Resource(parent=self.root, name='a/b')
        with self.assertRaises(ValidationError):
            a.full_clean()


class DirectoryModelTestCase(ResourceTestCaseBase):

    def testDirectoryCreation(self):
        """ Checks Directory model creation."""
        d = models.Directory(name='aaa', parent=self.root)
        d.clean()
        d.save()
        d.refresh_from_db()
        self.assertTrue(d.is_collection)

    def testSaveUpdateFields(self):
        """ Checks that update_fields are handled correctly while saving dir."""
        d = models.Directory.objects.create(name='aaa', parent=self.root)
        d.is_collection = False
        d.save(update_fields=['name'])
        d.refresh_from_db()
        self.assertTrue(d.is_collection)


class FileModelTestCase(ResourceTestCaseBase):

    def testDirectoryCreation(self):
        """ Checks Directory model creation."""
        d = models.File(name='aaa', parent=self.root)
        d.clean()
        d.save()
        d.refresh_from_db()
        self.assertFalse(d.is_collection)

    def testSaveUpdateFields(self):
        """
        Checks that update_fields are handled correctly while saving file.
        """
        f = models.File.objects.create(name='aaa', parent=self.root)
        f.is_collection = True
        f.save(update_fields=['name'])
        f.refresh_from_db()
        self.assertFalse(f.is_collection)


class MetadataModelTestCase(ResourceModelTestCase):

    def setUp(self):
        super(MetadataModelTestCase, self).setUp()
        self.ct = ContentType.objects.get_for_model(self.root)

    def testMetadataCreation(self):
        """ Checks Resource.metadata setter created Metadata object."""
        data = {'a': 'b'}
        self.root.metadata = data
        self.root.save()
        self.assertEqual(models.Metadata.objects.count(), 1)
        m = models.Metadata.objects.get()
        self.assertEqual(m.object_id, self.root.id)
        self.assertEqual(m.content_type_id, self.ct.id)
        self.assertDictEqual(m.data, data)
        r = models.Resource.objects.get(pk=self.root.pk)
        self.assertDictEqual(r.metadata, data)

    def testMetadataUpdate(self):
        """ Checks Resource.metadata setter correctly updates metadata."""
        data = {'a': 'b'}
        self.root.metadata = data
        self.root.save()
        new_data = {'c': 'd'}
        self.root.metadata = new_data
        self.root.save()
        self.assertEqual(models.Metadata.objects.count(), 1)
        m = models.Metadata.objects.get()
        self.assertDictEqual(m.data, new_data)

    def testMetadataDelete(self):
        """
        Checks Resource.metadata setter deletes Metadata model on cleanup.
        """
        data = {'a': 'b'}
        self.root.metadata = data
        self.root.save()
        self.root.metadata = {}
        self.root.save()
        self.assertEqual(models.Metadata.objects.count(), 0)

    def testMetadataDeleteWhileNotPresent(self):
        """
        Checks correct handling of metadata cleanup while not yet present.
        """
        self.root.metadata = {}
        self.root.save()
        self.assertEqual(models.Metadata.objects.count(), 0)

    def testDefaultMetadata(self):
        """ Checks default metadata value."""
        self.assertDictEqual(self.root.metadata, {})

    def testMetadataCache(self):
        """ Checks that metadata is cached."""
        with mock.patch('fci.index.models.Metadata.objects.get') as p:
            data = self.root.metadata
        p.assert_called_once_with(object_id=self.root.pk,
                                  content_type=self.ct)

        with mock.patch('fci.index.models.Metadata.objects.get') as p:
            new_data = self.root.metadata
        self.assertFalse(p.called)
        self.assertIs(data, new_data)
