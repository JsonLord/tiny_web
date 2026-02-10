### Problem: Intrusive blocking cookie banner
### Solution: Non-blocking footer-based consent bar

```html
<div id="ux-consent-bar" style="position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid #ccc; padding: 20px; z-index: 9999; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -2px 10px rgba(0,0,0,0.1);">
  <div style="flex: 1; padding-right: 20px; font-family: sans-serif; font-size: 14px;">
    We use cookies to enhance your experience. <a href="/privacy" style="color: #007bff;">Learn more</a>
  </div>
  <div style="display: flex; gap: 10px;">
    <button onclick="document.getElementById('ux-consent-bar').style.display='none'" style="background: #f8f9fa; border: 1px solid #ccc; padding: 8px 16px; cursor: pointer;">Settings</button>
    <button onclick="document.getElementById('ux-consent-bar').style.display='none'" style="background: #007bff; color: #fff; border: none; padding: 8px 16px; cursor: pointer;">Accept All</button>
  </div>
</div>
```
