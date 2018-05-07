from setuptools import setup

setup(
    name="rayutils",
    version='0.1',
    install_requires=[
        'ray',
        'Click',
    ],
    entry_points={
        "console_scripts": ["ray2=rayutils.rayutils:cli"]
    }
)
