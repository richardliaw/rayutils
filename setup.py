from setuptools import setup

setup(
    name="ray2",
    version='0.1',
    install_requires=[
        'ray',
        'Click',
    ],
    entry_points={
        "console_scripts": ["ray2=rayutils:cli"]
    }
)
