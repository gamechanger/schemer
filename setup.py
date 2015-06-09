import setuptools


setuptools.setup(
    name="Schemer",
    version="0.2.8",
    author="Tom Leach",
    author_email="tom@gc.io",
    description="Powerful schema-based validation of Python dicts",
    license="BSD",
    keywords="validation schema dict list",
    url="http://github.com/gamechanger/schemer",
    packages=["schemer"],
    long_description="Schemer allows users to declare schemas for Python dicts and lists and then validate actual dicts and lists against those schemas.",
    tests_require=['mock', 'nose']
    )
