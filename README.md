# GoldenIT Microsoft Entra Batch Email Method Adder

A Python-based GUI application for batch adding email authentication methods to Microsoft Entra (formerly Azure AD) accounts. This tool automates the process of adding alternative email addresses as sign-in methods for multiple accounts simultaneously.

## Features

- **Batch Processing**: Process multiple accounts simultaneously with configurable batch size
- **Email Management**: Add multiple email addresses per account automatically
- **2FA Support**: Built-in TOTP (Time-based One-Time Password) support for accounts with 2FA enabled
- **Progress Tracking**: Real-time progress monitoring with detailed logging
- **Error Handling**: Comprehensive error handling with failed email retry functionality
- **Export Capabilities**: Export logs and failed email lists for review and retry
- **Pause/Resume**: Ability to pause and resume batch operations
- **Modern UI**: Dark-themed GUI built with CustomTkinter

## Prerequisites

- Python 3.7 or higher
- Microsoft Entra (Azure AD) account with appropriate permissions
- Valid account credentials (email/password, optional 2FA secrets)

## Dependencies

Install the required Python packages:

```bash
pip install customtkinter playwright
playwright install chromium
```

### Required Packages:
- `customtkinter` - Modern UI framework
- `playwright` - Browser automation
- `tkinter` - Standard Python GUI library (usually pre-installed)

### Standard Library Dependencies:
- `asyncio`, `csv`, `os`, `threading`, `datetime`, `time`
- `struct`, `hmac`, `base64`, `hashlib`
- `dataclasses`, `queue`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jhossain1509/Microsoft-security.git
cd Microsoft-security
```

2. Install dependencies:
```bash
pip install customtkinter playwright
playwright install chromium
```

3. Run the application:
```bash
python GoldenIT-Microsoft-Entra.py
```

## Usage

### 1. Prepare Input Files

#### Accounts File (CSV or TXT)
Create a file containing your Microsoft Entra accounts. Supports both CSV and plain text formats.

**CSV Format:**
```csv
email,password,2fa_secret
user1@domain.com,password123,JBSWY3DPEHPK3PXP
user2@domain.com,password456,
```

**TXT Format (comma-separated):**
```
user1@domain.com,password123,JBSWY3DPEHPK3PXP
user2@domain.com,password456,
```

**Supported Column Names:**
- Email: `email`, `username`, or `upn`
- Password: `password` or `pass`
- 2FA Secret: `2fa_secret` or `secret` (optional, base32-encoded TOTP secret)

#### Emails File (TXT)
Create a text file with one email address per line:
```
alternate1@example.com
alternate2@example.com
alternate3@example.com
```

### 2. Configure Settings

- **Accounts File**: Browse and select your accounts CSV/TXT file
- **Emails File**: Browse and select your emails TXT file
- **Emails Per Account**: Set how many emails should be added to each account (default: 5)
- **Batch Browsers**: Set how many browser instances to run simultaneously (default: 3)

### 3. Start Processing

1. Click **Start** to begin the batch operation
2. Monitor progress in real-time through the log window
3. Use **Pause** to temporarily halt processing
4. Use **Resume** to continue after pausing
5. Use **Stop** to terminate all operations

### 4. Review Results

- View detailed logs in the application window
- Check the progress bar and summary statistics
- Export logs using the **Export Logs** button
- Retry failed emails using the **Retry Failed** button

## Output Files

The application generates several output files:

- `sent_done.txt` - List of successfully added email addresses
- `failed_emails.txt` - List of emails that failed to be added
- `logs_export.csv` - Detailed log export with columns: account, email, status, reason, timestamp

## Configuration

### Batch Size
The batch size determines how many browser instances run simultaneously. Consider your system resources:
- **Low-end systems**: 1-2 browsers
- **Mid-range systems**: 3-5 browsers
- **High-end systems**: 5-10 browsers

### Emails Per Account
Distributes emails evenly across accounts. For example:
- 100 emails ÷ 20 accounts = 5 emails per account

## Security Considerations

⚠️ **Important Security Notes:**

1. **Credential Storage**: This application requires storing account credentials. Ensure input files are:
   - Stored in a secure location
   - Protected with appropriate file permissions
   - Not committed to version control

2. **2FA Secrets**: TOTP secrets are sensitive. Handle with care:
   - Store securely
   - Never share or expose publicly
   - Use encrypted storage when possible

3. **Network Security**: The application connects to Microsoft services:
   - Ensure secure network connection
   - Be aware of corporate firewall/proxy settings
   - Monitor for suspicious activity

4. **Browser Automation**: Runs visible browser instances:
   - May trigger security alerts
   - Could be detected by advanced security systems
   - Use responsibly and in compliance with Microsoft's Terms of Service

## Troubleshooting

### Common Issues

**Browser Not Found**
```
Error: Executable doesn't exist at ...
```
Solution: Run `playwright install chromium`

**Login Failures**
- Verify credentials are correct
- Check if 2FA is properly configured
- Ensure accounts are not locked or require password reset

**Email Input Not Found**
- Microsoft may have updated their UI
- Check for application updates
- Contact support if issue persists

**Timeout Errors**
- Increase timeout values in the code if needed
- Check internet connection stability
- Verify Microsoft services are accessible

### Log Levels

- **INFO** (Blue): General information and progress updates
- **SUCCESS** (Green): Successful operations
- **WARN** (Yellow): Warnings and paused states
- **ERROR** (Red): Failures and critical issues

## Best Practices

1. **Test First**: Always test with a small batch before processing large numbers
2. **Monitor Progress**: Keep an eye on the logs for any issues
3. **Regular Backups**: Keep backups of your input files
4. **Staged Processing**: Process accounts in stages rather than all at once
5. **Network Stability**: Ensure stable internet connection before starting

## Limitations

- Requires non-headless browser mode for Microsoft security verification
- Subject to Microsoft's rate limiting and security policies
- May require manual intervention for unusual security prompts
- Performance depends on network speed and system resources

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style conventions
- Changes are tested thoroughly
- Security considerations are addressed

## License

This project is provided as-is for educational and automation purposes. Users are responsible for ensuring compliance with Microsoft's Terms of Service and applicable laws.

## Disclaimer

This tool is for legitimate automation purposes only. Users must:
- Have proper authorization to modify the accounts
- Comply with their organization's security policies
- Follow Microsoft's Terms of Service
- Use responsibly and ethically

The authors are not responsible for any misuse or violations of terms of service.

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.

## Version History

- **Initial Release**: Basic functionality for batch email method addition