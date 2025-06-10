from setuptools import setup, find_packages

setup(
    name="epochvc",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={
        'console_scripts': [
            'epochvc=epoch.entry:main'
        ],
    },
    author="Nqabenhle Mlaba",
    author_email="nqabenhlemlaba22@gmail.com",
    description="A small version control system inspired by Git",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lindelwa122/epoch",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
