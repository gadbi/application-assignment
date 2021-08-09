from setuptools import setup, find_packages


install_requires = ['aio_pika','flask','psycopg2']

setup(
    name='consumer',
    author='',
    author_email='',
    version='1.0.1',
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'scripts']),
    include_package_data=True,
    package_data={
        'consumer': ['templates/*.html', 'templates/**/*.html']
    },
    entry_points={
          'flask.commands': [
            'consumer = consumer.commands:cli'
          ],
          'console_scripts': [
              'consumer = consumer.main:main'
          ],
      },
    install_requires=install_requires,
    test_suite="tests",
    zip_safe=False)
