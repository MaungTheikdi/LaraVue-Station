# Tools for Laravel + Vue development

This folder stores local stack configuration files used to run Laravel + Vue
apps on this machine. The files are meant to be modified for local development.

## Files and what to edit

- `tools/httpd.conf`
  - Apache listens on port 81.
  - `DocumentRoot` points to `D:/maung/www`.
  - PHP module and `PHPIniDir` point to the local PHP install.
  - phpMyAdmin is exposed at `/phpmyadmin`.
  - If you want Laravel served directly, update `DocumentRoot` to
    `D:/maung/www/<app>/public`.

- `tools/php.ini`
  - Development-friendly settings (`display_errors = On`, `error_reporting = E_ALL`).
  - MySQL extensions enabled: `mysqli` and `pdo_mysql`.
  - Limits to revisit for Laravel uploads: `post_max_size = 8M`,
    `upload_max_filesize = 2M`, `memory_limit = 128M`.

- `tools/my.ini`
  - MySQL base and data directory.
  - Port `3306` and `bind-address = 127.0.0.1` for local-only access.

- `tools/config.inc.php`
  - phpMyAdmin local auth config (user, password, host/port).
  - Temp directory set to `D:/maung/app/phpmyadmin/tmp`.

## Related installer

- `www/lara_vue_install.sh`
  - Creates a Laravel app, installs Vue 3 + Vue Router + Sanctum + Tailwind.
  - Copies custom starter files from `theikdimaung/` into the new app.
  - Generates a roles migration and lists manual `.env` and migrate steps.

## Notes

- Keep these files in sync with your actual binaries in `D:/maung/bin`.
- If you change ports here, update your Laravel `.env` and any scripts that
  assume default ports.
