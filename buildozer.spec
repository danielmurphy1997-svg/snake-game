[app]
title = Snake Game
package.name = snakegame
package.domain = com.danielmurphy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = .github, .git, __pycache__

version = 1.0

requirements = python3,pygame==2.1.2

p4a.bootstrap = sdl2

orientation = landscape
fullscreen = 1

android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653

[buildozer]
log_level = 2
warn_on_root = 0
