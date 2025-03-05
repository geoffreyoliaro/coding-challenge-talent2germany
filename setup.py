from setuptools import setup, find_packages

setup(
    name='tenant-screening-match-evaluator',
    version='0.1.0',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'Flask',
        'jellyfish',
        'marshmallow',
    ],
    extras_require={
        'dev': ['pytest'],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A Flask-based tool for evaluating potential matches in tenant screening processes',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/tenant-screening-match-evaluator',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)