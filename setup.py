import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jetvision",
    version="0.0.1",
    author="Tomasz Lewicki",
    author_email="tlewicki@nvidia.com",
    description="jetvision: Computer Vision package for Nvidia Jetson platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomek-l/nv-jetvision",
    project_urls={
        "Bug Tracker": "https://github.com/tomek-l/nv-jetvision",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: JetPack 4.5 or higher",
    ],
    package_dir={"": "jetvision"},
    packages=setuptools.find_packages(where="jetvision"),
    python_requires=">=3.6",
)