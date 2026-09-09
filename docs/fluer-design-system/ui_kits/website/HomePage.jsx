const DSHome = window.FluerDesignSystem_fde5f8;
const HmBadge = DSHome.Badge, HmButton = DSHome.Button, HmCard = DSHome.Card, HmIcon = DSHome.Icon, HmTag = DSHome.Tag;

const SERVICES = [
  ["cloud","Cloud-Architektur","Aufbau auf AWS oder Hetzner: Netzwerk, Datenhaltung, Deployment-Pfad. Dokumentiert und übergabefähig."],
  ["layout-dashboard","App-Entwicklung","Web-Anwendungen mit React und TypeScript, API in Node oder Go. Ein Ansprechpartner von Entwurf bis Release."],
  ["activity","Betrieb & Monitoring","Logging, Alerting, Backups. Monatlicher Bericht statt Blackbox."],
];

const WORK = [
  ["Logistik-Portal","Sendungsverfolgung für 40 Standorte","eu-central-1","React · Go · Postgres"],
  ["Praxis-Terminsystem","Buchung und Erinnerungen, DSGVO-konform","eu-central-1","React · Node · Redis"],
  ["Field-Service-App","Offline-fähige Auftragserfassung","eu-west-1","React Native · Node"],
];

function HomePage({ onNav }) {
  return (
    <main>
      <section style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-14) var(--gutter-page) var(--space-13)"}}>
        <div style={{maxWidth:660}}>
          <span className="fluer-eyebrow">Cloud App Entwicklung</span>
          <h1 style={{fontSize:"var(--text-6xl)",lineHeight:1.02,letterSpacing:"var(--tracking-display)",marginTop:"var(--space-6)"}}>Cloud-Apps, sauber gebaut.</h1>
        </div>
        <p style={{marginTop:"var(--space-7)",maxWidth:"52ch",fontSize:"var(--text-lg)",lineHeight:"var(--lh-relaxed)",color:"var(--text-muted)"}}>
          Fluer Development ist ein Einzelunternehmen. Sie sprechen mit der Person, die Ihre Anwendung entwirft, baut und betreibt.
        </p>
        <div style={{display:"flex",gap:"var(--space-5)",marginTop:"var(--space-9)"}}>
          <HmButton size="lg" iconAfter="arrow-right" onClick={()=>onNav("kontakt")}>Projekt anfragen</HmButton>
          <HmButton size="lg" variant="ghost" onClick={()=>onNav("arbeit")}>Arbeiten ansehen</HmButton>
        </div>
        <div style={{display:"flex",gap:"var(--space-8)",marginTop:"var(--space-12)",paddingTop:"var(--space-7)",borderTop:"1px solid var(--border-hairline)",flexWrap:"wrap"}}>
          {[["9 Jahre","Erfahrung"],["24","ausgelieferte Anwendungen"],["EU","Hosting ausschließlich in der EU"]].map(([v,l])=>(
            <div key={l} style={{display:"grid",gap:4,minWidth:180}}>
              <span style={{fontSize:"var(--text-2xl)",fontWeight:600,color:"var(--text-strong)",letterSpacing:"var(--tracking-heading)"}}>{v}</span>
              <span style={{fontSize:"var(--text-sm)",color:"var(--text-muted)"}}>{l}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="leistungen" style={{background:"var(--bg-page-alt)",borderTop:"1px solid var(--border-hairline)",borderBottom:"1px solid var(--border-hairline)"}}>
        <div style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-13) var(--gutter-page)"}}>
          <span className="fluer-eyebrow">Leistungen</span>
          <h2 style={{marginTop:"var(--space-5)",maxWidth:"26ch"}}>Drei Dinge, gründlich statt vieles nebenbei.</h2>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:"var(--space-7)",marginTop:"var(--space-10)"}}>
            {SERVICES.map(([icon,t,d])=>(
              <div key={t} style={{background:"var(--surface-card)",border:"1px solid var(--border-hairline)",borderRadius:"var(--radius-lg)",boxShadow:"var(--shadow-sm)",padding:"var(--space-8)"}}>
                <span style={{display:"inline-flex",alignItems:"center",justifyContent:"center",width:38,height:38,borderRadius:"var(--radius-md)",background:"var(--surface-brand-soft)",border:"1px solid var(--border-brand)",color:"var(--text-brand)"}}><HmIcon name={icon} size={19} /></span>
                <h3 style={{marginTop:"var(--space-6)",fontSize:"var(--text-lg)"}}>{t}</h3>
                <p style={{marginTop:"var(--space-4)",fontSize:"var(--text-sm)",lineHeight:"var(--lh-relaxed)",color:"var(--text-muted)"}}>{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="arbeit" style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-13) var(--gutter-page) 0"}}>
        <span className="fluer-eyebrow">Arbeit</span>
        <h2 style={{marginTop:"var(--space-5)"}}>Ausgewählte Projekte</h2>
        <div style={{marginTop:"var(--space-9)",border:"1px solid var(--border-hairline)",borderRadius:"var(--radius-lg)",background:"var(--surface-card)",boxShadow:"var(--shadow-sm)",overflow:"hidden"}}>
          {WORK.map(([t,d,region,stack],i)=>(
            <div key={t} style={{display:"grid",gridTemplateColumns:"1.1fr 1.4fr auto",gap:"var(--space-7)",alignItems:"center",padding:"var(--space-7) var(--space-8)",borderTop:i?"1px solid var(--border-hairline)":"none"}}>
              <div style={{display:"grid",gap:4}}>
                <span style={{fontSize:"var(--text-md)",fontWeight:500,color:"var(--text-strong)"}}>{t}</span>
                <span style={{fontFamily:"var(--font-mono)",fontSize:"var(--text-2xs)",color:"var(--text-faint)"}}>{region}</span>
              </div>
              <span style={{fontSize:"var(--text-sm)",color:"var(--text-muted)"}}>{d}</span>
              <div style={{display:"flex",gap:"var(--space-3)",alignItems:"center"}}>
                <HmTag>{stack}</HmTag><HmIcon name="arrow-up-right" size={16} style={{color:"var(--text-faint)"}} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="kontakt" style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-13) var(--gutter-page) 0"}}>
        <div style={{background:"var(--surface-inverse)",borderRadius:"var(--radius-2xl)",padding:"var(--space-12) var(--space-11)",display:"grid",gridTemplateColumns:"1.3fr 1fr",gap:"var(--space-10)",alignItems:"center"}}>
          <div>
            <h2 style={{color:"var(--text-inverse)",maxWidth:"22ch",fontSize:"var(--text-3xl)"}}>Erzählen Sie mir vom Projekt.</h2>
            <p style={{marginTop:"var(--space-6)",fontSize:"var(--text-md)",color:"rgba(255,255,255,.66)",maxWidth:"44ch"}}>Erstgespräch, 30 Minuten, ohne Kosten. Danach erhalten Sie eine schriftliche Einschätzung zu Aufwand und Vorgehen.</p>
          </div>
          <div style={{display:"grid",gap:"var(--space-5)",justifyItems:"start"}}>
            <HmButton size="lg" icon="mail">hallo@fluer.dev</HmButton>
            <span style={{fontFamily:"var(--font-mono)",fontSize:"var(--text-2xs)",color:"rgba(255,255,255,.5)"}}>Antwort innerhalb eines Werktags</span>
          </div>
        </div>
      </section>
    </main>
  );
}

Object.assign(window,{HomePage});
