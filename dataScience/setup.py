import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

    setuptools.setup(
        name="gc-ml",
        version="0.0.1",
        author="Booz Allen Hamilton",
        author_email="ha_robert@example.com",
        description="Package for GAMECHANGER ML modules",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://bitbucket.di2e.net/projects/UOT/repos/gamechanger/browse",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "License :: ",
            "Operating System :: OS Independent",
        ],
        python_requires="==3.6.*",
    )
