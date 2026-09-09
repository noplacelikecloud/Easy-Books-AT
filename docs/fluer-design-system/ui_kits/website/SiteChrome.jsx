function SiteWordmark({ size = 24 }) {
  return <span style={{fontFamily:"var(--font-sans)",fontSize:size*0.86,fontWeight:600,letterSpacing:"-0.03em",color:"var(--text-strong)"}}>Fluer <span style={{fontWeight:400,color:"var(--text-muted)"}}>Development</span></span>;
}

const DSChrome = window.FluerDesignSystem_fde5f8;
const ChButton = DSChrome.Button, ChIcon = DSChrome.Icon, ChLogo = DSChrome.Logo || SiteWordmark;

function SiteHeader({ view, onNav }) {
  const items = [["leistungen","Leistungen"],["arbeit","Arbeit"],["kontakt","Kontakt"]];
  return (
    <header style={{position:"sticky",top:0,zIndex:20,background:"var(--surface-glass)",backdropFilter:"blur(var(--blur-glass))",borderBottom:"1px solid var(--border-hairline)"}}>
      <div style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"0 var(--gutter-page)",height:68,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <button onClick={()=>onNav("start")} style={{border:"none",background:"none",cursor:"pointer",padding:0,fontFamily:"var(--font-sans)",fontSize:20,fontWeight:600,letterSpacing:"-0.03em",color:"var(--text-strong)"}}>
          <ChLogo size={24} showWordmark />
        </button>
        <nav style={{display:"flex",alignItems:"center",gap:"var(--space-9)"}}>
          {items.map(([k,l])=>(
            <button key={k} onClick={()=>onNav(k)} style={{border:"none",background:"none",cursor:"pointer",fontFamily:"var(--font-sans)",fontSize:"var(--text-sm)",color:view===k?"var(--text-strong)":"var(--text-muted)",fontWeight:view===k?500:400}}>{l}</button>
          ))}
          <ChButton size="sm" variant="secondary" iconAfter="arrow-up-right" onClick={()=>onNav("kontakt")}>Projekt anfragen</ChButton>
        </nav>
      </div>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer style={{borderTop:"1px solid var(--border-hairline)",background:"var(--n-25)",marginTop:"var(--space-13)"}}>
      <div style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-11) var(--gutter-page) var(--space-9)",display:"grid",gridTemplateColumns:"1.4fr 1fr 1fr",gap:"var(--space-10)"}}>
        <div>
          <ChLogo size={26} showWordmark />
          <p style={{marginTop:10,fontSize:"var(--text-sm)",color:"var(--text-muted)",maxWidth:"34ch"}}>Einzelunternehmen für Cloud-App-Entwicklung. Architektur, Umsetzung, Betrieb.</p>
        </div>
        {[["Leistungen",["Cloud-Architektur","App-Entwicklung","Betrieb & Monitoring","Audit"]],["Kontakt",["hallo@fluer.dev","+49 …","Impressum","Datenschutz"]]].map(([t,ls])=>(
          <div key={t}>
            <div className="fluer-eyebrow">{t}</div>
            <div style={{display:"grid",gap:8,marginTop:14}}>
              {ls.map(l=><span key={l} style={{fontSize:"var(--text-sm)",color:"var(--text-body)"}}>{l}</span>)}
            </div>
          </div>
        ))}
      </div>
      <div style={{maxWidth:"var(--container-wide)",margin:"0 auto",padding:"var(--space-6) var(--gutter-page)",borderTop:"1px solid var(--border-hairline)",display:"flex",justifyContent:"space-between",fontSize:"var(--text-2xs)",color:"var(--text-faint)"}}>
        <span>© 2026 Fluer Development</span><span style={{fontFamily:"var(--font-mono)"}}>Frankfurt am Main</span>
      </div>
    </footer>
  );
}

Object.assign(window,{SiteHeader,SiteFooter});
