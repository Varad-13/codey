from setuptools import setup, find_packages

setup(
    name='codey',
    version='0.1.0',
    packages=find_packages(include=['codey', 'codey.*']),
    include_package_data=True,
    install_requires=[
        'openai',
        'python-dotenv',
        'prompt_toolkit'
    ],
    entry_points={
        'console_scripts': [
            'codey=codey.cli:main'
        ]
    },
    author='Varad Joshi',
    description='Codey is a in terminal AI assistant built for developers.',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent', 
    ],
    python_requires='>=3.7',
)
