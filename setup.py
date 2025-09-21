from setuptools import setup

setup(
    name='autogit-cli',
    version='1.0.0',
    description='自动执行 git add, commit 和 push 的CLI工具',
    author='Your Name',
    author_email='your.email@example.com',
    py_modules=['autogit'],
    install_requires=[
        'click>=8.0.0',
    ],
    entry_points={
        'console_scripts': [
            'autogit=autogit:autogit',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control :: Git',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)