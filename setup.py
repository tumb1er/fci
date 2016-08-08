from setuptools import setup

setup(
    name='fci',
    version='0.0.1',
    packages=['fci',
              'fci.index',
              'fci.index.migrations',
              'fci.standalone'],
    url='https://github.com/tumb1er/fci',
    license='Beer License',
    author='Sergey Tikhonov',
    author_email='zimbler@gmail.com',
    description='File Collection Index - Django app for file hierarchy',
    install_requires=[
        'Django',
        'djangorestframework',
        'django-extensions'
    ]
)
