### Problem: Text-heavy service descriptions
### Solution: Interactive Inquiry Cards

```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; font-family: sans-serif;">
  <div style="border: 1px solid #eee; border-radius: 8px; overflow: hidden; transition: transform 0.2s; cursor: pointer;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
    <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center;">
      <span style="font-size: 48px;">♻️</span>
    </div>
    <div style="padding: 20px;">
      <h3 style="margin: 0 0 10px 0;">Recycling Solutions</h3>
      <p style="color: #666; font-size: 14px;">Optimized waste streams for large-scale operations.</p>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
        <span style="font-weight: bold; color: #28a745;">ISO 14001 Certified</span>
        <button style="background: #28a745; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Add to Inquiry</button>
      </div>
    </div>
  </div>
</div>
```
