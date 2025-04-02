from setuptools import setup, find_packages

setup(
    name="nocksup",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "requests",
        "websocket-client",
        "protobuf",
    ],
    author="gyovannyvpn123",
    author_email="mdanut159@gmail.com",
    description="A Python library for WhatsApp communication compatible with current protocols.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/gyovannyvpn123/Nocksup",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)