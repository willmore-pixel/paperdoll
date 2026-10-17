# Paperdoll Atelier

紙娃娃繪圖 App：選人台（Regular / Curvier）、套上款式（上衣、裙子、洋裝），用填色、代針筆、水彩、橡皮擦和花邊上色，也能拍照做成布料色卡。

線上版：https://willmore-pixel.github.io/paperdoll/

## 檔案

| 路徑 | 內容 |
|---|---|
| `index.html` | 建置好的單一檔案 App（GitHub Pages 直接提供這個檔案） |
| `build/app.html` | App 主程式（英文介面），改功能改這裡 |
| `build/app.zh.html` | 舊版中文介面 |
| `build/prep.py` | 把人台和款式 SVG 轉成 `build/croquis-data.js` |
| `build/assemble.py` | 把 `app.html`、`croquis-data.js`、`src/swatch-kit.js` 合成 `index.html` |
| `src/design/` | 款式 SVG：`<款式名>1.svg` 是 Regular，`<款式名>2.svg` 是 Curvier |
| `src/` | 人台 SVG、色卡工具 `swatch-kit.js`、花邊 `trims.svg`、版面參考 |
| `croquis/` | 空白人台 SVG |
| `新款式檔案規格.md` | 新款式 SVG 要怎麼畫 |
| `atelier.html` | 舊版款式畫板 |

## 重新建置

```sh
python3 build/prep.py
python3 build/assemble.py
```

然後把 `index.html` 一起 commit，推上 `main` 後 GitHub Pages 會自動更新。
