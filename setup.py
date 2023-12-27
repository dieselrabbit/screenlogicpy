import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="screenlogicpy",
    version="0.10.1",
    author="Kevin Worrel",
    author_email="kevinworrel@yahoo.com",
    description="Interface for Pentair ScreenLogic connected pool controllers over IP via Python",
    license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dieselrabbit/screenlogicpy",
    packages=setuptools.find_packages(include=["screenlogicpy", "screenlogicpy.*"]),
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.10",
    install_requires=[
        "async_timeout>=3.0.0",
    ],
    entry_points={"console_scripts": ["screenlogicpy=screenlogicpy.__main__:main"]},
)
