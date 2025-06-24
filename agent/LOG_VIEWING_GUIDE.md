# NetPilot Agent Log Viewing Guide

## Overview

NetPilot Agent uses a dual-output logging system:
- **Files**: Clean text without ANSI codes (stored in `agent/logs/`)
- **Terminal**: Colored output when TTY is detected

This approach ensures log files remain clean and parseable while providing visual feedback during development.

## Log Files Structure

```
agent/logs/
├── main.log     # Application lifecycle, startup, shutdown
├── config.log   # Configuration loading, validation, updates  
├── tunnel.log   # Tunnel operations, monitoring, heartbeat
├── router.log   # Router communication, SSH, package installation
├── port.log     # Port allocation, cloud VM communication
├── status.log   # Status API server, health checks
├── error.log    # All errors from all modules (centralized)
└── debug.log    # Detailed debug information
```

## Viewing Colored Logs

### Method 1: Using `bat` (Recommended)

`bat` is a modern replacement for `cat` with syntax highlighting and Git integration.

#### Installation
```bash
# Ubuntu/Debian
sudo apt install bat

# macOS
brew install bat

# Windows
winget install sharkdp.bat
```

#### Usage
```bash
# View a single log file with syntax highlighting
bat --language log agent/logs/main.log

# View logs with line numbers
bat --language log --style numbers agent/logs/main.log

# Monitor logs in real-time (similar to tail -f)
tail -f agent/logs/main.log | bat --paging=never -l log

# View multiple log files
bat --language log agent/logs/*.log
```

#### Configuration
Add to your shell configuration (~/.bashrc, ~/.zshrc):
```bash
# Alias for viewing NetPilot logs
alias viewlogs='bat --language log --style numbers,changes'
alias taillogs='tail -f agent/logs/main.log | bat --paging=never -l log'
```

### Method 2: Using `ccze` (Log-Specific)

`ccze` is specifically designed for colorizing various log formats.

#### Installation
```bash
# Ubuntu/Debian
sudo apt install ccze

# CentOS/RHEL
sudo yum install ccze
```

#### Usage
```bash
# Colorize any log file
cat agent/logs/main.log | ccze

# Monitor logs in real-time with colors
tail -f agent/logs/main.log | ccze

# Auto-scroll with ccze
ccze < agent/logs/main.log
```

### Method 3: Using `less` with highlighting

For environments where `bat` or `ccze` aren't available:

```bash
# Basic colored viewing (if ANSI codes present)
less -R agent/logs/main.log

# Follow mode
less +F agent/logs/main.log
```

## Color Accessibility

The NetPilot Logger uses carefully selected colors for maximum readability:

### Colors Used ✅
- **Red**: Errors and critical messages
- **Green**: Success and info messages  
- **Cyan**: Debug information and main categories
- **Magenta**: Warnings and configuration
- **White**: Port management and neutral categories

### Colors Avoided ❌
- **Bright Yellow**: Poor contrast on light backgrounds
- **Blue**: Invisible on Windows cmd.exe
- **Grey**: Conflicts with Solarized Dark theme

## Log Analysis Tools

### Quick Commands
```bash
# Count error occurrences
grep -c "ERROR" agent/logs/error.log

# Find recent tunnel issues
grep "TUNNEL" agent/logs/tunnel.log | tail -20

# Monitor all errors in real-time
tail -f agent/logs/error.log | bat --paging=never -l log

# Search across all logs
grep -r "keyword" agent/logs/
```

### Integration with `fzf`
```bash
# Interactive log file browser with preview
find agent/logs -name "*.log" | fzf --preview "bat --color=always --language=log {}"
```

## Development Tips

1. **Use terminal output** for development (colored, real-time feedback)
2. **Use file output** for production monitoring (clean, parseable)
3. **Combine tools**: `tail -f` + `bat` for best real-time viewing
4. **Set up aliases** for frequently used log viewing commands

## Troubleshooting

### Colors not showing in terminal
- Ensure `TERM` environment variable supports colors
- Check if `COLORTERM` is set to `truecolor` or `24bit`

### `bat` not available
- Use `ccze` as alternative
- Or use `less -R` for basic ANSI support

### Performance with large files
- Use `tail` to view recent entries: `tail -1000 agent/logs/main.log | bat -l log`
- Use `head` for beginning: `head -1000 agent/logs/main.log | bat -l log`

## References

- [bat GitHub Repository](https://github.com/sharkdp/bat)
- [ccze Documentation](https://packages.debian.org/stable/ccze)
- [ANSI Color Guidelines](https://no-color.org/) 