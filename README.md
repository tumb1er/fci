File Collection Index
=====================

**FCI** is Django application for file organization. It does not provide
any storage facilities or file content management. It only stores
file metadata and hierarchy.

Usage
-----

FCI can be used as standalone application or as a part of django 
project.

Standalone application example is installed as `fci.standalone` package.
It only provides basic Django project structure to play with.

To use FCI in Django-project the only thing you need is:

* Add `fci.index` to `INSTALLED_APPS`
* OK, two things: run migrations.

Code example
------------

```python
>>> from fci.index.models import Directory, File
>>> root = Directory.objects.create(name='/', parent=None)
>>> dir = Directory.objects.create(name='dir', parent=root)
>>> file = File.objects.create(name='file.txt', parent=dir)
>>> file.path
dir/file.txt
```

API example
-----------

### Create dir
```
POST /fci/resources/parent/dir/

is_collection=true&name=new_dir

HTTP/1.1 201 Created

{
    "id": 2,
    "is_collection": true,
    "url": "/fci/resources/parent/dir/new_dir",
    "created": "2016-08-08T02:04:45.347865Z",
    "modified": "2016-08-08T02:04:45.348723Z",
    "name": "new_dir",
    "metadata": "{}",
    "parent": 1
}
```
