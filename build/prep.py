# Turn the croquis + design SVGs into compact JS data: body lines, garment pieces (lines + silhouette), CSS.
import re, json, math, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
SRC = ROOT + 'src/'
CRQ = [ROOT + 'croquis/', ROOT + 'croquis/uploaded-2026-10-18/']   # croquis1.svg Regular, croquis2.svg Curvier; first folder that has them wins
DES = ROOT + 'design/'   # canonical design folder
# piece id -> design file stem ('<stem>1.svg' Regular, '<stem>2.svg' Curvier), class prefix
DESIGNS = [('bodice', 'lisa bodice', 'b'), ('skirt', 'circle skirt', 's'), ('zelda', 'zelda skirt', 'z'), ('princess', 'princess dress', 'p'),
           ('etoile', 'etoile bodice', 'e'), ('youthquake', 'youthquake skirt', 'y'),
           ('yves', 'yves trouser', 'v')]
SHAPES = r'path|line|polygon|polyline|rect|circle|ellipse'

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

def find_design(fn):
    """'<stem>1.svg' also matches 'Stem_1.svg', 'stem-1.svg', 'Stem 1.svg' (case, spaces, _ and - ignored)."""
    import os
    key = lambda f: re.sub(r'[\s_-]+', '', f.lower())
    hits = [f for f in os.listdir(DES) if key(f) == key(fn)]
    assert len(hits) == 1, (fn, hits)
    return DES + hits[0]

def parse(path, pre):
    """Lines of one SVG: all shapes in order, the ones Fill stops at (not detail*), and closed shapes by id."""
    s = open(path).read().replace('\r', '')
    s = re.sub(r'<metadata>.*?</metadata>', '', s, flags=re.S)
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
    assert 'transform' not in s and '<image' not in s and 'clip-path' not in s, path
    body = s[s.index('>', s.index('<svg')) + 1:]
    allp, walls, named, stack = [], [], [], []
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
        if idm and tag == 'path' and not idm.group(1).startswith('detail'):
            named.append((re.sub(r'[-_]\d+$', '', idm.group(1)), re.search(r'\sd="([^"]+)"', attrs).group(1)))   # 'skin-2' -> ('skin', d)
        allp.append(el)
        if not ((stack and stack[-1]) or (idm and idm.group(1).startswith('detail'))): walls.append(el)   # detail lines show but don't stop Fill
    return css, allp, walls, named

def design(fn, pre):
    css, allp, walls, named = parse(find_design(fn), pre)
    sil = [d for k, d in named if k == 'outline']
    assert sil, fn + ': no outline'
    return css, {'lines': ''.join(allp), 'walls': ''.join(walls), 'sil': sil, 'box': box_of(sil), 'parts': [box_of([d]) for d in sil]}

out = {}
import os
for key, n in [('regular', '1'), ('curvier', '2')]:
    fn = next(d + 'croquis%s.svg' % n for d in CRQ if os.path.exists(d + 'croquis%s.svg' % n))
    css, allp, walls, named = parse(fn, 'k')
    skin = [d for k, d in named if k == 'skin']
    assert skin, fn + ': no skin'
    out[key] = {'css': css, 'body': ''.join(allp), 'walls': ''.join(walls), 'skin': skin,
                'cover': [d for k, d in named if k not in ('skin', 'hair')], 'pieces': {}}   # shoes, bra... sit over the skin
    for pid, stem, pre in DESIGNS:
        c, piece = design(stem + n + '.svg', pre)
        out[key]['css'] += c
        out[key]['pieces'][pid] = piece
open(ROOT + 'build/croquis-data.js', 'w').write('const CROQUIS=' + json.dumps(out, ensure_ascii=False) + ';\n')
print({k: (len(v['skin']), len(v['cover']), len(v['body']), len(v['walls'])) for k, v in out.items()})
print({k: {p: (q['box'], len(q['lines']), len(q['walls']), len(q['sil'])) for p, q in v['pieces'].items()} for k, v in out.items()})
