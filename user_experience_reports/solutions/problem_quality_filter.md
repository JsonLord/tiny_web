
### Problem: Hidden Quality Tier Filters
**Category:** Choice Architecture
**Proposed Solution:** Move quality tiers to a "Featured Filter" bar at the top of the product grid for high-intent shoppers like Friedrich.

```html
<div class="featured-filters">
    <span>Quality Tier:</span>
    <button class="filter-chip active">Premium</button>
    <button class="filter-chip">Standard</button>
    <button class="filter-chip">Basic</button>
</div>
<style>
.featured-filters {
    display: flex;
    gap: 10px;
    padding: 15px;
    background: #f9f9f9;
    align-items: center;
}
.filter-chip {
    padding: 8px 16px;
    border: 1px solid #ccc;
    background: white;
    cursor: pointer;
}
.filter-chip.active {
    background: #000;
    color: #fff;
    border-color: #000;
}
</style>
```
