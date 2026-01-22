<?php
// /d:/maung/www/index.php
http_response_code(200);
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Maung Local Environment</title>
    <style>
        body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;display:flex;min-height:100vh;align-items:center;justify-content:center;background:#f7fafc;margin:0}
        .card{background:#fff;padding:28px 36px;border-radius:10px;box-shadow:0 6px 20px rgba(2,6,23,.08);text-align:center;max-width:680px}
        h1{margin:0 0 8px;font-size:20px}
        p{margin:6px 0;color:#556070}
        a.button{display:inline-block;margin-top:12px;padding:10px 14px;background:#2563eb;color:#fff;border-radius:8px;text-decoration:none}
        code{background:#f1f5f9;padding:3px 6px;border-radius:6px;font-size:90%}
    </style>
</head>
<body>
    <div class="card">
        <h1>Welcome to Maung Local Environment for Laravel + Vue</h1>
        <p>Laravel app entry: <a href="public" class="button">public/</a></p>
        <p>Common commands: <code>composer install</code> · <code>npm install</code> · <code>php artisan serve</code></p>
    </div>

    <script>
        // Lightweight hint: if you want a quick Vue mount for testing
        (function(){
            if (typeof Vue !== 'undefined') return;
            var s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/vue@2/dist/vue.min.js';
            s.async = true;
            document.head.appendChild(s);
        })();
    </script>
</body>
</html>