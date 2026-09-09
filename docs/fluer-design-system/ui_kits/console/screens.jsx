function ScreenWordmark({ size = 24 }) {
  return <span style={{fontFamily:"var(--font-sans)",fontSize:size*0.86,fontWeight:600,letterSpacing:"-0.03em",color:"var(--text-strong)"}}>Fluer <span style={{fontWeight:400,color:"var(--text-muted)"}}>Development</span></span>;
}

const DS = window.FluerDesignSystem_fde5f8;
const ScButton = DS.Button, ScIconButton = DS.IconButton, ScBadge = DS.Badge, ScTag = DS.Tag, ScCard = DS.Card, ScIcon = DS.Icon, ScInput = DS.Input, ScSelect = DS.Select, ScCheckbox = DS.Checkbox, ScLogo = DS.Logo || ScreenWordmark, ScSwitch = DS.Switch, ScTabs = DS.Tabs, ScTooltip = DS.Tooltip, ScDialog = DS.Dialog, ScToast = DS.Toast;

const PAGE = {padding:"var(--space-10) var(--space-9) var(--space-12)",maxWidth:1040,margin:"0 auto"};

function StatRow({ items }) {
  return (
    <div style={{display:"grid",gridTemplateColumns:`repeat(${items.length},1fr)`,border:"1px solid var(--border-hairline)",borderRadius:"var(--radius-lg)",background:"var(--surface-card)",boxShadow:"var(--shadow-sm)",overflow:"hidden"}}>
      {items.map(([label,value,sub],i)=>(
        <div key={label} style={{padding:"var(--space-7) var(--space-8)",borderLeft:i?"1px solid var(--border-hairline)":"none"}}>
          <div className="fluer-eyebrow">{label}</div>
          <div style={{fontSize:"var(--text-3xl)",fontWeight:600,letterSpacing:"var(--tracking-display)",color:"var(--text-strong)",marginTop:10,whiteSpace:"nowrap"}}>{value}</div>
          <div style={{fontSize:"var(--text-2xs)",color:"var(--text-muted)",marginTop:4}}>{sub}</div>
        </div>
      ))}
    </div>
  );
}

const DEPLOYS = [
  ["deploy_8f2c41","main","success","vor 4 Min.","42 s"],
  ["deploy_7b1a09","main","success","vor 3 Std.","39 s"],
  ["deploy_6c88d2","feat/billing","failed","vor 5 Std.","18 s"],
  ["deploy_5a2f70","main","success","gestern","44 s"],
];
const TONE = {success:["success","Erfolgreich"],failed:["danger","Fehlgeschlagen"],building:["info","Läuft"]};

function DeployTable({ rows = DEPLOYS, onOpen }) {
  return (
    <div style={{border:"1px solid var(--border-hairline)",borderRadius:"var(--radius-lg)",background:"var(--surface-card)",boxShadow:"var(--shadow-sm)",overflow:"hidden"}}>
      <div style={{display:"grid",gridTemplateColumns:"1.3fr 1fr .9fr .8fr auto",gap:"var(--space-6)",padding:"var(--space-5) var(--space-8)",background:"var(--n-25)",borderBottom:"1px solid var(--border-hairline)"}}>
        {["Deployment","Branch","Status","Dauer",""].map(h=><span key={h} className="fluer-eyebrow">{h}</span>)}
      </div>
      {rows.map(([id,branch,status,when,dur],i)=>{
        const [tone,label]=TONE[status];
        return (
          <div key={id} style={{display:"grid",gridTemplateColumns:"1.3fr 1fr .9fr .8fr auto",gap:"var(--space-6)",alignItems:"center",padding:"var(--space-6) var(--space-8)",borderTop:i?"1px solid var(--border-hairline)":"none"}}>
            <div style={{display:"grid",gap:2}}>
              <span style={{fontFamily:"var(--font-mono)",fontSize:"var(--text-xs)",color:"var(--text-strong)"}}>{id}</span>
              <span style={{fontSize:"var(--text-2xs)",color:"var(--text-faint)"}}>{when}</span>
            </div>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:"var(--text-sm)",color:"var(--text-body)"}}><ScIcon name="git-branch" size={14} style={{color:"var(--text-faint)"}} />{branch}</span>
            <span><ScBadge tone={tone} dot>{label}</ScBadge></span>
            <span style={{fontFamily:"var(--font-mono)",fontSize:"var(--text-xs)",color:"var(--text-muted)"}}>{dur}</span>
            <div style={{display:"flex",gap:2}}>
              <ScTooltip content="Log öffnen"><ScIconButton icon="scroll-text" size="sm" label="Log" onClick={onOpen} /></ScTooltip>
              <ScIconButton icon="more-horizontal" size="sm" label="Mehr" />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function OverviewScreen({ onDeploy }) {
  return (
    <div style={PAGE}>
      <div style={{display:"flex",alignItems:"flex-end",justifyContent:"space-between",gap:"var(--space-8)"}}>
        <div>
          <h1 style={{fontSize:"var(--text-3xl)"}}>fluer-console</h1>
          <p style={{marginTop:8,fontSize:"var(--text-sm)",color:"var(--text-muted)"}}>Produktion · eu-central-1 · zuletzt deployt vor 4 Minuten</p>
        </div>
        <div style={{display:"flex",gap:"var(--space-4)"}}>
          <ScButton variant="secondary" icon="external-link">Öffnen</ScButton>
          <ScButton icon="rocket" onClick={onDeploy}>Deploy starten</ScButton>
        </div>
      </div>
      <div style={{marginTop:"var(--space-9)"}}>
        <StatRow items={[["Verfügbarkeit","99,98 %","letzte 30 Tage"],["Antwortzeit","128 ms","p95"],["Requests","1,4 Mio.","letzte 7 Tage"],["Kosten","84 €","laufender Monat"]]} />
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1.6fr 1fr",gap:"var(--space-7)",marginTop:"var(--space-7)",alignItems:"start"}}>
        <ScCard title="Letzte Deployments" subtitle="Vier von 128" padding="sm" actions={<ScIconButton icon="more-horizontal" label="Mehr" />}>
          <div style={{display:"grid",gap:0,margin:"-4px 0"}}>
            {DEPLOYS.slice(0,3).map(([id,branch,status,when])=>{
              const [tone,label]=TONE[status];
              return (
                <div key={id} style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:12,padding:"11px 0",borderBottom:"1px solid var(--border-hairline)"}}>
                  <div style={{display:"grid",gap:2}}>
                    <span style={{fontFamily:"var(--font-mono)",fontSize:"var(--text-xs)",color:"var(--text-strong)"}}>{id}</span>
                    <span style={{fontSize:"var(--text-2xs)",color:"var(--text-faint)"}}>{branch} · {when}</span>
                  </div>
                  <ScBadge tone={tone} dot>{label}</ScBadge>
                </div>
              );
            })}
          </div>
        </ScCard>
        <ScCard title="Umgebung" padding="sm">
          <div style={{display:"grid",gap:12}}>
            <ScSwitch label="Auto-Deploy" description="Bei Push auf main." checked onChange={()=>{}} />
            <div style={{height:1,background:"var(--border-hairline)"}} />
            <ScSwitch label="Vorschau-Umgebungen" description="Pro Pull Request." checked={false} onChange={()=>{}} />
            <div style={{display:"flex",gap:6,flexWrap:"wrap",marginTop:2}}>
              <ScTag>eu-central-1</ScTag><ScTag>node 22</ScTag><ScTag>postgres 16</ScTag>
            </div>
          </div>
        </ScCard>
      </div>
    </div>
  );
}

function DeploymentsScreen({ onOpenLog }) {
  const [tab,setTab]=React.useState("alle");
  return (
    <div style={PAGE}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:"var(--space-8)"}}>
        <h1 style={{fontSize:"var(--text-3xl)"}}>Deployments</h1>
        <div style={{display:"flex",gap:"var(--space-4)",alignItems:"center"}}>
          <ScInput icon="search" placeholder="Suchen …" style={{width:220}} />
          <ScSelect options={["Alle Branches","main","feat/billing"]} style={{width:170}} />
        </div>
      </div>
      <ScTabs style={{marginTop:"var(--space-8)"}} value={tab} onChange={setTab}
        items={[{value:"alle",label:"Alle",count:128},{value:"prod",label:"Produktion",count:96},{value:"preview",label:"Vorschau",count:32}]} />
      <div style={{marginTop:"var(--space-8)"}}><DeployTable onOpen={onOpenLog} /></div>
      <div style={{marginTop:"var(--space-7)",background:"var(--surface-sunken)",border:"1px solid var(--border-hairline)",borderRadius:"var(--radius-lg)",padding:"var(--space-7) var(--space-8)",fontFamily:"var(--font-mono)",fontSize:"var(--text-xs)",lineHeight:1.7,color:"var(--text-muted)"}}>
        <div style={{color:"var(--text-strong)"}}>› deploy_8f2c41 · build log</div>
        <div>14:02:11  install  ✓ 412 Pakete aus Cache</div>
        <div>14:02:29  build    ✓ 18 Routen, 2,1 MB</div>
        <div>14:02:48  deploy   ✓ eu-central-1 aktiv</div>
      </div>
    </div>
  );
}

function SettingsScreen(){
  const [tab,setTab]=React.useState("allgemein");
  return (
    <div style={{...PAGE,maxWidth:820}}>
      <h1 style={{fontSize:"var(--text-3xl)"}}>Einstellungen</h1>
      <ScTabs style={{marginTop:"var(--space-8)"}} value={tab} onChange={setTab} items={[{value:"allgemein",label:"Allgemein"},{value:"env",label:"Variablen"},{value:"team",label:"Team"}]} />
      <div style={{display:"grid",gap:"var(--space-7)",marginTop:"var(--space-9)"}}>
        <ScCard title="Projekt" padding="md" footer="Änderungen wirken beim nächsten Deployment.">
          <div style={{display:"grid",gap:"var(--space-6)",maxWidth:420}}>
            <ScInput label="Projektname" defaultValue="fluer-console" hint="Kleinbuchstaben und Bindestriche." />
            <ScSelect label="Region" options={["eu-central-1 · Frankfurt","eu-west-1 · Dublin"]} />
            <ScCheckbox label="Build-Cache nutzen" description="Beschleunigt Deployments deutlich." checked onChange={()=>{}} />
          </div>
        </ScCard>
        <ScCard title="Gefahrenzone" subtitle="Diese Aktionen sind endgültig." padding="md">
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:"var(--space-8)"}}>
            <span style={{fontSize:"var(--text-sm)",color:"var(--text-muted)",maxWidth:"46ch"}}>Projekt samt Deployments, Logs und Variablen löschen.</span>
            <ScButton variant="danger" icon="trash-2">Projekt löschen</ScButton>
          </div>
        </ScCard>
      </div>
    </div>
  );
}

function LoginScreen({ onLogin }){
  return (
    <div style={{minHeight:"100vh",display:"grid",gridTemplateColumns:"1fr 1fr"}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"center",padding:"var(--space-11)"}}>
        <div style={{width:340}}>
          <ScLogo size={26} showWordmark />
          <h1 style={{fontSize:"var(--text-2xl)",marginTop:"var(--space-9)"}}>Anmelden</h1>
          <p style={{marginTop:8,fontSize:"var(--text-sm)",color:"var(--text-muted)"}}>Console für Projekte, Deployments und Logs.</p>
          <div style={{display:"grid",gap:"var(--space-6)",marginTop:"var(--space-9)"}}>
            <ScInput label="E-Mail" defaultValue="hallo@fluer.dev" icon="mail" />
            <ScInput label="Passwort" type="password" defaultValue="········" />
            <ScButton fullWidth size="lg" onClick={onLogin} iconAfter="arrow-right">Weiter</ScButton>
            <ScButton fullWidth variant="secondary" icon="github">Mit GitHub anmelden</ScButton>
          </div>
          <p style={{marginTop:"var(--space-8)",fontSize:"var(--text-2xs)",color:"var(--text-faint)"}}>Hosting und Daten ausschließlich in der EU.</p>
        </div>
      </div>
      <div style={{background:"var(--surface-inverse)",display:"flex",alignItems:"flex-end",padding:"var(--space-11)"}}>
        <div>
          <p style={{fontSize:"var(--text-xl)",color:"var(--text-inverse)",maxWidth:"26ch",lineHeight:1.4}}>„Ein Ansprechpartner von Entwurf bis Betrieb."</p>
          <p style={{marginTop:"var(--space-6)",fontFamily:"var(--font-mono)",fontSize:"var(--text-2xs)",color:"rgba(255,255,255,.45)"}}>Fluer Development · Cloud App Entwicklung</p>
        </div>
      </div>
    </div>
  );
}

Object.assign(window,{OverviewScreen,DeploymentsScreen,SettingsScreen,LoginScreen,DeployTable,StatRow});
