<?php
// app/phpmyadmin/config.inc.php

// Restart the stack (Stop All → Start All).
// If root doesn’t have a password yet, run:
// D:\maung\bin\mysql-9.4.0-winx64\bin\mysqladmin.exe -u root password "password"
// If root already has a password, use:

// D:\maung\bin\mysql-9.4.0-winx64\bin\mysqladmin.exe -u root -p password "password"
// Reload http://localhost:81/phpmyadmin.


// Basic phpMyAdmin configuration for local development.
$cfg['blowfish_secret'] = 'local-dev-only-blowfish-secret-32';

$i = 0;
$i++;
$cfg['Servers'][$i]['auth_type'] = 'config';
$cfg['Servers'][$i]['host'] = '127.0.0.1';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['user'] = 'root';
$cfg['Servers'][$i]['password'] = 'password';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = false;

$cfg['TempDir'] = 'D:/maung/app/phpmyadmin/tmp';
