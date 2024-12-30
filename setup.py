from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="TerminalTelemetry",
    version="0.1",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    description="Terminal Telemetry - A PyQt6 Terminal Emulator with Device Telemetry",
    url="https://github.com/scottpeterman/termtel",
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
            'termtel=termtel.termtel:main',
        ],
        'gui_scripts': [
            'termtel-no-con=termtel.termtel:main',
        ],
    },
    python_requires=">=3.9",
)