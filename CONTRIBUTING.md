# Contributing to GoldenIT Microsoft Entra Batch Email Method Adder

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and constructive
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Issues

When reporting issues, please include:
- **Description**: Clear description of the problem
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, dependencies versions
- **Logs**: Relevant log messages (remove sensitive information)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:
- Clear description of the enhancement
- Use case and benefits
- Potential implementation approach (if applicable)
- Any security considerations

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, focused commits
3. **Test thoroughly** before submitting
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

#### Pull Request Guidelines

- **One feature per PR**: Keep changes focused and manageable
- **Clear commit messages**: Use descriptive commit messages
- **Code style**: Follow existing code style and conventions
- **Comments**: Add comments for complex logic
- **Security**: Consider security implications of all changes

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jhossain1509/Microsoft-security.git
cd Microsoft-security
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Run the application:
```bash
python GoldenIT-Microsoft-Entra.py
```

## Code Style

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Keep functions focused and reasonably sized
- Add docstrings for classes and complex functions
- Use type hints where appropriate

## Testing

- Test all changes thoroughly before submitting
- Include test cases for new features
- Verify existing functionality still works
- Test with different input formats and edge cases

## Security Considerations

When contributing, always consider:
- **Credential handling**: Never log or expose credentials
- **Input validation**: Validate and sanitize all inputs
- **Error messages**: Don't expose sensitive information in errors
- **Dependencies**: Keep dependencies updated and secure
- **API changes**: Be aware of changes to Microsoft APIs

## Documentation

Update documentation when:
- Adding new features
- Changing existing functionality
- Fixing significant bugs
- Adding new configuration options

Documentation should be:
- Clear and concise
- Include examples where helpful
- Up-to-date with code changes

## Commit Message Format

Use clear, descriptive commit messages:
```
Add feature: Brief description

Detailed explanation of what changed and why,
if needed for complex changes.
```

Examples:
- `Fix: Resolve timeout issue in email input detection`
- `Add: Support for additional CSV column names`
- `Update: Improve error handling in login process`
- `Docs: Add troubleshooting section to README`

## Review Process

- Maintainers will review pull requests as time permits
- Address feedback constructively
- Be patient - reviews may take time
- Once approved, changes will be merged

## Questions?

If you have questions about contributing:
- Check existing documentation
- Review closed issues and pull requests
- Open a new issue with your question

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing!
