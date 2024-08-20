from setuptools import setup, find_packages

with open("README.md", "r") as f:
    full_readme = f.read()

setup(
    author="Matt Triano",
    name="dwh_api",
    version="0.1.0",
    description="A pythonic interface to my data warehouse.",
    long_description=full_readme,
    long_description_content_type="text/markdown",
    packages=["dwh_api"],
    install_requires=[
        "pandas",
        "psycopg2-binary",
        "sqlalchemy>=2.0",
        "GeoAlchemy2",
    ],
)
