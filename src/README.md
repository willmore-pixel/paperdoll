# Swatch Kit 色卡工具包

把真實材料的照片變成可以無縫重複鋪的色卡，可以直接放進其他網頁專案（例如紙娃娃）。不需要安裝任何套件。

包含兩個功能：

1. **拍照／相簿裁切**：跟鞋子網站一樣有方框和公分刻度。拍照時只保留框內，相簿照片可以拖曳、雙指縮放後再按「使用」。框代表幾公分可以自己設定，不一定是 30 cm。
2. **無縫處理（方法 2+）**：先把照片的光線拉平（去掉陰影和一邊亮一邊暗），再把四邊融合成可以無縫重複的圖。

## 檔案

- `swatch-kit.js`：工具本身，放進專案就能用。
- `demo.html`：示範頁，和 `swatch-kit.js` 放在同一個資料夾，用手機打開就能試。左邊是原始照片直接重複，右邊是 2+ 處理過的，下面套在一件紙娃娃洋裝上。（相機需要 https 網址才能開，本機直接開檔案時請用 🖼 相簿。）

## 放進你的專案

1. 把 `swatch-kit.js` 複製到專案資料夾。
2. 在網頁裡加上：

```html
<script src="swatch-kit.js"></script>
```

3. 在按鈕被按下的時候叫它（一定要在點擊裡面呼叫，手機才會允許開相機或相簿）：

```js
button.onclick = async () => {
  const sw = await SwatchKit.capture({ source: "camera", sizeCm: 30 });
  if (!sw) return;          // 使用者按了取消
  // sw.url     → 處理好的色卡圖片（data URL，可以存起來）
  // sw.sizeCm  → 這張圖代表幾公分
};
```

### capture 的設定

| 設定 | 預設 | 說明 |
|---|---|---|
| `source` | `"camera"` | `"camera"` 開相機（開不了會改用手機內建相機），`"album"` 開相簿，或直接給一個檔案 |
| `sizeCm` | `30` | 方框代表幾公分 |
| `size` | `640` | 輸出圖片的邊長（像素） |
| `seamless` | `true` | 要不要做 2+ 無縫處理 |
| `text` | 中文 | 畫面上的文字，可以換成英文，例如 `{ use: "Use", cancel: "Cancel" }` |

## 把色卡貼到衣服上

色卡要照真實尺寸鋪，才會跟實際大小一樣。你需要知道畫面上「1 公分是幾個單位」。

**SVG 衣服**（建議）：

```js
// 例如衣服寬 200 單位、實際 50 cm → 每公分 4 單位
defs.innerHTML = SwatchKit.svgPattern("fabric", sw.url, sw.sizeCm, 4);
dressPath.setAttribute("fill", "url(#fabric)");
```

**一般 HTML 元素**：

```js
Object.assign(el.style, SwatchKit.cssBackground(sw.url, sw.sizeCm, pxPerCm));
```

**只要無縫處理**（例如已經有裁好的圖）：

```js
const canvas = SwatchKit.makeSeamless(imageOrCanvas, { size: 640 });
const url = canvas.toDataURL("image/jpeg", 0.85);
```

## 拍照小提醒

- 材料攤平、正上方拍，光線越平均越好，2+ 能處理輕微的陰影，但大片的影子還是會留下痕跡。
- 有大圖案的印花布，2+ 融合的地方會有一點重影。這種布最好拍剛好一個花紋循環，再關掉無縫處理（`seamless: false`），把 `sizeCm` 設成循環的實際尺寸。
- 手機量不到距離，方框只是參考，邊上可以放一把尺對齊。
