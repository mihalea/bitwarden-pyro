import setuptools
from bitwarden_pyro.settings import NAME, VERSION

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='bitwarden_pyro',
                 version=VERSION,
                 description='Bitwarden python interface built with Rofi',
                 url='https://github.com/mihalea/bitwarden-pyro',
                 author='Mircea Mihalea',
                 author_email='mircea@mihalea.ro',
                 license='MIT',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 zip_safe=False,
                 include_package_data=True,
                 install_requires=['pyyaml'],
                 packages=setuptools.find_packages(),
                 entry_points={
                     'console_scripts': [
                         f'{NAME}=bitwarden_pyro.bwpyro:run',
                     ]
                 })
