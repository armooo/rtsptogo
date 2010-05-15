from setuptools import setup, find_packages
setup(
    name = 'rtsptogo',
    version = '0.1',
    packages = find_packages(),
    include_package_data=True,
    install_requires=['web.py'],
    setup_requires=['setuptools-git'],
    entry_points = {
        'console_scripts' : ['rtsptogo = rtsptogo.main:main',]
    },
)
