import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='labelpandas',
    version='0.1.26',
    author='Labelbox',
    author_email="raphael@labelbox.com",
    description='Labelbox Connector for Pandas',
    long_description=long_description,
    long_description_content_type="text/markdown",    
    url='https://github.com/Labelbox/labelpandas',    
    packages=setuptools.find_packages(),
    install_requires=["labelbox", "labelbase", "packaging"]
)
