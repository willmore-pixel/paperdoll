/* swatch-kit.js — turn a photo of real material into a seamless swatch.
 *
 * No dependencies. Include with <script src="swatch-kit.js"></script>; it adds window.SwatchKit.
 *
 *   const sw = await SwatchKit.capture({ source: "camera", sizeCm: 30 });   // or source: "album" / a File
 *   if (sw) img.src = sw.url;   // sw = { url, canvas, sizeCm, seamless }
 *
 *   SwatchKit.makeSeamless(canvasOrImage, { size: 640 })  -> canvas  (method 2+: even out light, then edge-blend)
 *   SwatchKit.svgPattern(id, url, sizeCm, unitsPerCm)     -> "<pattern …>" string for an SVG <defs>
 *   SwatchKit.cssBackground(url, sizeCm, pxPerCm)         -> { backgroundImage, backgroundSize } for an element
 *
 * The camera / crop screen shows a square frame with a cm ruler on its edges. A phone can't measure distance,
 * so the frame is a guide: whatever the user fits in it is treated as sizeCm × sizeCm.
 */
(function () {
  "use strict";

  const DEFAULTS = {
    source: "camera",     // "camera" (live camera, falls back to the phone's own camera), "album", or a File/Blob
    sizeCm: 30,           // real size the frame stands for
    size: 640,            // output pixels per side
    seamless: true,       // run makeSeamless on the result
    quality: 0.85,        // JPEG quality of sw.url
    text: {
      camHint: "把 {cm} × {cm} cm 的材料放滿框內",
      camSmall: "框邊的刻度是公分，可以在旁邊放一把尺對齊",
      cropHint: "拖曳、雙指縮放照片，讓 {cm} × {cm} cm 放滿框內",
      cropSmall: "框邊的刻度是公分",
      cancel: "取消", use: "使用", shot: "拍照", native: "系統相機",
    },
  };

  // ---------- Method 2+: even out the light, then blend the edges into a wrap-around tile ----------

  function makeSeamless(src, opts = {}) {
    const N = opts.size || 640;
    const band = opts.band ?? 0.22;      // share of the side used for blending at each edge
    const flatten = opts.flatten ?? true;
    const c = canvas(N, N), x = c.getContext("2d");
    x.drawImage(src, 0, 0, N, N);
    const a = x.getImageData(0, 0, N, N).data;

    // The light falloff: a very soft copy, made by shrinking to ~10 px and scaling back up smoothly.
    let low = null;
    if (flatten) {
      const k = 10, t = canvas(k, k), tx = t.getContext("2d");
      tx.imageSmoothingQuality = "high"; tx.drawImage(c, 0, 0, k, k);
      const b = canvas(N, N), bx = b.getContext("2d");
      bx.imageSmoothingEnabled = true; bx.imageSmoothingQuality = "high"; bx.drawImage(t, 0, 0, N, N);
      low = bx.getImageData(0, 0, N, N).data;
    }
    const mean = [0, 0, 0];
    for (let i = 0; i < a.length; i += 4) { mean[0] += a[i]; mean[1] += a[i + 1]; mean[2] += a[i + 2]; }
    for (let ch = 0; ch < 3; ch++) mean[ch] /= N * N;
    const f = new Float32Array(N * N * 3);
    for (let p = 0, i = 0; p < N * N; p++, i += 4)
      for (let ch = 0; ch < 3; ch++)
        f[p * 3 + ch] = low ? a[i + ch] / Math.max(low[i + ch], 1) * mean[ch] : a[i + ch];

    // Blend with a copy shifted by half a tile: near the edges the shifted copy (which wraps cleanly) takes over.
    const out = x.createImageData(N, N), o = out.data, h = N >> 1, bw = N * band;
    for (let y = 0; y < N; y++) for (let xx = 0; xx < N; xx++) {
      const d = Math.min(xx, y, N - 1 - xx, N - 1 - y);
      let w = Math.min(d / bw, 1); w = w * w * (3 - 2 * w);
      const p = y * N + xx, q = ((y + h) % N) * N + (xx + h) % N;
      for (let ch = 0; ch < 3; ch++) o[p * 4 + ch] = w * f[p * 3 + ch] + (1 - w) * f[q * 3 + ch];
      o[p * 4 + 3] = 255;
    }
    x.putImageData(out, 0, 0);
    return c;
  }

  // ---------- Using a swatch ----------

  const svgPattern = (id, url, sizeCm, unitsPerCm, x = 0, y = 0) => {
    const s = sizeCm * unitsPerCm;
    return `<pattern id="${id}" patternUnits="userSpaceOnUse" x="${x}" y="${y}" width="${s}" height="${s}"><image href="${url}" width="${s}" height="${s}" preserveAspectRatio="none"/></pattern>`;
  };
  const cssBackground = (url, sizeCm, pxPerCm) => ({ backgroundImage: `url("${url}")`, backgroundSize: `${sizeCm * pxPerCm}px ${sizeCm * pxPerCm}px`, backgroundRepeat: "repeat" });

  // ---------- Camera and crop screen ----------

  const CSS = `
.skit{position:fixed;inset:0;z-index:2147483000;background:#000;touch-action:none;user-select:none;-webkit-user-select:none;font-family:system-ui,sans-serif}
.skit img{position:absolute;left:0;top:0;max-width:none;transform-origin:0 0}
.skit video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.skit .crop-only,.skit.crop .cam-only{display:none}.skit.crop .crop-only{display:block}
.skit-frame{position:absolute;left:50%;top:44%;width:min(84vw,58vh);aspect-ratio:1;transform:translate(-50%,-50%);box-shadow:0 0 0 100vmax rgba(0,0,0,.5);border:2px solid #fff}
.skit-frame svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.skit-hint{position:absolute;left:16px;right:16px;top:calc(14px + env(safe-area-inset-top,0px));margin:0;text-align:center;color:#fff;font-size:15px;font-weight:800;line-height:1.45;text-shadow:0 1px 3px #000}
.skit-hint small{display:block;font-size:12px;font-weight:700;opacity:.85}
.skit-bar{position:absolute;left:0;right:0;bottom:0;padding:18px 24px calc(22px + env(safe-area-inset-bottom,0px));display:grid;grid-template-columns:1fr auto 1fr;align-items:center;color:#fff;font-weight:800;font-size:14px}
.skit-bar button,.skit-bar label{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
.skit-bar>:first-child{justify-self:start}.skit-bar label{justify-self:end;position:relative}
.skit-bar input{position:absolute;inset:0;opacity:0;width:100%}
.skit .skit-shutter{width:70px;height:70px;border-radius:50%;background:#fff;border:5px solid rgba(255,255,255,.4);background-clip:padding-box}
.skit .skit-shutter:active{transform:scale(.94)}
.skit .skit-use{justify-self:center;padding:12px 26px;border-radius:99px;background:#fff;color:#111;font-weight:900;font-size:16px}`;

  function ruler(cm) {
    // Ticks every cm (long every 5), numbers every 5 cm (or every 10 for big frames).
    const u = 300 / cm, step = cm > 40 ? 10 : 5;
    let ticks = "";
    for (let i = 0; i <= cm; i++) {
      const v = i * u, len = i % 5 ? 7 : 14;
      ticks += `<line x1="${v}" y1="0" x2="${v}" y2="${len}"/><line x1="0" y1="${v}" x2="${len}" y2="${v}"/><line x1="${v}" y1="300" x2="${v}" y2="${300 - len}"/><line x1="300" y1="${v}" x2="${300 - len}" y2="${v}"/>`;
    }
    if (cm > 60) ticks = "";  // too dense to read
    let nums = "";
    for (let i = 0; i <= cm; i += step) nums += `<text x="${i * u}" y="28">${i}</text>`;
    return `<g stroke="#000" stroke-opacity=".5" stroke-width="3">${ticks}</g><g stroke="#fff" stroke-width="1.4">${ticks}</g>` +
      `<g fill="#fff" font-size="11" font-weight="800" text-anchor="middle" stroke="#000" stroke-opacity=".55" stroke-width="2.5" style="paint-order:stroke">${nums}<text x="150" y="46">cm</text></g>`;
  }

  function capture(options = {}) {
    const o = { ...DEFAULTS, ...options, text: { ...DEFAULTS.text, ...(options.text || {}) } };
    const T = k => o.text[k].replaceAll("{cm}", o.sizeCm);
    if (!document.getElementById("skit-css")) {
      const st = document.createElement("style"); st.id = "skit-css"; st.textContent = CSS; document.head.appendChild(st);
    }
    return new Promise(resolve => {
      const root = document.createElement("div");
      root.className = "skit"; root.hidden = true;
      root.innerHTML = `<video class="cam-only" playsinline muted autoplay></video><img class="crop-only" alt="" draggable="false">
<div class="skit-frame"><svg viewBox="0 0 300 300" aria-hidden="true">${ruler(o.sizeCm)}</svg></div>
<p class="skit-hint cam-only">${T("camHint")}<small>${T("camSmall")}</small></p>
<p class="skit-hint crop-only">${T("cropHint")}<small>${T("cropSmall")}</small></p>
<div class="skit-bar"><button type="button" data-k="cancel">${T("cancel")}</button>
<button type="button" class="skit-shutter cam-only" data-k="shot" aria-label="${T("shot")}"></button>
<button type="button" class="skit-use crop-only" data-k="use">${T("use")}</button>
<label class="cam-only">${T("native")}<input type="file" accept="image/*" capture="environment"></label><span class="crop-only"></span></div>`;
      document.body.appendChild(root);
      const $ = s => root.querySelector(s), video = $("video"), img = $("img"), frame = $(".skit-frame");
      let stream = null, crop = null, done = false;
      const pointers = new Map();

      function finish(result) {
        if (done) return; done = true;
        if (stream) stream.getTracks().forEach(t => t.stop());
        if (crop) URL.revokeObjectURL(crop.url);
        root.remove(); resolve(result);
      }
      function take(src, sx, sy, side) {
        let c = canvas(o.size, o.size);
        c.getContext("2d").drawImage(src, sx, sy, side, side, 0, 0, o.size, o.size);
        if (o.seamless) c = makeSeamless(c, { size: o.size });
        finish({ url: c.toDataURL("image/jpeg", o.quality), canvas: c, sizeCm: o.sizeCm, seamless: !!o.seamless });
      }
      function pickFile(input) {
        input.onchange = () => { const f = input.files[0]; input.value = ""; f ? openCrop(f) : finish(null); };
        input.oncancel = () => finish(null);
        input.click();
      }

      async function openCam() {
        const native = $("input[capture]");
        native.onchange = () => { const f = native.files[0]; native.value = ""; if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; f ? openCrop(f) : finish(null); };
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1920 } }, audio: false });
        } catch {
          // No live camera here: the phone's own camera, then the crop screen. (Some browsers need a tap first.)
          const f = document.createElement("input"); f.type = "file"; f.accept = "image/*"; f.capture = "environment";
          return pickFile(f);
        }
        video.srcObject = stream; root.classList.remove("crop"); root.hidden = false;
      }
      function openCrop(file) {
        const url = URL.createObjectURL(file);
        img.onload = () => {
          root.classList.add("crop"); root.hidden = false;
          const f = frame.getBoundingClientRect();
          const s = Math.max(f.width / img.naturalWidth, f.height / img.naturalHeight);
          crop = { url, min: s, s, x: f.left + (f.width - img.naturalWidth * s) / 2, y: f.top + (f.height - img.naturalHeight * s) / 2 };
          draw();
        };
        img.onerror = () => finish(null);
        img.src = url;
      }
      function draw() {
        const f = frame.getBoundingClientRect(), w = img.naturalWidth * crop.s, h = img.naturalHeight * crop.s;
        crop.x = Math.min(f.left, Math.max(f.right - w, crop.x));
        crop.y = Math.min(f.top, Math.max(f.bottom - h, crop.y));
        img.style.transform = `translate(${crop.x}px,${crop.y}px) scale(${crop.s})`;
      }
      function zoom(k, cx, cy) {
        const s = Math.min(Math.max(crop.s * k, crop.min), crop.min * 12);
        crop.x = cx - (cx - crop.x) * s / crop.s; crop.y = cy - (cy - crop.y) * s / crop.s; crop.s = s; draw();
      }

      root.addEventListener("pointerdown", e => { if (crop && !e.target.closest("button,label")) { pointers.set(e.pointerId, { x: e.clientX, y: e.clientY }); root.setPointerCapture(e.pointerId); } });
      root.addEventListener("pointermove", e => {
        const prev = pointers.get(e.pointerId);
        if (!crop || !prev) return;
        const pts = [...pointers.values()];
        if (pts.length === 1) { crop.x += e.clientX - prev.x; crop.y += e.clientY - prev.y; draw(); }
        else {
          const other = pts.find(p => p !== prev), d0 = Math.hypot(prev.x - other.x, prev.y - other.y), d1 = Math.hypot(e.clientX - other.x, e.clientY - other.y);
          const m0 = [(prev.x + other.x) / 2, (prev.y + other.y) / 2], m1 = [(e.clientX + other.x) / 2, (e.clientY + other.y) / 2];
          crop.x += m1[0] - m0[0]; crop.y += m1[1] - m0[1];
          d0 > 0 ? zoom(d1 / d0, m1[0], m1[1]) : draw();
        }
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      });
      ["pointerup", "pointercancel"].forEach(t => root.addEventListener(t, e => pointers.delete(e.pointerId)));
      root.addEventListener("wheel", e => { if (crop) { e.preventDefault(); zoom(Math.exp(-e.deltaY / 300), e.clientX, e.clientY); } }, { passive: false });

      $('[data-k="cancel"]').onclick = () => finish(null);
      $('[data-k="use"]').onclick = () => {
        if (!crop) return;
        const f = frame.getBoundingClientRect(), side = Math.min(f.width / crop.s, img.naturalWidth, img.naturalHeight);
        take(img, Math.max(0, (f.left - crop.x) / crop.s), Math.max(0, (f.top - crop.y) / crop.s), side);
      };
      $('[data-k="shot"]').onclick = () => {
        const vw = video.videoWidth, vh = video.videoHeight;
        if (!vw) return;
        // Map the on-screen square back to video pixels (the video fills the screen like object-fit: cover).
        const box = video.getBoundingClientRect(), f = frame.getBoundingClientRect();
        const s = Math.max(box.width / vw, box.height / vh), ox = (box.width - vw * s) / 2, oy = (box.height - vh * s) / 2;
        const side = Math.min(f.width / s, vw, vh);
        take(video, Math.min(Math.max((f.left - box.left - ox) / s, 0), vw - side), Math.min(Math.max((f.top - box.top - oy) / s, 0), vh - side), side);
      };

      if (o.source instanceof Blob) openCrop(o.source);
      else if (o.source === "album") { const f = document.createElement("input"); f.type = "file"; f.accept = "image/*"; pickFile(f); }
      else if (navigator.mediaDevices?.getUserMedia) openCam();
      else { const f = document.createElement("input"); f.type = "file"; f.accept = "image/*"; f.capture = "environment"; pickFile(f); }
    });
  }

  function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }

  window.SwatchKit = { capture, makeSeamless, svgPattern, cssBackground, defaults: DEFAULTS };
})();
