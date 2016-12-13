from setuptools import setup, find_packages

def readme():
    with open('README.org') as f:
        return f.read()

setup(name='Machine Cycles',
      version='0.1',
      description='Log machine cycle time',
      long_description='Log machine cycle time to mongodb',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.4',
          'Topic :: Communications',
      ],
      keywords='arduino',
      url='http://github.com/kcjuntunen/cycles',
      author='K. C. Juntunen',
      author_email='kcjuntunen@amstore.com',
      license='GPLv2',
      packages=['cycles'],
      install_requires=[
          'eve',
          'pymongo',
          'python-dateutil',
          'pyserial',
          'evdev',
      ],
      include_package_data=True,
      zip_safe=False,
      scripts=['bin/cycles'],
      test_suite='nose.collector',
      tests_require=['nose'],
)
