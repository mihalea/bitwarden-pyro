import setuptools
from bitwarden_pyro.settings import NAME, VERSION

setuptools.setup(name='bitwarden_pyro',
                 version=VERSION,
                 description='Bitwarden python interface with Rofi',
                 url='https://github.com/mihalea/i3expo',
                 author='Mircea Mihalea',
                 author_email='mircea@mihalea.ro',
                 license='MIT',
                 zip_safe=False,
                 include_package_data=True,
                 packages=setuptools.find_packages(),
                 entry_points={
                     'console_scripts': [
                         f'{NAME}=bitwarden_pyro.bwpyro:run',
                     ]
                 })
