from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lotto-prediction",
    version="0.1.0",
    author="Korean Lotto Prediction Team",
    description="한국 로또 6/45 번호 예측 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lotto-prediction",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.1.4",
        "numpy>=1.26.2",
        "scikit-learn>=1.3.2",
        "xgboost>=2.0.3",
        "streamlit>=1.29.0",
        "plotly>=5.18.0",
        "matplotlib>=3.8.2",
        "seaborn>=0.13.0",
        "APScheduler>=3.10.4",
        "loguru>=0.7.2",
        "pyyaml>=6.0.1",
        "sqlalchemy>=2.0.23",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "jupyter>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lotto-collect=src.data.collector:main",
            "lotto-train=src.models.train:main",
            "lotto-predict=src.prediction.predictor:main",
        ],
    },
)
