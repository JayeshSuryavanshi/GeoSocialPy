from setuptools import setup, find_packages

setup(
    name="GeoSocialPy",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "tweepy",
        "geopy"
    ],
    author="Jayesh Kishor Suryavanshi",
    author_email="jayeshki@buffalo.edu",
    description="A Python library to fetch and analyze geospatial data from social media",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/JayeshSuryavanshi/GeoSocialPy",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
