# Better UI: Transparent Navigation
```html
<div class="nav-fix">
  <button class="nav-trigger" aria-haspopup="true">Strom & Gas</button>
  <ul class="nav-visible-fallback">
    <li><a href="/strom/tarife">Alle Tarife</a></li>
    <li><a href="/strom/oekostrom">Ökostrom</a></li>
  </ul>
</div>
<style>
.nav-visible-fallback { display: block !important; opacity: 1; position: relative; }
</style>
```