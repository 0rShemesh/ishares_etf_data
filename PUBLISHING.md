# Publishing to PyPI

This document outlines the steps to publish the `ishares_etf_data` package to PyPI.

## Publishing Methods

### Method 1: Automated Publishing with GitHub Actions (Recommended)

The repository includes GitHub Actions workflows that automate the testing, building, and publishing process.

To use this method:

1. **Update Version Numbers** in:
   - `pyproject.toml` - Look for the `version = "x.y.z"` line
   - `setup.py` - Look for the `version='x.y.z'` line 
   - `src/ishares_etf_data/__init__.py` - Look for the `__version__ = "x.y.z"` line

2. **Create a new GitHub Release**:
   - Go to the repository on GitHub
   - Click "Releases" then "Create a new release"
   - Create a new tag (e.g., `v0.1.0`) that matches your version number
   - Add release notes describing the changes
   - Click "Publish release"

3. **Monitor the Workflow**:
   - The workflow will automatically:
     - Run tests on multiple Python versions
     - Build the package
     - Publish to TestPyPI
     - Publish to PyPI

   - You can monitor progress in the "Actions" tab of your repository

### Method 2: Manual Publishing

If you prefer to publish manually, follow these steps:

## Prerequisites

1. Create accounts on:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (recommended for testing)

2. Install required tools:
   ```bash
   pip install build twine
   ```
   
   or using the dev dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Steps to Publish Manually

### 1. Update Version Numbers

Make sure the version number is updated in:
- `pyproject.toml` - Look for the `version = "x.y.z"` line
- `setup.py` - Look for the `version='x.y.z'` line 
- `src/ishares_etf_data/__init__.py` - Look for the `__version__ = "x.y.z"` line

Follow [Semantic Versioning](https://semver.org/) principles:
- Increment MAJOR version when you make incompatible API changes
- Increment MINOR version when you add functionality in a backward compatible manner
- Increment PATCH version when you make backward compatible bug fixes

### 2. Clean the Distribution Directory

Remove any old distribution files:
```bash
rm -rf dist/ build/ *.egg-info/
```

### 3. Build the Package

Build both source distribution and wheel:
```bash
python -m build
```

This will create files in the `dist/` directory.

### 4. Test with TestPyPI (Recommended)

Upload to TestPyPI:
```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for your TestPyPI username and password.

Test the installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ishares_etf_data
```

### 5. Upload to PyPI

When you're ready to publish to the real PyPI:
```bash
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

### 6. Verify the Upload

Check your package on PyPI at:
```
https://pypi.org/project/ishares_etf_data/
```

Test installation from PyPI:
```bash
pip install ishares_etf_data
```

## Automating with API Tokens

For automation, you can use API tokens instead of passwords. Store them in a `~/.pypirc` file:

```
[testpypi]
username = __token__
password = your-test-pypi-token

[pypi]
username = __token__
password = your-pypi-token
```

Or set environment variables:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your-token
```

## Troubleshooting

- **"File already exists"**: If you get an error saying the file already exists, it means you can't upload the same version twice. You must bump the version number.
- **README not displaying properly**: Verify your Markdown syntax in the README.md file.
- **Missing dependencies**: Make sure all dependencies are listed in both `pyproject.toml` and `setup.py`.
- **Workflow failures**: Check the GitHub Actions logs for detailed error information.

## Resources

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [PyPI Package Publishing Tutorial](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions for Python Packaging](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) 