from setuptools import setup, find_packages

setup(
    name="job-scraping-tool",
    version="1.0.0",
    description="Job scraping and export tool for LeapGen AI",
    author="Anurag & Hemanth",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.10",
        "python-dotenv>=0.19.0"
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'job-scraper=job_scraper:main',
        ],
    },
)