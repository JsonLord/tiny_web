
### Problem: Search Result Information Density (Wardrobes)
**Category:** Information Architecture / Scannability
**Proposed Solution:** Add a "Technical Quick-Spec" badge to search result cards, showing key dimensions (Height, Width, Depth) without needing a click.

```html
<div class="product-card">
    <img src="schrank.jpg" alt="Wardrobe">
    <div class="quick-specs">
        <span class="spec-badge">H: 300cm</span>
        <span class="spec-badge">W: 150cm</span>
    </div>
    <h3>Premium Wandschrank</h3>
    <p class="price">1.200,00 €</p>
</div>
<style>
.spec-badge {
    background: #e0e0e0;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    color: #333;
    margin-right: 4px;
}
</style>
```
