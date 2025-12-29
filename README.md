# Microsoft-security

## Screenshot Monitor (SMTP)

A desktop application that captures full desktop screenshots at configurable intervals and sends them via email using SMTP protocol. Each email includes the hostname and local IP address to identify the source PC/RDP session.

### Features
- ✨ Full desktop screenshot capture
- 📧 SMTP email delivery with screenshots
- ⏱️ Configurable capture intervals
- 🖥️ System identification (hostname + local IP)
- 💾 Configuration persistence
- 🔄 Background monitoring thread

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python screenshot_monitor.py
```

### Documentation
See [USAGE.md](USAGE.md) for detailed usage instructions and configuration guide.

### Requirements
- Python 3.7+
- Tkinter (usually comes with Python, see installation notes below)
- Pillow (for screenshot capture)

### Installation Notes

**Tkinter Installation:**
- **Windows**: Tkinter is included with Python by default
- **macOS**: Tkinter is included with Python by default
- **Linux (Debian/Ubuntu)**: 
  ```bash
  sudo apt-get install python3-tk
  ```
- **Linux (Fedora)**: 
  ```bash
  sudo dnf install python3-tkinter
  ```

**Pillow Installation:**
```bash
pip install -r requirements.txt
```

### GUI Features
The application provides a user-friendly interface with:
- **SMTP Configuration**: Host, Port, Username, Password
- **Email Settings**: Recipient email and capture interval
- **Status Monitor**: Real-time monitoring status and last capture time
- **Control Buttons**: Start/Stop monitoring and Save configuration