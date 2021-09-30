import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jetvision",
    version="0.0.3",
    author="Tomasz Lewicki",
    author_email="tlewicki@nvidia.com",
    description="jetvision: Computer Vision package for Nvidia Jetson platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomek-l/nv-jetvision",
    project_urls={
        "Bug Tracker": "https://github.com/tomek-l/nv-jetvision/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    packages=setuptools.find_packages(where="."),
    package_dir={"jetvision": "jetvision"},
    include_package_data=True,
    package_data={
        "": ["*.txt"], # For nvinfer config files
        },
    python_requires=">=3.6",
    install_requires=[
        'numpy>=1.18'  # TODO: test with >1.0-1.19
    ]
)
