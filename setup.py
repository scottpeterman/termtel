from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="TerminalTelemetry",
    version="0.9.3",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    description="Terminal Telemetry - A PyQt6 Terminal Emulator with Device Telemetry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scottpeterman/termtel",
    project_urls={
        "Bug Tracker": "https://github.com/scottpeterman/termtel/issues",
        "Documentation": "https://github.com/scottpeterman/termtel/wiki"
    },
    keywords="terminal, telemetry, ssh, network, automation, pyqt6",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'termtel': [
            'static/**/*',
            'templates/**/*',
            'templates.db'
        ]
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
entry_points={
        'console_scripts': [
            'termtel-con=termtel.termtel:main',
        ],
        'gui_scripts': [
            'termtel=termtel.termtel:main',
        ],
    },
    python_requires=">=3.9",
)