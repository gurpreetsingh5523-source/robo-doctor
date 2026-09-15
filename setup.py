from setuptools import setup, find_packages

setup(
    name="amrit-research-os",
    version="6.2.0",
    description="Autonomous Medical Research & Personalized Health System",
    author="Gurpreet Singh",
    author_email="gurpreet@amrit-research.org",
    url="https://github.com/gurpreet/amrit-research-os",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "networkx>=3.0",
        "pydantic>=2.0.0",
        "websockets>=11.0",
    ],
    extras_require={
        "telegram": ["python-telegram-bot>=20.0"],
        "discord": ["discord.py>=2.0"],
        "all": ["python-telegram-bot>=20.0", "discord.py>=2.0"],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: Public Domain",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="medical research AI autonomous health personalized medicine",
    entry_points={
        "console_scripts": [
            "amrit-dashboard=src.dashboard.dashboard:main",
            "amrit-chat=src.dashboard.chat_dashboard:app",
            "amrit-telegram=src.dashboard.telegram_bot:main",
        ],
    },
)
