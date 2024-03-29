import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as fh:
    install_requires=fh.readlines()

setuptools.setup(
    name="id3cleaner", # Replace with your own username
    version="0.1.0",
    author="Eric Miller",
    author_email="sosheskaz.github.io@gmail.com",
    description="Easily clean and tweak ID3 tags from the command line.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sosheskaz/id3cleaner",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'id3clean=id3cleaner.entrypoint:main'
        ]
    },
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
