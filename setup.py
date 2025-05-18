from setuptools import setup, find_packages

setup(
    name='ishares_etf_data',
    version='0.1.0', # Keep in sync with pyproject.toml
    author='0r Shemesh', # Keep in sync with pyproject.toml
    author_email='0rshemesh at mail', # Keep in sync with pyproject.toml
    description='An UNOFFICIAL Python library to fetch holdings data for iShares Russell 1000 ETF. Not affiliated with BlackRock or iShares.', # Keep in sync
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/0rshemesh/ishares_etf_data', # Keep in sync
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'requests>=2.25.0', # Keep in sync with pyproject.toml
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
) 