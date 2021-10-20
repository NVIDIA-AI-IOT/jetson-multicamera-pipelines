import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jetmulticam",
    version="0.1.0",
    author="Tomasz Lewicki",
    author_email="tlewicki@nvidia.com",
    description="JetMutliCam: Easy-to-use realtime CV/AI pipelines for Nvidia Jetson Platform.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomek-l/nv-jetmulticam",
    project_urls={
        "Bug Tracker": "https://github.com/tomek-l/nv-jetmulticam/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    packages=setuptools.find_packages(where="."),
    package_dir={"jetmulticam": "jetmulticam"},
    include_package_data=True,
    package_data={
        "": ["*.txt"], # For nvinfer config files
        },
    python_requires=">=3.6",
    install_requires=[
        'numpy>=1.18'  # TODO: test with >1.0-1.19
    ]
)
