function ShellWordmark({ size = 24 }) {
  return <span style={{fontFamily:"var(--font-sans)",fontSize:size*0.86,fontWeight:600,letterSpacing:"-0.03em",color:"var(--text-strong)"}}>Fluer <span style={{fontWeight:400,color:"var(--text-muted)"}}>Development</span></span>;
}

const DSShell = window.FluerDesignSystem_fde5f8;
const ShLogo = DSShell.Logo || ShellWordmark, ShIcon = DSShell.Icon, ShIconButton = DSShell.IconButton, ShBadge = DSShell.Badge, ShTooltip = DSShell.Tooltip;

const NAV = [
  ["overview","Übersicht","layout-dashboard"],
  ["deployments","Deployments","rocket"],
  ["logs","Logs","scroll-text"],
  ["settings","Einstellungen","settings"],
];

function SideNav({ view, onNav }) {
  return (
    <aside style={{width:264,flex:"0 0 auto",borderRight:"1px solid var(--border-hairline)",background:"var(--n-25)",display:"flex",flexDirection:"column",padding:"var(--space-6)"}}>
      <div style={{display:"grid",gap:10,justifyItems:"start",padding:"var(--space-3) var(--space-3) var(--space-7)"}}>
        <ShLogo size={24} showWordmark />
        <ShBadge tone="brand">Console</ShBadge>
      </div>
      <div style={{display:"grid",gap:2}}>
        {NAV.map(([k,l,icon])=>{
          const on=view===k;
          return (
            <button key={k} onClick={()=>onNav(k)} style={{display:"flex",alignItems:"center",gap:10,height:34,padding:"0 10px",border:"1px solid "+(on?"var(--border-hairline)":"transparent"),borderRadius:"var(--radius-sm)",background:on?"var(--surface-card)":"transparent",boxShadow:on?"var(--shadow-xs)":"none",cursor:"pointer",fontFamily:"var(--font-sans)",fontSize:"var(--text-sm)",fontWeight:on?500:400,color:on?"var(--text-strong)":"var(--text-muted)",textAlign:"left",transition:"var(--transition-control)"}}>
              <ShIcon name={icon} size={16} />{l}
            </button>
          );
        })}
      </div>
      <div style={{marginTop:"auto",padding:"var(--space-5) var(--space-3)",borderTop:"1px solid var(--border-hairline)",display:"flex",alignItems:"center",gap:9}}>
        <span style={{width:26,height:26,borderRadius:"var(--radius-pill)",background:"var(--blue-100)",border:"1px solid var(--border-brand)",display:"inline-flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:600,color:"var(--blue-600)"}}>FD</span>
        <div style={{display:"grid",gap:1,flex:1}}>
          <span style={{fontSize:"var(--text-xs)",color:"var(--text-strong)"}}>Fluer Development</span>
          <span style={{fontSize:"var(--text-3xs)",color:"var(--text-faint)"}}>Team-Plan</span>
        </div>
        <ShIconButton icon="chevrons-up-down" size="sm" label="Konto wechseln" />
      </div>
    </aside>
  );
}

function TopBar({ title, breadcrumb, actions }) {
  return (
    <header style={{height:60,flex:"0 0 auto",borderBottom:"1px solid var(--border-hairline)",background:"var(--surface-glass)",backdropFilter:"blur(var(--blur-glass))",display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 var(--space-9)"}}>
      <div style={{display:"flex",alignItems:"center",gap:9}}>
        {breadcrumb?<><span style={{fontSize:"var(--text-sm)",color:"var(--text-faint)"}}>{breadcrumb}</span><ShIcon name="chevron-right" size={14} style={{color:"var(--text-faint)"}} /></>:null}
        <span style={{fontSize:"var(--text-md)",fontWeight:500,color:"var(--text-strong)"}}>{title}</span>
      </div>
      <div style={{display:"flex",alignItems:"center",gap:"var(--space-4)"}}>
        <ShTooltip content="Dokumentation"><ShIconButton icon="book-open" label="Dokumentation" /></ShTooltip>
        <ShTooltip content="Keine neuen Hinweise"><ShIconButton icon="bell" label="Hinweise" /></ShTooltip>
        {actions}
      </div>
    </header>
  );
}

Object.assign(window,{SideNav,TopBar});
