# Contributing to RobotsAndSitemapCheck

We love your input! We want to make contributing to RobotsAndSitemapCheck as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RobotsAndSitemapCheck.git
   cd RobotsAndSitemapCheck
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Code Quality Standards

- Use [Black](https://github.com/psf/black) for code formatting
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Add type hints to all functions
- Maintain test coverage for new code
- Document new functions and modules

## Running Tests

```bash
pytest
```

## License
By contributing, you agree that your contributions will be licensed under its MIT License.
