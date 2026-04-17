[app]
title = Snake Game
package.name = snakegame
package.domain = com.danielmurphy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
