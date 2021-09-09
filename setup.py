import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jetvision",
    version="0.0.2",
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
    ],
    package_dir={"jetvision": "jetvision"},
    packages=setuptools.find_packages(where=""),
    python_requires=">=3.6",
    install_requires=[
        'opencv-python>=4.5',
        'numpy>1.19'
    ]
)
