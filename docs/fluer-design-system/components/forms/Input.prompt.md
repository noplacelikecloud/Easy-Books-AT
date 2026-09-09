One-line: the text field for every form — label above, hint or error below, focus ring in teal.

```jsx
<Input label="Projektname" placeholder="mein-projekt" hint="Kleinbuchstaben und Bindestriche." />
<Input label="Notiz" multiline rows={4} />
```

Fields are 38px tall with a 10px radius and an inset shadow — never a flat borderless field. Error state colours the border and the message, no icon.
