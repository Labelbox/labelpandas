from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='labelpandas',
    version='0.1.38',
    author='Labelbox',
    author_email="raphael@labelbox.com",
    description='Labelbox Connector for Pandas',
    long_description=long_description,
    long_description_content_type="text/markdown",    
    url='https://github.com/Labelbox/labelpandas',    
    packages=find_packages(),
    install_requires=["labelbox[data]", "labelbase", "packaging"]
)
