File Collection Index
=====================

[![Build Status](https://travis-ci.org/tumb1er/fci.svg?branch=master)](https://travis-ci.org/tumb1er/fci)
[![codecov](https://codecov.io/gh/tumb1er/fci/branch/master/graph/badge.svg)](https://codecov.io/gh/tumb1er/fci)


**FCI** is Django application for file organization. It does not provide
any storage facilities or file content management. It only stores
file metadata and hierarchy.

Usage
-----

FCI can be used as standalone application or as a part of django 
project.

`standalone` provides basic Django project structure to play with.

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
    "metadata": {},
    "parent": 1
}
```

### Create file
```
POST /fci/resources/parent/
Content-Type: application/json

{
  "is_collection": true,
  "name": "file.jpg",
  "metadata": {
    "mime-type": "image/jpeg"
  }
}

HTTP/1.1 201 Created

{
    "id": 3,
    "is_collection": false,
    "url": "/fci/resources/parent/file.txt",
    "created": "2016-08-08T02:05:34.234343Z",
    "modified": "2016-08-08T02:05:34.234343Z",
    "name": "file.txt",
    "metadata": {
        "mime-type": "image/jpeg"
     },
    "parent": 1
}
```

### Move/rename resource

```
PATCH /fci/resources/parent/file.txt

parent=2&name=new_file.txt

HTTP/1.1 200 OK

{
    "id": 3,
    "is_collection": false,
    "url": "/fci/resources/parent/dir/new_dir/new_file.txt",
    "created": "2016-08-08T02:05:34.234343Z",
    "modified": "2016-08-08T02:06:40.731572Z",
    "name": "new_file.txt",
    "metadata": {
        "mime-type": "image/jpeg"
     },
    "parent": 2
}
```
