from setuptools import setup, find_packages
setup(
    name = 'rtsptogo',
    version = '0.1.1',
    description = 'rtsptogo is a tivo togo proxy serving mp4 video over RSTP',
    long_description=open('README').read(),
    keywords = 'tivo rstp mobile',
    author = 'Jason Michalski',
    author_email = 'armooo@armooo.net',
    url = 'http://github.com/armooo/rtsptogo/',
    license = 'GPL',
    packages = find_packages(),
    include_package_data = True,
    install_requires = ['web.py'],
    setup_requires = ['setuptools-git'],
    entry_points = {
        'console_scripts' : ['rtsptogo = rtsptogo.main:main',]
    },
)
