# UI Kit — Fluer Console

Anwendungsfläche: Login → App-Shell (Sidebar + TopBar) mit vier Ansichten.

Dateien: `AppShell.jsx` (SideNav, TopBar), `screens.jsx` (LoginScreen, OverviewScreen, DeploymentsScreen, SettingsScreen, StatRow, DeployTable), `index.html` (Klickpfad).

Klickpfad: Anmelden → Übersicht → „Deploy starten" → Dialog bestätigen → Erfolgs-Toast unten rechts → Deployments → Log-Zeile → Einstellungen.

Alle Primitives kommen aus dem Bundle (Button, IconButton, Badge, Tag, Card, Icon, Input, Select, Checkbox, Switch, Tabs, Dialog, Toast, Tooltip); im Kit selbst existieren nur produktspezifische Kompositionen (Shell, Tabelle, Statistikzeile).
