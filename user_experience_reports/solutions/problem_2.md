# Better UI: Dual-Input Calculator
```html
<div class="calculator-input-group">
  <label for="consumption">Ihr jährlicher Verbrauch (kWh):</label>
  <div class="input-wrapper">
    <input type="number" id="consumption" value="2500" class="numeric-input">
    <input type="range" min="500" max="10000" step="100" value="2500" oninput="consumption.value=this.value">
  </div>
</div>
<style>
.numeric-input {
  border: 2px solid #005f73;
  padding: 8px;
  border-radius: 4px;
  font-weight: bold;
}
</style>
```
