# LaraVue-Station Dev Environment Controller

A small Tkinter desktop app that starts and stops a local Windows dev stack:
Apache, MySQL, PHP, and phpMyAdmin. The UI provides start/stop controls, live
status indicators, and a log window that captures process output.

## Features
- Start all services with one click.
- Stop all services gracefully (with forced kill fallback).
- Status indicators per service.
- Log window for stdout/stderr.

## Requirements
- Windows with Python 3.8+.
- Local binaries in the expected folder layout:
  - `bin/apache/bin/httpd.exe`
  - `bin/mysql-9.4.0-winx64/bin/mysqld.exe`
  - `bin/php/php.exe`
  - `app/phpmyadmin/` folder

If your paths differ, edit them in `theikdi_maung.py`.

## Default Bundled Versions and Download Pages
These are the default bundle names expected by the current folder layout. If you
upgrade, update the folder names or edit `theikdi_maung.py` paths accordingly.

- Apache HTTP Server: `httpd-2.4.65-250724-Win64-VS17`
  - https://www.apachelounge.com/download/
- MySQL: `mysql-9.4.0-winx64`
  - https://dev.mysql.com/downloads/mysql/
- PHP: `php-8.4.15-Win32-vs17-x64`
  - https://windows.php.net/download/
- phpMyAdmin: `phpMyAdmin-5.2.2-all-languages`
  - https://www.phpmyadmin.net/downloads/

## Usage
```powershell
python .\theikdi_maung.py
```

Click **START ALL** to launch services, and **STOP ALL** to shut them down.

phpMyAdmin is expected at:
```
http://localhost:81/phpmyadmin
```

## Project Layout
```
.
├─ theikdi_maung.py
├─ app/
│  └─ phpmyadmin/
├─ bin/
│  ├─ apache/
│  │  └─ bin/httpd.exe
│  ├─ mysql-9.4.0-winx64/
│  │  ├─ bin/mysqld.exe
│  │  └─ my.ini
│  └─ php/
│     └─ php.exe
└─ www/
```

## Notes
- Apache requires PHP configured in `httpd.conf` before it will start.
- MySQL uses `bin/mysql-9.4.0-winx64/my.ini` if present.
