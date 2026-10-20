(function(){
"use strict";
var T=Object.assign({dot:".",mh:"Sizes that share a diameter take different holes: a #8 machine screw and a #8 wood screw are not interchangeable. A caliper reading is never exact, so measure the thread crests and expect a small error.",enter:"Enter a diameter greater than zero.",go:"Look up",err:"Could not read that size. Try #8, #8-32, 1/4-20, M6, M8 x 1 or 1\".",copy:"Copy",copied:"Copied",nomatch:"No standard size matches that.",major:"Major diameter",src:"Source",rel:"Related sizes",cap:"Major diameter, true proportion. Length not shown."},window.I18N||{});
var I18=window.I18N||{},tr=function(x){return x in I18?I18[x]:x};
var $=function(s,r){return(r||document).querySelector(s)};
var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
var D={},ready;
// theme
var tb=$("#theme");if(tb)tb.addEventListener("click",function(){var r=document.documentElement,d=r.getAttribute("data-theme")==="dark"?"light":"dark";r.setAttribute("data-theme",d);try{localStorage.setItem("theme",d)}catch(e){}});
function load(){return ready||(ready=Promise.all(["imperial-machine-screws","metric-machine-screws","wood-screws","drill-bits"].map(function(n){return fetch("/data/"+n+".json").then(function(r){return r.json()})})).then(function(a){D.imp=a[0].rows;D.met=a[1].rows;D.wood=a[2].rows;D.drills=a[3];D.I={};D.imp.forEach(function(r){D.I[r.label]=r});D.M={};D.met.forEach(function(r){D.M[r.label]=r});D.W={};D.wood.forEach(function(r){D.W[r.label]=r})}))}
// parser: returns {fam,row,tpi,pitch} or {err}
function parse(q,type){
 var s=q.trim().toLowerCase().replace(/\u00d7/g,"x").replace(/\s+/g," "),m,label,tpi=null,pitch=null,fam;
 if(!s)return{err:T.err};
 if(m=s.match(/^m ?(\d+(?:\.\d+)?)(?: ?x ?(\d+(?:\.\d+)?))?$/)){var r=D.M["M"+m[1]];if(!r)return{err:T.nomatch};
  pitch=m[2]?parseFloat(m[2]):r.coarsePitch;
  if(pitch!==r.coarsePitch&&!r.finePitches.some(function(f){return f.pitch===pitch}))return{err:r.label+tr(" has no standard ")+pitch+tr(" mm pitch. Standard pitches: ")+[r.coarsePitch].concat(r.finePitches.map(function(f){return f.pitch})).join(", ")+" mm."};
  return{fam:"met",row:r,pitch:pitch}}
 if(m=s.match(/^(\d+(?:\/\d+)?) ?(?:"|in|inch)$/)){label=m[1];fam="imp"}
 else if(m=s.match(/^#?(\d+)-(\d+)$/)){label="#"+m[1];tpi=+m[2];fam="imp"}
 else if(m=s.match(/^(\d+\/\d+)(?:-(\d+))?$/)){label=m[1];tpi=m[2]?+m[2]:null;fam="imp"}
 else if(m=s.match(/^#?(\d+)$/)){label="#"+m[1];fam="imp"}
 else return{err:T.err};
 if(type==="metric")return{err:tr("Metric sizes start with M, for example M6 or M8 x 1.")};
 if(type==="wood"){var w=D.W[label];if(!w)return{err:tr("Wood screws use gauge numbers (#2 to #14). ")+label+tr(" is not a standard wood screw size here.")};return{fam:"wood",row:w}}
 var row=D.I[label];if(!row)return{err:T.nomatch};
 var ser=null;if(tpi){ser=row.unc&&row.unc.tpi===tpi?"unc":row.unf&&row.unf.tpi===tpi?"unf":null;if(!ser)return{err:row.label+tr(" has no standard thread of ")+tpi+tr(" TPI thread. Standard: ")+[row.unc&&row.unc.tpi,row.unf&&row.unf.tpi].filter(Boolean).join(tr(" and "))+" TPI."}}
 return{fam:"imp",row:row,ser:ser}}
var f4=function(x){return(+x).toFixed(4)};
function fields(p){var r=p.row,o=[];
 if(p.fam==="imp"){["unc","unf"].forEach(function(k){if(r[k]&&(!p.ser||p.ser===k))o.push([r.label+"-"+r[k].tpi+" "+k.toUpperCase(),r[k].tpi+" TPI"],[tr("Tap drill (")+k.toUpperCase()+")",r[k].tapDrill+" ("+f4(r[k].tapDrillIn)+" in)"])});
  [["close",tr("Close")],["normal",tr("Normal")],["loose",tr("Loose")]].forEach(function(c){var v=r.clearance[c[0]];o.push([c[1]+tr(" clearance"),v.drill+" ("+f4(v.in)+" in)"])});}
 else if(p.fam==="met"){var fine=r.finePitches.filter(function(f){return f.pitch===p.pitch})[0];o.push([tr("Pitch"),p.pitch+" mm"+(fine?tr(" (fine)"):tr(" (coarse)"))],[tr("Tap drill"),(fine?fine.tapDrill:r.tapDrillCoarse).toFixed(2)+" mm"]);
  [["fine",tr("Fine")],["medium",tr("Medium")],["coarse",tr("Coarse")]].forEach(function(c){o.push([c[1]+tr(" clearance (ISO 273)"),r.clearance[c[0]].toFixed(1)+" mm"])})}
 else{o.push([tr("Pilot, softwood"),r.pilotSoftwood+" ("+f4(r.pilotSoftwoodIn)+" in)"],[tr("Pilot, hardwood"),r.pilotHardwood+" ("+f4(r.pilotHardwoodIn)+" in)"],[tr("Clearance"),r.clearance+" ("+f4(r.clearanceIn)+" in)"])}
 return o}
function drawing(d){var s=120,h=Math.max(d*s,5),w=300,hd=Math.max(h*1.7,9),y=70,hw=Math.max(h*.7,6),i,t="";
 for(i=hw+20;i<w-30;i+=Math.max(h*.18,2.5))t+='<line x1="'+i+'" y1="'+(y-h/2)+'" x2="'+(i-h*.15)+'" y2="'+(y+h/2)+'" stroke="currentColor" stroke-width=".8" opacity=".5"/>';
 return '<svg viewBox="0 0 '+w+' 150" role="img" aria-label="'+esc(T.cap)+'" style="color:var(--ink-2);width:100%"><rect x="6" y="'+(y-hd/2)+'" width="'+hw+'" height="'+hd+'" rx="1" fill="var(--accent-soft)" stroke="currentColor"/><rect x="'+(6+hw)+'" y="'+(y-h/2)+'" width="'+(w-40-hw)+'" height="'+h+'" fill="var(--surface)" stroke="currentColor"/>'+t+'<path d="M'+(w-40)+' '+(y-h/2)+' l-5 '+(h/4)+' l5 '+(h/4)+' l-5 '+(h/4)+' l5 '+(h/4)+'" fill="none" stroke="currentColor"/><line x1="'+(w-14)+'" y1="'+(y-h/2)+'" x2="'+(w-14)+'" y2="'+(y+h/2)+'" stroke="var(--accent)" stroke-width="1.5"/><path d="M'+(w-17)+' '+(y-h/2+5)+' l3 -5 l3 5 M'+(w-17)+' '+(y+h/2-5)+' l3 5 l3 -5" fill="none" stroke="var(--accent)"/><text x="'+(w/2)+'" y="145" text-anchor="middle" font-size="11" fill="currentColor">'+esc(T.cap)+'</text></svg>'}
function ladder(rows,sel,dk){var s=60,g=9,x=6,out="",W=0,i,pos=[];
 rows.forEach(function(r){var d=r[dk]*s;pos.push([x+d/2,d]);x+=d+g});W=x;
 rows.forEach(function(r,i){var c=pos[i],on=r.label===sel;out+='<circle class="dot'+(on?" sel":"")+'" tabindex="0" role="button" aria-label="'+esc(r.label)+'" data-l="'+esc(r.label)+'" cx="'+c[0]+'" cy="40" r="'+Math.max(c[1]/2,1.5)+'"/>';if(on||c[1]>=14)out+='<text class="lb" x="'+c[0]+'" y="'+(86+(i%3)*12)+'">'+esc(r.label)+'</text>'});
 return '<svg viewBox="0 0 '+W+' 124" aria-label="'+tr("Size ladder, circles at true relative diameter")+'">'+out+'</svg>'}
function render(p,q){var r=p.row,rows=p.fam==="met"?D.met:p.fam==="wood"?D.wood:D.imp,dk=p.fam==="met"?"majorDiameterMm":"majorDiameterIn",din=r.majorDiameterIn,dmm=r.majorDiameterMm;
 var rel=rows.map(function(x){return x.label}).filter(function(l){return Math.abs(rows.map(function(x){return x.label}).indexOf(l)-rows.indexOf(r))<=2&&l!==r.label});
 var h='<div class="res"><div><div class="big">'+f4(din)+' in<span class="eq">'+dmm+' mm</span><button class="copy" type="button" data-c="'+f4(din)+' in / '+dmm+' mm">'+T.copy+'</button></div><dl>'+fields(p).map(function(f){return"<dt>"+esc(f[0])+"</dt><dd>"+esc(f[1])+"</dd>"}).join("")+'</dl>'+(p.fam==="wood"?'<p class="note">'+esc(r.assumption)+'</p>':"")+'<p class="hint">'+T.src+": "+esc(r.source)+'</p><div class="chips" aria-label="'+T.rel+'">'+rel.map(function(l){return'<button type="button" class="chip" data-q="'+esc(l)+'">'+esc(l)+'</button>'}).join("")+'</div></div><div>'+drawing(din)+'</div></div><div class="ladder">'+ladder(rows,r.label,p.fam==="met"?"majorDiameterMm":"majorDiameterIn")+'</div>';
 return h}
function initLookup(){var f=$("#lookup");if(!f)return;var out=$("#result"),inp=$("#q"),ty=$("#type");
 function run(q){load().then(function(){var p=parse(q,ty.value);out.innerHTML=p.err?'<p class="note">'+esc(p.err)+'</p>':render(p,q)})}
 f.addEventListener("submit",function(e){e.preventDefault();run(inp.value)});
 out.addEventListener("click",function(e){var t=e.target;if(t.dataset.c){navigator.clipboard&&navigator.clipboard.writeText(t.dataset.c);t.textContent=T.copied;setTimeout(function(){t.textContent=T.copy},1200)}var q=t.dataset.q||(t.classList.contains("dot")&&t.dataset.l);if(q){inp.value=q;run(q)}});
 out.addEventListener("keydown",function(e){if((e.key==="Enter"||e.key===" ")&&e.target.classList.contains("dot")){e.preventDefault();inp.value=e.target.dataset.l;run(inp.value)}});
 var u=new URLSearchParams(location.search).get("q");if(u){inp.value=u;run(u)}}
// drills
function allDrills(){var o=[];["number","letter","fractional","metric"].forEach(function(s){D.drills[s].forEach(function(d){o.push({s:s,label:d.label,inch:d.inch,mm:d.mm})})});return o}
function nearest(inch){var best={},d=allDrills();d.forEach(function(x){var e=Math.abs(x.inch-inch);if(!best[x.s]||e<best[x.s].e)best[x.s]={x:x,e:e}});return best}
var SN={number:tr("Number"),letter:tr("Letter"),fractional:tr("Fractional"),metric:tr("Metric")};
function initFinder(){var s=$("#fSize");if(!s)return;var pu=$("#fPurpose"),va=$("#fVar"),out=$("#fOut");
 load().then(function(){s.innerHTML='<optgroup label="'+tr("Machine screw (inch)")+'">'+D.imp.map(function(r){return"<option value='imp|"+r.label+"'>"+esc(r.label)+"</option>"}).join("")+'</optgroup><optgroup label="'+tr("Metric machine screw")+'">'+D.met.map(function(r){return"<option value='met|"+r.label+"'>"+esc(r.label)+"</option>"}).join("")+'</optgroup><optgroup label="'+tr("Wood screw")+'">'+D.wood.map(function(r){return"<option value='wood|"+r.label+"'>"+esc(r.label)+tr(" wood</option>")}).join("")+"</optgroup>";s.value="imp|#8";purposes();calc()});
 function cur(){var a=s.value.split("|");return{fam:a[0],row:a[0]==="imp"?D.I[a[1]]:a[0]==="met"?D.M[a[1]]:D.W[a[1]]}}
 function purposes(){var c=cur(),o=c.fam==="wood"?[["pilot",tr("Wood pilot hole")],["clear",tr("Clearance hole")]]:[["tap",tr("Tap drill")],["clear",tr("Clearance hole")]];var keep=pu.value;pu.innerHTML=o.map(function(x){return"<option value='"+x[0]+"'>"+x[1]+"</option>"}).join("");if(o.some(function(x){return x[0]===keep}))pu.value=keep;vars()}
 function vars(){var c=cur(),p=pu.value,o=[];
  if(c.fam==="imp"){if(p==="tap"){["unc","unf"].forEach(function(k){if(c.row[k])o.push([k,k.toUpperCase()+" "+c.row[k].tpi+" TPI"])})}else o=[["close",tr("Close fit")],["normal",tr("Normal fit")],["loose",tr("Loose fit")]]}
  else if(c.fam==="met"){if(p==="tap")o=[["c",tr("Coarse ")+c.row.coarsePitch+" mm"]].concat(c.row.finePitches.map(function(f){return["f"+f.pitch,tr("Fine ")+f.pitch+" mm"]}));else o=[["fine",tr("Fine (H12)")],["medium",tr("Medium (H13)")],["coarse",tr("Coarse (H14)")]]}
  else o=p==="pilot"?[["soft",tr("Softwood")],["hard",tr("Hardwood")]]:[["x",tr("Standard")]];
  va.innerHTML=o.map(function(x){return"<option value='"+x[0]+"'>"+esc(x[1])+"</option>"}).join("")}
 function calc(){var c=cur(),p=pu.value,v=va.value,name,inch,meth,src=c.row.source;
  if(c.fam==="imp"){if(p==="tap"){var t=c.row[v];name=t.tapDrill;inch=t.tapDrillIn;meth=tr("75% thread tap drill for ")+c.row.label+"-"+t.tpi+" "+v.toUpperCase()}else{var q=c.row.clearance[v];name=q.drill;inch=q.in;meth="ASME B18.2.8, "+tr(v==="close"?tr("Close fit"):v==="normal"?tr("Normal fit"):tr("Loose fit"))}}
  else if(c.fam==="met"){var mm;if(p==="tap"){if(v==="c")mm=c.row.tapDrillCoarse;else mm=c.row.finePitches.filter(function(f){return"f"+f.pitch===v})[0].tapDrill;meth=tr("Tap drill = diameter minus pitch")}else{mm=c.row.clearance[v];meth="ISO 273, "+tr(v==="fine"?tr("Fine (H12)"):v==="medium"?tr("Medium (H13)"):tr("Coarse (H14)"))}name=mm.toFixed(2)+" mm";inch=mm/25.4}
  else{if(p==="pilot"){name=v==="soft"?c.row.pilotSoftwood:c.row.pilotHardwood;inch=v==="soft"?c.row.pilotSoftwoodIn:c.row.pilotHardwoodIn;meth=tr("Pilot hole guidance for ")+(v==="soft"?tr("softwood"):tr("hardwood"))+tr(". Test on scrap: species and hardness change the ideal size.")}else{name=c.row.clearance;inch=c.row.clearanceIn;meth=tr("Clearance hole for the shank, guidance")}}
  var n=nearest(inch);out.innerHTML='<div class="big">'+esc(name)+'<span class="eq">'+f4(inch)+' in</span></div><p>'+esc(meth)+(/[.。]$/.test(meth)?'':T.dot)+'</p><p class="hint">'+T.src+": "+esc(src)+'</p><h3>'+tr("Nearest common drill, by series")+'</h3><dl>'+Object.keys(SN).map(function(k){var b=n[k];return"<dt>"+SN[k]+"</dt><dd>"+esc(b.x.label)+" ("+f4(b.x.inch)+" in, "+(b.e<=.00005?tr("exact"):(b.x.inch>inch?"+":"-")+f4(b.e))+")</dd>"}).join("")+"</dl>"}
 s.addEventListener("change",function(){purposes();calc()});pu.addEventListener("change",function(){vars();calc()});va.addEventListener("change",calc)}
function initMatch(){var f=$("#match");if(!f)return;var out=$("#mOut");
 f.addEventListener("submit",function(e){e.preventDefault();var v=parseFloat($("#mVal").value),u=$("#mUnit").value;if(!(v>0)){out.innerHTML='<p class="note">'+T.enter+'</p>';return}
  load().then(function(){var inch=u==="mm"?v/25.4:v,g={};
   D.imp.forEach(function(r){add(r.majorDiameterIn,r.label+tr(" machine"))});D.met.forEach(function(r){add(r.majorDiameterIn,r.label+tr(" metric"))});D.wood.forEach(function(r){add(r.majorDiameterIn,r.label+tr(" wood"))});
   function add(d,l){var k=d.toFixed(3);(g[k]=g[k]||{d:d,l:[]}).l.push(l)}
   var a=Object.keys(g).map(function(k){return g[k]}).sort(function(x,y){return Math.abs(x.d-inch)-Math.abs(y.d-inch)}).slice(0,3);
   out.innerHTML='<table><thead><tr><th>'+tr("Sizes")+'</th><th>'+tr("Diameter")+'</th><th>'+tr("Off by")+'</th></tr></thead><tbody>'+a.map(function(x){return'<tr><td data-label="'+tr("Sizes")+'">'+esc(x.l.join(", "))+'</td><td data-label="'+tr("Diameter")+'">'+f4(x.d)+" in / "+(x.d*25.4).toFixed(2)+' mm</td><td data-label="'+tr("Off by")+'">'+(Math.abs(x.d-inch)*25.4).toFixed(2)+" mm</td></tr>"}).join("")+'</tbody></table><p class="hint">'+T.mh+'</p>'})})}
// explorer
function initExplorer(){var tb=$("#xTbl");if(!tb)return;var st={fam:"imp",q:"",sort:"d"},tabs=document.querySelectorAll("#xTabs button");
 var u=new URLSearchParams(location.search);if(u.get("fam"))st.fam=u.get("fam");st.q=u.get("q")||"";st.sort=u.get("sort")||"d";$("#xQ").value=st.q;$("#xSort").value=st.sort;
 var C={imp:[[tr("Size"),"label"],[tr("Diameter (in)"),function(r){return f4(r.majorDiameterIn)}],[tr("Diameter (mm)"),function(r){return r.majorDiameterMm}],["UNC",function(r){return r.unc?r.unc.tpi+tr(" TPI, tap ")+r.unc.tapDrill:"-"}],["UNF",function(r){return r.unf?r.unf.tpi+tr(" TPI, tap ")+r.unf.tapDrill:"-"}]],
  met:[[tr("Size"),"label"],[tr("Diameter (mm)"),function(r){return r.majorDiameterMm}],[tr("Coarse pitch"),function(r){return r.coarsePitch+" mm"}],[tr("Tap drill"),function(r){return r.tapDrillCoarse.toFixed(2)+" mm"}],[tr("Clearance (medium)"),function(r){return r.clearance.medium.toFixed(1)+" mm"}]],
  wood:[[tr("Size"),"label"],[tr("Diameter (in)"),function(r){return f4(r.majorDiameterIn)}],[tr("Pilot, softwood"),function(r){return r.pilotSoftwood}],[tr("Pilot, hardwood"),function(r){return r.pilotHardwood}],[tr("Clearance"),function(r){return r.clearance}]]};
 function draw(){load().then(function(){var rows=D[st.fam==="imp"?"imp":st.fam].slice(),q=st.q.trim().toLowerCase(),dk=st.fam==="met"?"majorDiameterMm":"majorDiameterIn";
  if(q){var p=parse(q,st.fam==="met"?"":st.fam==="wood"?"wood":"machine");rows=p.row?rows.filter(function(r){return r.label===p.row.label}):rows.filter(function(r){return r.label.toLowerCase().indexOf(q)>-1})}
  rows.sort(function(a,b){return st.sort==="d"?a[dk]-b[dk]:(parseFloat(a.label.replace(/[^\d.]/g,""))||0)-(parseFloat(b.label.replace(/[^\d.]/g,""))||0)||a.label.localeCompare(b.label)});
  var cols=C[st.fam];tb.innerHTML="<thead><tr>"+cols.map(function(c){return"<th>"+c[0]+"</th>"}).join("")+"</tr></thead><tbody>"+rows.map(function(r){return"<tr>"+cols.map(function(c){return'<td data-label="'+c[0]+'">'+esc(typeof c[1]==="string"?r[c[1]]:c[1](r))+"</td>"}).join("")+"</tr>"}).join("")+"</tbody>";
  $("#xCount").textContent=rows.length+tr(" rows");tabs.forEach(function(b){b.setAttribute("aria-selected",b.dataset.f===st.fam)});
  var n=new URLSearchParams();if(st.fam!=="imp")n.set("fam",st.fam);if(st.q)n.set("q",st.q);if(st.sort!=="d")n.set("sort",st.sort);history.replaceState(null,"",location.pathname+(n.toString()?"?"+n:""))})}
 tabs.forEach(function(b){b.addEventListener("click",function(){st.fam=b.dataset.f;draw()})});
 $("#xQ").addEventListener("input",function(e){st.q=e.target.value;draw()});$("#xSort").addEventListener("change",function(e){st.sort=e.target.value;draw()});
 if(location.search)draw()}
initLookup();initFinder();initMatch();initExplorer();
})();
