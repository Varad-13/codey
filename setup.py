from setuptools import setup, find_packages

setup(
    name='codestorm',
    version='0.1.0',
    packages=find_packages(include=['codestorm', 'codestorm.*']),
    include_package_data=True,
    install_requires=[
        'openai',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'codestorm=codestorm.cli:main'
        ]
    },
    author='Varad Joshi',
    description='Codestorm package providing AI tooling.',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
