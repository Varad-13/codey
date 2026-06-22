import subprocess
import sys

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


class _PlaywrightMixin:
    def _install_chromium(self):
        try:
            print("codey: installing Playwright Chromium browser (one-time ~120 MB)...")
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
            )
        except Exception as e:
            print(f"codey: could not auto-install Chromium: {e}")
            print("codey: run manually: playwright install chromium")


class InstallWithPlaywright(_PlaywrightMixin, install):
    def run(self):
        super().run()
        self._install_chromium()


class DevelopWithPlaywright(_PlaywrightMixin, develop):
    def run(self):
        super().run()
        self._install_chromium()


setup(
    name='codey',
    version='0.3.7',
    packages=find_packages(include=['codey', 'codey.*']),
    include_package_data=True,
    install_requires=[
        'openai',
        'python-dotenv',
        'prompt_toolkit',
        'playwright',
        'Pillow',
    ],
    cmdclass={
        'install': InstallWithPlaywright,
        'develop': DevelopWithPlaywright,
    },
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
