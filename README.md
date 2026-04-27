# KeyComics

A lightweight browser-based viewer for comic book collection data exported from [Key Collector Comics](https://www.keycollectorcomics.com/).

## What it does

Load a JSON file of your comic series and browse your collection with a clean, fast interface. No server required — everything runs locally in your browser.

**Features:**
- Upload your own `comics_data.json` or drag and drop it onto the page
- Browse series from the sidebar and view all issues in grid or list view
- Filter by key issues or issues with variants
- Sort by price (high/low) or title
- Search across issue titles, key notes, and tags
- Click any issue to open a detail modal with pricing, key notes, tags, and variant covers

## Getting started

1. Clone or download the repo
2. Open `index.html` in your browser (or serve with `npx serve .`)
3. Drop in your `comics_data.json` — or hit **"continue with sample data"** to try it out

## JSON format

The app expects a JSON array of series objects. Each series contains issues, and each issue can contain variants. Example structure:

```json
[
  {
    "title": "Magik",
    "publisher": "Marvel",
    "dates": "1983–1984 · Vol. 1",
    "key_issues": 2,
    "total_issues": 4,
    "issues": [
      {
        "title": "Magik #1",
        "publisher": "Marvel",
        "year": "1983",
        "is_key": true,
        "key_badge": "1st Appearance",
        "cover_image": "https://...",
        "detail_url": "https://...",
        "price_low": "$1",
        "price_mid": "$2",
        "price_high": "$4",
        "key_notes": ["Origin of Illyana Rasputin"],
        "tags": [],
        "has_variants": true,
        "variant_count": 2,
        "variants": []
      }
    ]
  }
]
```

## Files

| File | Description |
|------|-------------|
| `index.html` | Main app shell |
| `styles.css` | All styling |
| `app.js` | App logic — rendering, filtering, sorting, modals |
| `data.js` | Sample data (`window.COMICS_DATA = [...]`) |

## Made by Hammy
