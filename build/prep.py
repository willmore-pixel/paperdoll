# Turn the croquis + design SVGs into compact JS data: body lines, garment pieces (lines + silhouette), CSS.
import re, json, math
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
SRC = ROOT + 'src/'
DES = SRC + 'design/'
# piece id -> design file stem ('<stem>1.svg' Regular, '<stem>2.svg' Curvier), class prefix
DESIGNS = [('bodice', 'lisa bodice', 'b'), ('skirt', 'circle skirt', 's'), ('zelda', 'zelda skirt', 'z'), ('princess', 'princess dress', 'p')]
SHAPES = r'path|line|polygon|polyline|rect|circle|ellipse'

def body_of(fn):
    s = open(SRC + fn).read()
    css = re.search(r'<style>(.*?)</style>', s, re.S).group(1)
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    l1 = s[s.index('id="Layer_1"'):s.index('id="Layer_2"')]
    l1 = l1[l1.index('>') + 1:]
    l1 = l1[:l1.rindex('<g')]                       # drop the trailing "<g " that opens Layer_2
    guide = re.findall(r'\.(cls-\d+)\{stroke:#ef9921;\}', css)       # orange waist guide line
    for g in guide: l1 = re.sub(r'<(line|path|polygon)[^>]*class="%s"[^>]*/>' % g, '', l1)
    l1 = re.sub(r'</g>\s*$', '', l1.strip())
    l1 = re.sub(r'\s(id|data-name)="[^"]*"', '', l1)
    return css, vb, l1

def path_pts(d):
    """Every end and control point of a path, absolute (good enough for a bounding box)."""
    toks = re.findall(r'[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)
    pts, i, cmd, x, y, x0, y0 = [], 0, None, 0.0, 0.0, 0.0, 0.0
    n = {'M': 2, 'L': 2, 'T': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'A': 7, 'Z': 0}
    while i < len(toks):
        if toks[i].isalpha(): cmd = toks[i]; i += 1
        C, rel = cmd.upper(), cmd.islower()
        if C == 'Z': x, y = x0, y0; continue
        a = [float(v) for v in toks[i:i + n[C]]]; i += n[C]
        if C == 'H': x = a[0] + (x if rel else 0)
        elif C == 'V': y = a[0] + (y if rel else 0)
        elif C == 'A': x, y = a[5] + (x if rel else 0), a[6] + (y if rel else 0)
        else:
            for j in range(0, len(a), 2): pts.append((a[j] + (x if rel else 0), a[j + 1] + (y if rel else 0)))
            x, y = pts[-1]
        pts.append((x, y))
        if C == 'M': x0, y0 = x, y; cmd = 'l' if rel else 'L'
    return pts

def box_of(ds, pad=8):
    p = [q for d in ds for q in path_pts(d)]
    x0, y0 = min(a for a, b in p) - pad, min(b for a, b in p) - pad
    return [math.floor(x0), math.floor(y0), math.ceil(max(a for a, b in p) + pad - x0), math.ceil(max(b for a, b in p) + pad - y0)]

def design(fn, pre):
    s = open(DES + fn).read().replace('\r', '')
    css = re.sub(r'\s+', ' ', re.search(r'<style>(.*?)</style>', s, re.S).group(1))
    css = re.sub(r'\s*([{};:,])\s*', r'\1', css).strip()
    ren = {c: '%s-%s' % (pre, c) for c in set(re.findall(r'\.([A-Za-z][\w-]*)', css))}   # keep each design's classes apart in the shared stylesheet
    css = re.sub(r'\.([A-Za-z][\w-]*)', lambda m: '.' + ren[m.group(1)], css)
    rules = re.findall(r'([^{}]+)\{([^}]*)\}', css)
    def prop(cls, key):
        v = None
        for sel, body in rules:
            if re.search(r'\.%s(?![\w-])' % re.escape(cls), sel):
                m = re.search(r'(?:^|;)%s:([^;]+)' % key, body)
                if m: v = m.group(1)
        return v
    assert 'transform' not in s and '<image' not in s and 'clip-path' not in s, fn
    body = s[s.index('>', s.index('<svg')) + 1:]
    allp, walls, sil, stack = [], [], [], []
    for m in re.finditer(r'<(/?)(g|%s)\b([^>]*?)(/?)>' % SHAPES, body):
        close, tag, attrs, _ = m.groups()
        idm = re.search(r'\sid="([^"]+)"', attrs)
        if tag == 'g':      # stack holds "inside a detail group" for each open <g>, so nested groups count too
            if close: stack.pop()
            else: stack.append(bool(idm and idm.group(1).startswith('detail')) or (bool(stack) and stack[-1]))
            continue
        if close: continue
        cls = re.search(r'class="([^"]+)"', attrs)
        cls = cls and ren[cls.group(1)]
        if cls and prop(cls, 'fill') == '#dedede' and not prop(cls, 'stroke'): continue   # unstroked grey duplicates
        el = re.sub(r'\s(id|data-name)="[^"]*"', '', m.group(0))
        if cls: el = re.sub(r'class="[^"]+"', 'class="%s"' % cls, el)
        if idm and re.fullmatch(r'outline([-_]\d+)?', idm.group(1)):
            sil.append(re.search(r'\sd="([^"]+)"', attrs).group(1))
        allp.append(el)
        if not ((stack and stack[-1]) or (idm and idm.group(1).startswith('detail'))): walls.append(el)   # detail lines show but don't stop Fill
    assert sil, fn + ': no outline'
    return css, {'lines': ''.join(allp), 'walls': ''.join(walls), 'sil': sil, 'box': box_of(sil), 'parts': [box_of([d]) for d in sil]}

out = {}
for key, fn, n in [('regular', 'circle1.svg', '1'), ('curvier', 'lisa bodic2.svg', '2')]:
    css, vb, body = body_of(fn)
    out[key] = {'vb': vb, 'css': css, 'body': body, 'pieces': {}}
    for pid, stem, pre in DESIGNS:
        c, piece = design(stem + n + '.svg', pre)
        out[key]['css'] += c
        out[key]['pieces'][pid] = piece
open(ROOT + 'build/croquis-data.js', 'w').write('const CROQUIS=' + json.dumps(out, ensure_ascii=False) + ';\n')
print({k: {p: (q['box'], len(q['lines']), len(q['walls']), len(q['sil'])) for p, q in v['pieces'].items()} for k, v in out.items()})
