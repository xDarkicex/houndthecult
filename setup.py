from setuptools import setup, find_packages

setup(
    name="houndthecult",
    version="1.0.0",
    description="Twitter bot that quotes tweets when mentioned",
    author="HoundTheCult",
    packages=find_packages(),
    install_requires=[
        "tweepy>=4.10.0",
        "python-dotenv>=0.20.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "houndthecult=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json.example"],
    },
)
