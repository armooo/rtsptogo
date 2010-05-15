from setuptools import setup, find_packages
from version import get_git_version
setup(
    name = 'rtsptogo',
    version = get_git_version(),
    description = 'rtsptogo is a tivo togo proxy serving mp4 video over RSTP',
    long_description=open('README').read(),
    keywords = 'tivo rstp mobile',
    author = 'Jason Michalski',
    author_email = 'armooo@armooo.net',
    url = 'http://github.com/armooo/rtsptogo/',
    license = 'GPL',
    packages = find_packages(),
    include_package_data = True,
    package_data = { '' : ['RELEASE-VERSION'] },
    install_requires = ['web.py'],
    setup_requires = ['setuptools-git'],
    entry_points = {
        'console_scripts' : ['rtsptogo = rtsptogo.main:main']
    },
    classifiers = [
        'Programming Language :: Python',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Internet',
        'Topic :: Multimedia :: Video :: Conversion',
    ]
)
