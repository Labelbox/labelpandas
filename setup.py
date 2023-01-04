import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name='labelpandas',
  version='0.0.85',
  packages=setuptools.find_packages(),
  url='https://github.com/Labelbox/labelpandas',
  description='Labelbox Connector for Pandas',
  long_description=long_description,
  long_description_content_type="text/markdown",
  author_email="raphael@labelbox.com",
  install_requires=["labelbox", "labelbase", "packaging"]
)
