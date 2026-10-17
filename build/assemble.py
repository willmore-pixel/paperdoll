# Inline swatch-kit.js and croquis-data.js into app.html -> index.html, the single-file app GitHub Pages serves
import os
b = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
s = open(b+'build/app.html').read()
s = s.replace('/*SWATCHKIT*/',open(b+'src/swatch-kit.js').read().replace('\r\n','\n').replace('</script>','<\\/script>')).replace('/*CROQUIS*/',open(b+'build/croquis-data.js').read())
s = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + s
open(b+'index.html','w').write(s);print(len(s))
