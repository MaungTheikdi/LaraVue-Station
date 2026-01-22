@echo off
color 0B
cls

:: =======================================================
:: HEADER & BRANDING
:: =======================================================
echo.
echo  Min-ga-lar-bar!
echo.
echo  #######################################################
echo  #                                                     #
echo  #             M I N G A L A R   C O D E             #
echo  #                                                     #
echo  #            Powered by: Theikdi Maung              #
echo  #                                                     #
echo  #######################################################
echo.
echo  [ Laravel 12 Comp. + Vue 3 + Sanctum + Tailwind + Roles ]
echo.

:: =======================================================
:: 1. SETUP VARIABLES
:: =======================================================
:: Sets the source directory to the folder 'theikdimaung' in the same dir as this script
set "SOURCE_DIR=%~dp0theikdimaung"

if not exist "%SOURCE_DIR%" (
    color 0C
    echo [ERROR] The source folder "%SOURCE_DIR%" was not found!
    echo Please create the folder and put your Vue/PHP files there.
    pause
    exit
)

set /p appname="Enter Application Name (e.g., my-app): "

:: =======================================================
:: 2. LARAVEL INSTALLATION
:: =======================================================
echo.
echo [1/7] Installing Laravel Framework...
echo -------------------------------------------------------
call composer create-project laravel/laravel %appname%
cd %appname%

:: =======================================================
:: 3. PACKAGES INSTALLATION
:: =======================================================
echo.
echo [2/7] Installing Vue, Router, Sanctum & Tailwind...
echo -------------------------------------------------------
call php artisan install:api
call composer require laravel/sanctum
call npm install vue@next vue-router@4 @vitejs/plugin-vue axios
call npm install -D tailwindcss postcss autoprefixer
call npx tailwindcss init -p

:: =======================================================
:: 4. DIRECTORY SCAFFOLDING
:: =======================================================
echo.
echo [3/7] Creating Directory Structure...
echo -------------------------------------------------------
if not exist "resources\js\components" mkdir resources\js\components
if not exist "resources\js\router" mkdir resources\js\router
if not exist "resources\js\layouts" mkdir resources\js\layouts

:: =======================================================
:: 5. COPYING CUSTOM FILES (Theikdi Maung Logic)
:: =======================================================
echo.
echo [4/7] Copying "Mingalar Code" Custom Files...
echo       From: %SOURCE_DIR%
echo -------------------------------------------------------

:: -- Backend Files --
copy "%SOURCE_DIR%\AuthController.php" "app\Http\Controllers\" /Y
copy "%SOURCE_DIR%\api.php" "routes\" /Y

:: -- Frontend Configuration --
copy "%SOURCE_DIR%\app.js" "resources\js\" /Y
copy "%SOURCE_DIR%\vite.config.js" ".\" /Y
copy "%SOURCE_DIR%\tailwind.config.js" ".\" /Y
copy "%SOURCE_DIR%\app.css" "resources\css\" /Y
copy "%SOURCE_DIR%\welcome.blade.php" "resources\views\" /Y

:: -- Vue Components --
:: Assumes your source folder has these specific files
copy "%SOURCE_DIR%\Login.vue" "resources\js\components\" /Y
copy "%SOURCE_DIR%\Register.vue" "resources\js\components\" /Y
copy "%SOURCE_DIR%\Dashboard.vue" "resources\js\components\" /Y
copy "%SOURCE_DIR%\App.vue" "resources\js\components\" /Y
copy "%SOURCE_DIR%\index.js" "resources\js\router\" /Y

:: =======================================================
:: 6. DATABASE & MIGRATIONS
:: =======================================================
echo.
echo [5/7] Setting up User Roles Migration...
echo -------------------------------------------------------
:: This creates the migration file
call php artisan make:migration add_role_to_users_table --table=users

:: We define the migration content dynamically using a simple PHP script to inject the code
:: (Or you can copy a ready-made migration file from your source folder if you have one)
echo.
echo [INFO] Please manually update the new migration file to include:
echo        $table->tinyInteger('role')->default(0);
echo.

:: =======================================================
:: 7. FINALIZATION
:: =======================================================
echo.
echo [6/7] Finalizing Setup...
echo -------------------------------------------------------
:: Run a build to ensure mix/vite is ready
call npm run build

echo.
echo #######################################################
echo #           INSTALLATION COMPLETE!                    #
echo #                                                     #
echo #   Mingalar Code Setup by Theikdi Maung is ready.    #
echo #######################################################
echo.
echo 1. Update your .env file with Database credentials.
echo 2. Run 'php artisan migrate'
echo 3. Run 'npm run dev'
echo 4. Run 'php artisan serve'
echo.
pause