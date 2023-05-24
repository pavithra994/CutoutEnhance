from setuptools import setup, find_packages

setup(
    name="cutout",
    version="1.0.1",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
long_description="This package will upload a image into cutout.pro and download the enhanced image.",
long_description_content_type="text/markdown",
install_requires=["requests"],
)