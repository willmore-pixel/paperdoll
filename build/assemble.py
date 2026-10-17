# Inline swatch-kit.js and croquis-data.js into app.html -> index.html, the single-file app GitHub Pages serves
import os
b = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
s = open(b+'build/app.html').read()
s = s.replace('/*SWATCHKIT*/',open(b+'src/swatch-kit.js').read().replace('\r\n','\n').replace('</script>','<\\/script>')).replace('/*CROQUIS*/',open(b+'build/croquis-data.js').read())
head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#e8698a">
<link rel="icon" href="icons/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Paperdoll">
<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));</script>
'''
s = head + s  # manifest, icons and service worker make the GitHub Pages site installable as an app
open(b+'index.html','w').write(s);print(len(s))
