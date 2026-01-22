#!/bin/bash

# =======================================================
# HEADER & BRANDING
# =======================================================
clear
echo -e "\e[93m" # Change text color to light yellow/gold
echo " Min-ga-lar-bar!"
echo ""
echo " #######################################################"
echo " #                                                     #"
echo " #             M I N G A L A R   C O D E               #"
echo " #                                                     #"
echo " #######################################################"
echo ""
echo " [ Laravel 12 Comp. + Vue 3 + Sanctum + Tailwind + Roles ]"
echo -e "\e[0m" # Reset color

# =======================================================
# 1. SETUP VARIABLES
# =======================================================
# [cite_start]Get the current directory where the script is located [cite: 6]
SOURCE_DIR="$(pwd)/theikdimaung"

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "\e[91m[ERROR] The source folder \"$SOURCE_DIR\" was not found!\e[0m"
    echo "Please create the folder and put your Vue/PHP files there."
    exit 1
fi

read -p "Enter Application Name (e.g., my-app): " appname

# =======================================================
# 2. LARAVEL INSTALLATION
# =======================================================
echo ""
[cite_start]echo "[1/7] Installing Laravel Framework..." [cite: 7]
echo "-------------------------------------------------------"
composer create-project laravel/laravel "$appname"
cd "$appname" || exit

# =======================================================
# 3. PACKAGES INSTALLATION
# =======================================================
echo ""
[cite_start]echo "[2/7] Installing Vue, Router, Sanctum & Tailwind..." [cite: 8]
echo "-------------------------------------------------------"
php artisan install:api
composer require laravel/sanctum
npm install vue@next vue-router@4 @vitejs/plugin-vue axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# =======================================================
# 4. DIRECTORY SCAFFOLDING
# =======================================================
echo ""
[cite_start]echo "[3/7] Creating Directory Structure..." [cite: 9]
echo "-------------------------------------------------------"
[cite_start]mkdir -p resources/js/components resources/js/router resources/js/layouts [cite: 9]

# =======================================================
# 5. COPYING CUSTOM FILES
# =======================================================
echo ""
[cite_start]echo "[4/7] Copying \"Mingalar Code\" Custom Files..." [cite: 10]
echo "      From: $SOURCE_DIR"
echo "-------------------------------------------------------"

# -- Backend Files --
[cite_start]cp "$SOURCE_DIR/AuthController.php" "app/Http/Controllers/" [cite: 10]
[cite_start]cp "$SOURCE_DIR/api.php" "routes/" [cite: 10]

# -- Frontend Configuration --
[cite_start]cp "$SOURCE_DIR/app.js" "resources/js/" [cite: 10]
[cite_start]cp "$SOURCE_DIR/vite.config.js" "./" [cite: 10]
[cite_start]cp "$SOURCE_DIR/tailwind.config.js" "./" [cite: 10]
[cite_start]cp "$SOURCE_DIR/app.css" "resources/css/" [cite: 10]
[cite_start]cp "$SOURCE_DIR/welcome.blade.php" "resources/views/" [cite: 10]

# -- Vue Components --
[cite_start]cp "$SOURCE_DIR/Login.vue" "resources/js/components/" [cite: 10]
[cite_start]cp "$SOURCE_DIR/Register.vue" "resources/js/components/" [cite: 10]
[cite_start]cp "$SOURCE_DIR/Dashboard.vue" "resources/js/components/" [cite: 10]
cp "$SOURCE_DIR/HomePage.vue" "resources/js/components/"
cp "$SOURCE_DIR/About.vue" "resources/js/components/"
cp "$SOURCE_DIR/Contact.vue" "resources/js/components/"
[cite_start]cp "$SOURCE_DIR/App.vue" "resources/js/components/" [cite: 10]
cp "$SOURCE_DIR/router.js" "resources/js/router/"

# =======================================================
# 6. DATABASE & MIGRATIONS
# =======================================================
echo ""
[cite_start]echo "[5/7] Setting up User Roles Migration..." [cite: 11]
echo "-------------------------------------------------------"
[cite_start]php artisan make:migration add_role_to_users_table --table=users [cite: 11]

echo ""
[cite_start]echo -e "\e[96m[INFO] Please manually update the new migration file to include:\e[0m" [cite: 12]
[cite_start]echo "       \$table->tinyInteger('role')->default(0);" [cite: 12]

# =======================================================
# 7. FINALIZATION
# =======================================================
echo ""
[cite_start]echo "[6/7] Finalizing Setup..." [cite: 13]
echo "-------------------------------------------------------"
[cite_start]npm run build [cite: 13]

echo ""
echo -e "\e[92m#######################################################"
[cite_start]echo "#           INSTALLATION COMPLETE!                    #" [cite: 14]
echo "#                                                     #"
[cite_start]echo "#   Mingalar Code Setup by Theikdi Maung is ready.    #" [cite: 15]
echo "#######################################################\e[0m"
echo ""
echo "" APP_URL=http://127.0.0.1:8000
echo "" e.g Create database on mysql name with laravel
echo "" DB_CONNECTION=mysql
echo "" DB_HOST=127.0.0.1
echo "" DB_PORT=3307
echo "" DB_DATABASE=laravel
echo "" DB_USERNAME=root
echo "" DB_PASSWORD=
echo "" 
echo "" php artisan key:generate
echo "" php artisan migrate


[cite_start]echo "1. Update your .env file with Database credentials." [cite: 16]
[cite_start]echo "2. Run 'php artisan migrate'" [cite: 17]
[cite_start]echo "3. Run 'npm run dev'" [cite: 17]
[cite_start]echo "4. Run 'php artisan serve'" [cite: 17]
echo ""
read -p "Press enter to exit..."