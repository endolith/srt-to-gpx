from setuptools import setup

setup(
    name="srt-to-gpx",
    version="1.0.0",
    py_modules=["srt_to_gpx"],
    entry_points={
        "console_scripts": [
            "srt-to-gpx=srt_to_gpx:main",
        ],
    },
    install_requires=[],
    author="Your Name",
    author_email="your_email@example.com",
    description="Convert SRT files with GPS data to GPX format.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/srt-to-gpx",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: CC0 1.0 Universal (CC0 1.0)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
