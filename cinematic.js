/* Native scroll scenes and a small indexed WebGL sculpture. No animation framework or audio. */
(() => {
  const $=(q,root=document)=>root.querySelector(q),$$=(q,root=document)=>[...root.querySelectorAll(q)];
  const systemMotion=matchMedia('(prefers-reduced-motion: reduce)'),mobile=matchMedia('(max-width:800px)');
  const reduced=()=>systemMotion.matches||document.documentElement.dataset.motion==='reduce';
  const calm=()=>reduced()||mobile.matches;
  const clamp=(n,a=0,b=1)=>Math.min(b,Math.max(a,n));
  const sceneProgress=el=>clamp(-el.getBoundingClientRect().top/Math.max(1,el.offsetHeight-innerHeight));
  const process=[
    ['Discover','Start with the right questions.','Your audience, your ambition, your constraints. We define what the website needs to do before deciding how it should look.','A SHARED BRIEF'],
    ['Concept','Give the idea a direction.','Explore references, materials and visual language. A clear creative direction keeps every later decision connected.','A CREATIVE DIRECTION'],
    ['Design','Make every detail belong.','Typography, structure and interactions come together. Review the design in your portal before development moves forward.','A REVIEWABLE DESIGN'],
    ['Develop','Bring the intention to life.','Translate the design into a responsive, accessible experience. Test the real interactions, not just how they look.','A WORKING EXPERIENCE'],
    ['Launch','Ready for the next chapter.','Review, approve and prepare your release. Agree the handover and ongoing support before the site meets the world.','A CONSIDERED HANDOVER']
  ];
  let activeStage=0,activeExhibit=0,scrollFrame=0;
  const hero=$('.hero-sequence'),gallery=$('.exhibition-sequence'),processScene=$('.process-scene'),track=$('.exhibition-track');
  function selectStage(index){
    if(index===activeStage)return;activeStage=index;const s=process[index];
    $('#process-index').textContent=`0${index+1} / ${s[0].toUpperCase()}`;$('#process-stage-title').textContent=s[1];$('#process-stage-copy').textContent=s[2];$('#process-deliverable').textContent='OUTPUT / '+s[3];
    $$('[data-process-index]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.processIndex)===index)));$('.process-line span').style.width=(index+1)/5*100+'%';
    if(!reduced())$('.process-scene-detail').animate([{opacity:.4,transform:'translateY(10px)'},{opacity:1,transform:'translateY(0)'}],{duration:400,easing:'cubic-bezier(.16,1,.3,1)'});
    sculptures.get($('#process-canvas'))?.wake();
  }
  function selectExhibit(index){if(index===activeExhibit)return;activeExhibit=index;$('.exhibition-counter').textContent=`0${index+1} / 03`;$$('[data-exhibit-index]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.exhibitIndex)===index)));}
  function updateScroll(){
    scrollFrame=0;if(!$('#page-home').classList.contains('on'))return;
    if(!calm()){
      const hp=sceneProgress(hero);$('.hero-content').style.transform=`translateY(${-hp*70}px) scale(${1-hp*.06})`;$('.hero-content').style.opacity=String(1-hp*.75);$('.sculpture-stage').style.transform=`translateX(${-hp*9}%) scale(${1+hp*.25})`;
      const gp=sceneProgress(gallery),distance=Math.max(0,track.scrollWidth-gallery.clientWidth*.9);
      track.style.transform=`translate3d(${-gp*distance}px,0,0)`;
      $$('.exhibit-frame').forEach((f,i)=>{const focus=clamp(1-Math.abs(gp*2-i)*.4,.55,1);f.style.transform=`rotateY(${(gp*2-i)*9}deg) scale(${.86+focus*.14})`;f.style.opacity=String(.5+focus*.5);});selectExhibit(Math.round(gp*2));
      selectStage(Math.min(4,Math.floor(sceneProgress(processScene)*5)));
    }
    sculptures.forEach(s=>s.scrollWake());
  }
  const schedule=()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(updateScroll);};
  window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule,{passive:true});document.addEventListener('nvtra:route',schedule);
  $$('[data-exhibit-index]').forEach(b=>b.addEventListener('click',()=>{const index=Number(b.dataset.exhibitIndex);if(calm()){const card=$$('.exhibit-frame')[index];track.scrollTo({left:card.offsetLeft-track.offsetLeft,behavior:reduced()?'instant':'smooth'});selectExhibit(index);}else{const top=scrollY+gallery.getBoundingClientRect().top;window.scrollTo({top:top+(gallery.offsetHeight-innerHeight)*index/2,behavior:'smooth'});}}));
  track.addEventListener('scroll',()=>{if(calm()){const first=$$('.exhibit-frame')[0];selectExhibit(clamp(Math.round(track.scrollLeft/(first.offsetWidth+24)),0,2));}},{passive:true});
  $$('[data-process-index]').forEach(b=>b.addEventListener('click',()=>{const index=Number(b.dataset.processIndex);if(calm())selectStage(index);else{const top=scrollY+processScene.getBoundingClientRect().top;window.scrollTo({top:top+(processScene.offsetHeight-innerHeight)*(index+.25)/5,behavior:'smooth'});}}));

  // Parametric torus-knot: vertices + normals, indexed triangles, depth and lit materials.
  const sculptures=new Map();
  function sculpture(canvas){
    const gl=canvas.getContext('webgl',{alpha:true,antialias:!mobile.matches,powerPreference:'low-power',preserveDrawingBuffer:false});
    if(!gl){canvas.dataset.renderer='fallback';return {wake(){},scrollWake(){}};}
    let frame=0,visible=false,lost=false,width=0,height=0,last=0,phase=0,ready=false;
    let program,indexCount,uniforms;
    const pointer={x:0,y:0};
    const vert=`attribute vec3 a_position;attribute vec3 a_normal;uniform mat4 u_projection;uniform vec2 u_angle;uniform float u_scale;uniform float u_distance;varying vec3 v_normal;varying vec3 v_view;void main(){float x=u_angle.x,y=u_angle.y;mat3 rx=mat3(1.,0.,0.,0.,cos(x),sin(x),0.,-sin(x),cos(x));mat3 ry=mat3(cos(y),0.,-sin(y),0.,1.,0.,sin(y),0.,cos(y));vec3 p=ry*rx*a_position*u_scale;p.z-=u_distance;v_normal=ry*rx*a_normal;v_view=normalize(-p);gl_Position=u_projection*vec4(p,1.);}`;
    const frag=`precision mediump float;varying vec3 v_normal;varying vec3 v_view;uniform float u_light;uniform float u_stage;void main(){vec3 n=normalize(v_normal),v=normalize(v_view);vec3 l=normalize(vec3(-.6,.9,1.)),l2=normalize(vec3(.8,-.2,.7));float diff=max(dot(n,l),0.);float rim=pow(1.-max(dot(n,v),0.),2.4);float spec=pow(max(dot(n,normalize(l+v)),0.),52.);float spec2=pow(max(dot(n,normalize(l2+v)),0.),18.);vec3 silver=vec3(.63,.65,.60);vec3 gold=vec3(.65,.53,.35);vec3 sage=vec3(.31,.48,.42);vec3 lavender=vec3(.49,.45,.64);vec3 tint=mix(sage,lavender,.5+.5*sin(n.x*2.+u_stage*.6));vec3 base=mix(gold,silver,.55+.2*n.y);base=mix(base,tint,.22+rim*.3);float band=smoothstep(.35,.95,sin(n.y*5.+n.x*2.5));vec3 col=base*(.3+diff*.7)+vec3(.94,.89,.74)*spec*.85+vec3(.64,.76,.75)*spec2*.26+base*band*.18+vec3(.58,.65,.56)*rim*.26;col*=mix(1.0,.82,u_light);gl_FragColor=vec4(col,1.);}`;
    const normalise=v=>{const l=Math.hypot(...v)||1;return v.map(x=>x/l);};
    const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
    const point=t=>{const r=1.05+.34*Math.cos(3*t);return [r*Math.cos(2*t),r*Math.sin(2*t),.43*Math.sin(3*t)];};
    function initialise(){
      const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Shader unavailable');return s;};
      try{
        program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,vert));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,frag));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Shader unavailable');gl.useProgram(program);
        const segments=mobile.matches?96:180,sides=mobile.matches?10:18,positions=[],normals=[],indices=[];
        for(let i=0;i<=segments;i++){
          const t=i/segments*Math.PI*2,p=point(t),next=point(t+.001),tangent=normalise(next.map((x,j)=>x-p[j]));const n=normalise(cross(tangent,[0,0,1])),binormal=normalise(cross(tangent,n));
          for(let j=0;j<=sides;j++){const a=j/sides*Math.PI*2,normal=n.map((x,k)=>x*Math.cos(a)+binormal[k]*Math.sin(a));positions.push(...p.map((x,k)=>x+normal[k]*.24));normals.push(...normal);if(i<segments&&j<sides){const k=i*(sides+1)+j;indices.push(k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2);}}
        }
        for(const [name,values] of [['a_position',positions],['a_normal',normals]]){const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.STATIC_DRAW);const loc=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0);}
        const buffer=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,buffer);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indices),gl.STATIC_DRAW);indexCount=indices.length;
        uniforms=Object.fromEntries(['projection','angle','scale','distance','light','stage'].map(k=>[k,gl.getUniformLocation(program,'u_'+k)]));gl.enable(gl.DEPTH_TEST);gl.clearColor(0,0,0,0);ready=true;canvas.parentElement.classList.add('has-webgl');canvas.dataset.renderer='webgl';resize();
      }catch{ready=false;canvas.dataset.renderer='fallback';canvas.parentElement.classList.remove('has-webgl');}
    }
    function resize(){if(!ready||lost)return;const rect=canvas.getBoundingClientRect();width=rect.width;height=rect.height;if(!width||!height)return;const dpr=Math.min(devicePixelRatio||1,mobile.matches?1.25:1.5);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);gl.viewport(0,0,canvas.width,canvas.height);const f=1/Math.tan(.65/2),aspect=width/height,near=.1,far=100;gl.uniformMatrix4fv(uniforms.projection,false,new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]));wake();}
    function draw(time){frame=0;if(!ready||lost||!visible||document.hidden||!width)return;
      const delta=last?Math.min(time-last,60):0;last=time;if(!calm())phase+=delta*.000065;
      const isProcess=canvas.id==='process-canvas',stage=isProcess?activeStage:0,progress=isProcess?stage/4:sceneProgress(hero);
      gl.useProgram(program);gl.uniform2f(uniforms.angle,.55+pointer.y*.15+progress*.4,.25+phase+pointer.x*.18+stage*.25);gl.uniform1f(uniforms.scale,isProcess?.92:1);gl.uniform1f(uniforms.distance,mobile.matches?5.8:5.4);gl.uniform1f(uniforms.light,isProcess||document.documentElement.dataset.theme==='light'?1:0);gl.uniform1f(uniforms.stage,stage);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,indexCount,gl.UNSIGNED_SHORT,0);
      if(!calm())frame=requestAnimationFrame(draw);
    }
    function wake(){if(frame)cancelAnimationFrame(frame);frame=0;last=0;if(visible&&!document.hidden&&!lost&&ready)frame=requestAnimationFrame(draw);}
    const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible&&!ready&&!lost)initialise();wake();},{threshold:.05});observer.observe(canvas);
    new ResizeObserver(resize).observe(canvas);
    canvas.parentElement.parentElement.addEventListener('pointermove',e=>{if(e.pointerType==='touch'||calm())return;const r=canvas.getBoundingClientRect();pointer.x=clamp((e.clientX-r.left)/r.width*2-1,-1,1);pointer.y=clamp((e.clientY-r.top)/r.height*2-1,-1,1);},{passive:true});
    canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;wake();canvas.parentElement.classList.remove('has-webgl');canvas.dataset.renderer='fallback';});
    canvas.addEventListener('webglcontextrestored',()=>{lost=false;initialise();wake();});
    document.addEventListener('visibilitychange',wake);document.addEventListener('nvtra:preferences',wake);systemMotion.addEventListener('change',wake);mobile.addEventListener('change',()=>{resize();wake();});
    new MutationObserver(wake).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
    return {wake,scrollWake(){if(calm())wake();}};
  }
  $$('.sculpture-canvas').forEach(canvas=>sculptures.set(canvas,sculpture(canvas)));
  const resetScenes=()=>{if(calm()){$('.hero-content').style.transform='none';$('.hero-content').style.opacity='1';$('.sculpture-stage').style.transform='none';track.style.transform='none';}schedule();};
  document.addEventListener('nvtra:preferences',resetScenes);systemMotion.addEventListener('change',resetScenes);mobile.addEventListener('change',resetScenes);schedule();

  const studies={
    corner:{title:'Corner',category:'Hospitality',approach:'A familiar ritual, thoughtfully reframed.',copy:'A fictional neighbourhood café, explored through warm colour, editorial typography and a simple route from discovery to a visit. This is a studio design study, not a client commission.',details:'Soft sage surfaces, a tactile coffee composition and generous spacing give the everyday a little ceremony.',tech:'Semantic HTML · CSS materials · Responsive composition'},
    forma:{title:'Forma',category:'Architecture',approach:'Let the space do the talking.',copy:'A fictional architecture practice used to explore light, negative space and a restrained project-led composition. No client or business results are implied.',details:'Architectural frames and quiet typography establish hierarchy. The interface makes room for the work rather than competing with it.',tech:'CSS perspective · Editorial type · Accessible navigation'},
    orbit:{title:'Orbit',category:'Digital product',approach:'Make the unfamiliar feel inviting.',copy:'A conceptual digital product identity exploring dimensional objects, bold typography and clear interactions. Built as an interactive studio demonstration.',details:'Cool lilac, intersecting forms and precise labels create an experimental visual language with a readable interface beneath it.',tech:'Geometric CSS · Native transitions · Responsive controls'}
  };
  const regions={navigation:['Navigation','A predictable route through the experience. Clear labels, visible focus and a compact mobile menu help visitors stay oriented.'],hero:['Hero composition','A useful headline states the purpose. Type, space and the dominant visual guide attention toward one clear next step.'],cards:['Content cards','A flexible content system keeps related information together. Cards adapt to narrow screens and never rely on hover alone.'],motion:['Motion','Transitions explain changes of state. Reduced-motion preferences remove nonessential movement while keeping every action available.'],forms:['Interactive forms','Native labels and validation are backed by server-side checks. Success, storage and delivery are reported as separate states.'],footer:['Footer','Contact details and secondary routes remain easy to find. It closes the story without hiding essential navigation.']};
  let studyTrigger=null,transitionBusy=false;
  function fillStudy(id){const s=studies[id],source=$(`.exhibit-frame[data-study="${id}"] .exhibit-art`);const visual=source.cloneNode(true);visual.classList.add('study-shared-art');visual.style.viewTransitionName='none';
    $('#study-content').innerHTML=`<header class="study-hero"><span class="cinema-kicker">STUDIO STUDY / ${s.category.toUpperCase()} / INTERACTIVE DEMONSTRATION</span><h2>${s.title}<em> / ${s.category}</em></h2><p>${s.copy}</p></header><div class="study-layout"><div class="study-visual-slot"></div><div class="study-facts"><h3>${s.approach}</h3><p>${s.details}</p><dl><dt>Type</dt><dd>Independent studio exploration</dd><dt>Built with</dt><dd>${s.tech}</dd><dt>Outcomes</dt><dd>No client outcome or performance claim. This study demonstrates interface decisions.</dd></dl><button class="text-button" id="study-enquire">Explore a direction like this ↗</button></div></div><section class="website-explorer"><span class="cinema-kicker">LOOK UNDER THE SURFACE</span><h3>A website, taken apart.</h3><p class="microcopy">Select a region to explore its purpose. Every region works with a keyboard or tap.</p><div class="explorer-layout"><div class="explorer-map" role="group" aria-label="Website regions">${Object.entries(regions).map(([id,v],i)=>`<button data-region="${id}" aria-pressed="${i===0}">${v[0]} <span aria-hidden="true">↗</span></button>`).join('')}</div><div class="explorer-description" aria-live="polite"><span class="cinema-kicker">01 / NAVIGATION</span><h4>${regions.navigation[0]}</h4><p>${regions.navigation[1]}</p></div></div></section>`;
    $('.study-visual-slot').append(visual);$$('[data-region]').forEach(b=>b.addEventListener('click',()=>{$$('[data-region]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));const r=regions[b.dataset.region],number=Object.keys(regions).indexOf(b.dataset.region)+1;$('.explorer-description').innerHTML=`<span class="cinema-kicker">0${number} / ${r[0].toUpperCase()}</span><h4>${r[0]}</h4><p>${r[1]}</p>`;}));
    $('#study-enquire').addEventListener('click',()=>{$('#study-dialog').close();go('lab');});return visual;
  }
  async function openStudy(id,trigger){if(transitionBusy||!studies[id])return;transitionBusy=true;studyTrigger=trigger;const source=$('.exhibit-art',trigger);const open=()=>{const art=fillStudy(id);if(source)source.style.viewTransitionName='none';$('#study-dialog').showModal();$('#study-dialog').scrollTop=0;art.style.viewTransitionName='study-visual';};
    try{if(document.startViewTransition&&!reduced()&&source){source.style.viewTransitionName='study-visual';await document.startViewTransition(open).finished;}else open();}finally{if(source)source.style.viewTransitionName='none';$('.study-shared-art')?.style.setProperty('view-transition-name','none');transitionBusy=false;}
  }
  $$('[data-study]').forEach(b=>b.addEventListener('click',()=>openStudy(b.dataset.study,b)));
  $('#study-dialog').addEventListener('close',()=>{studyTrigger?.focus({preventScroll:true});});
  // Restrained feedback, with no pointer-only interactions or continuous cursor loop.
  $$('.hero .btn-glass-solid').forEach(button=>{button.addEventListener('pointermove',e=>{if(calm()||e.pointerType==='touch')return;const r=button.getBoundingClientRect();button.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.06}px,${(e.clientY-r.top-r.height/2)*.08}px)`;});button.addEventListener('pointerleave',()=>button.style.transform='');});
  let amountObserver;
  const observePrice=()=>{amountObserver?.disconnect();const live=$('#estimate-live');if(!live)return;amountObserver=new MutationObserver(()=>{const amount=$('.estimate-amount',live);if(amount&&!reduced())amount.classList.add('price-change');});amountObserver.observe(live,{childList:true});};
  document.addEventListener('nvtra:estimator-ready',observePrice);observePrice();
})();
