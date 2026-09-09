One-line: modal decision or short form — 20px radius, blurred scrim, actions bottom-right.

```jsx
<Dialog title="Projekt löschen?" description="Diese Aktion kann nicht widerrufen werden."
  footer={<><Button variant="ghost">Abbrechen</Button><Button variant="danger">Löschen</Button></>} onClose={close} />
```

Positioned `absolute` inside its container, so it also works inside a framed mock. Never stack two dialogs.
