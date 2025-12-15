# FreshRSS to Karakeep

A tool to transfer saved/favorited items from [FreshRSS](https://github.com/FreshRSS/FreshRSS) to [Karakeep](https://github.com/karakeep-app/karakeep).

## Overview

FreshRSS to Karakeep simplifies the curation workflow between self-hosted FreshRSS (RSS reader) and Karakeep (bookmarking/read-it-later app). The tool automatically transfers items you've marked as "favorites" (saved) in FreshRSS to your Karakeep instance, applying the "freshrss" tag for easy identification.

## Workflow

The intended workflow is simple:

1. Browse your RSS feeds in FreshRSS
2. Mark interesting items as "favourite" (which is called 'saved' in the Fever API)
3. Have a scheduled job (e.g., systemd timer) run this script daily
4. Find your saved items in Karakeep with the "freshrss" tag

## Dependencies

This tool relies on two custom API clients that I made:
- [karakeep_python_api](https://github.com/thiswillbeyourgithub/karakeep_python_api/)
- [freshrss_python_api](https://github.com/thiswillbeyourgithub/freshrss_python_api/)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/freshrss-to-karakeep.git
cd freshrss-to-karakeep

# Install dependencies
pip install -r requirements.txt
```

## Configuration

You need to set the following environment variables:

### FreshRSS Configuration
```bash
export FRESHRSS_PYTHON_API_HOST="https://your-freshrss-instance.com"
export FRESHRSS_PYTHON_API_USERNAME="your_username"
export FRESHRSS_PYTHON_API_PASSWORD="your_password"
```

### Karakeep Configuration
```bash
export KARAKEEP_PYTHON_API_ENDPOINT="https://your-karakeep-instance.com/api/v1"
export KARAKEEP_PYTHON_API_KEY="your_api_key"
export KARAKEEP_PYTHON_API_VERBOSE="true"  # Optional
export KARAKEEP_PYTHON_API_VERIFY_SSL="true"  # Optional, defaults to true
```

### Logging Configuration
The application always logs at DEBUG level to a log file, but console output verbosity can be controlled with the `--verbose` flag.

## Usage

```bash
# Basic usage
python freshrss_to_karakeep.py

# Only include items with URLs matching a pattern
python freshrss_to_karakeep.py --needed-regex "github\.com"

# Exclude items with URLs matching a pattern
python freshrss_to_karakeep.py --ignore-regex "youtube\.com"

# Dry run (don't actually transfer, just show what would be transferred)
python freshrss_to_karakeep.py --dry-run

# Keep items saved in FreshRSS after transfer
python freshrss_to_karakeep.py --no-unsave-freshrss

# Mark bookmarks as favourited in Karakeep
python freshrss_to_karakeep.py --mark-as-favourite

# Mark bookmarks as archived in Karakeep
python freshrss_to_karakeep.py --mark-as-archived

# Don't mark items as read in FreshRSS after unsaving
python freshrss_to_karakeep.py --no-mark-as-read
```

### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--needed-regex` | Only include items with URLs matching this regex | `.*` (all URLs) |
| `--ignore-regex` | Exclude items with URLs matching this regex | `""` (none) |
| `--dry-run` | Don't actually transfer items, just show what would be transferred | `False` |
| `--unsave-freshrss/--no-unsave-freshrss` | Whether to unsave items from FreshRSS after transfer | `True` |
| `--mark-as-read/--no-mark-as-read` | Whether to mark items as read in FreshRSS after transfer (only if unsaved) | `True` |
| `--mark-as-favourite/--no-mark-as-favourite` | Whether to mark bookmarks as favourited in Karakeep | `False` |
| `--mark-as-archived/--no-mark-as-archived` | Whether to mark bookmarks as archived in Karakeep | `False` |
| `--verbose` | Show detailed log messages in console output | `False` |

## Automation with systemd

To run this script daily, you can set up a systemd service and timer:

1. Create a service file at `/etc/systemd/system/freshrss-to-karakeep.service`:
```ini
[Unit]
Description=Transfer saved items from FreshRSS to Karakeep
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/freshrss_to_karakeep.py
Environment="FRESHRSS_PYTHON_API_HOST=https://your-freshrss-instance.com"
Environment="FRESHRSS_PYTHON_API_USERNAME=your_username"
Environment="FRESHRSS_PYTHON_API_PASSWORD=your_password" 
Environment="KARAKEEP_PYTHON_API_ENDPOINT=https://your-karakeep-instance.com/api/v1/"
Environment="KARAKEEP_PYTHON_API_KEY=your_api_key"
# No environment variable for logging needed anymore
WorkingDirectory=/path/to/directory

[Install]
WantedBy=multi-user.target
```

2. Create a timer file at `/etc/systemd/system/freshrss-to-karakeep.timer`:
```ini
[Unit]
Description=Run FreshRSS to Karakeep transfer daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start the timer:
```bash
sudo systemctl enable freshrss-to-karakeep.timer
sudo systemctl start freshrss-to-karakeep.timer
```


---
*This README was created with assistance from [aider.chat](https://github.com/Aider-AI/aider/)*
