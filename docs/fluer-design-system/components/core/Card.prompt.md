One-line: the standard surface — use it to group, not to decorate; a page should rarely hold more than three.

```jsx
<Card title="Deployments" subtitle="Letzte 24 Stunden" actions={<IconButton icon="more-horizontal" label="Mehr" />}>
  …
</Card>
```

Depth is border-first: hairline border + `--shadow-sm`. `interactive` upgrades to `--shadow-md` on hover. `tone="sunken"` for inset regions (logs, previews) — no shadow.
