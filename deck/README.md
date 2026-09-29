# Pitch deck

- `PunarGati.pptx`: 12-slide, 16:9 deck (native, editable PowerPoint text, shapes, table and chart)
- `PunarGati.pdf`: the same deck exported for upload

Regenerate after editing `build_deck.js` (requires Node and `npm i -g pptxgenjs`):

```bash
NODE_PATH=$(npm root -g) node deck/build_deck.js
soffice --headless --convert-to pdf --outdir deck deck/PunarGati.pptx   # optional PDF
```

`assets/` holds the screenshots the deck uses (cropped from `docs/img`). If you retake the app screenshots on the Snapdragon laptop, where the badge shows *Hexagon NPU*, replace `assets/coach_crop.png` and rebuild.
