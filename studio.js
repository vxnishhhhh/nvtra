/* Small, dependency-free interactions; animations sleep offscreen. */
(() => {
  const systemMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const reduced = {get matches(){return systemMotion.matches || document.documentElement.dataset.motion==='reduce';},addEventListener:(...args)=>systemMotion.addEventListener(...args)};
  try {
    const saved = localStorage.getItem('nvtra-theme');
    if (['light','dark'].includes(saved) && saved !== document.documentElement.dataset.theme) toggleTheme();
  } catch {}
  const menu = document.querySelector('.menu-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  const closeMenu = () => { mobileNav.hidden = true; menu.setAttribute('aria-expanded','false'); };
  menu.addEventListener('click', () => { mobileNav.hidden = !mobileNav.hidden; menu.setAttribute('aria-expanded', String(!mobileNav.hidden)); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !mobileNav.hidden) { closeMenu(); menu.focus(); } });
  document.addEventListener('click', e => { if (!mobileNav.contains(e.target) && !menu.contains(e.target)) closeMenu(); });
  mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', e => { e.preventDefault(); go(a.hash.slice(1)); }));
  const restoreRoute = () => { const id = location.hash.slice(1).split('?')[0]; go(document.getElementById('page-'+id) ? id : 'home', false); };
  window.addEventListener('popstate', restoreRoute);
  window.addEventListener('hashchange', restoreRoute);
  if (location.hash) restoreRoute();
  let scrollFrame = 0;
  const progress = document.querySelector('.reading-progress');
  function updateProgress() { scrollFrame = 0; const height = document.documentElement.scrollHeight-innerHeight; progress.style.transform = `scaleX(${height > 0 ? scrollY/height : 0})`; }
  window.addEventListener('scroll', () => { if (!scrollFrame) scrollFrame = requestAnimationFrame(updateProgress); }, {passive:true});
  window.addEventListener('resize', updateProgress, {passive:true});
  document.addEventListener('nvtra:route', updateProgress);

  const preview = document.querySelector('.vision-preview');
  const slider = document.getElementById('energy');
  const directions = {
    editorial: {name:'Editorial',number:'01',kicker:'A little less ordinary.',line:'Make room',em:'possibility.',text:'Considered design. Lasting impressions.',color:'#ba8e55'},
    electric: {name:'Electric',number:'02',kicker:'Turn the ordinary up.',line:'Take up',em:'space.',text:'Bold ideas. An unmistakable presence.',color:'#c2fc67'},
    organic: {name:'Organic',number:'03',kicker:'Good things take root.',line:'Leave room',em:'growth.',text:'Natural rhythm. Meaningful connections.',color:'#577953'}
  };
  let direction='editorial', energy=50;
  function updateDirection() {
    const d=directions[direction];
    preview.dataset.direction=direction;
    preview.querySelector('.preview-kicker').textContent=d.kicker;
    const heading=preview.querySelector('h3');
    heading.replaceChildren(document.createTextNode(d.line),document.createElement('br'),document.createTextNode(direction==='electric'?'':'for '));
    const em=document.createElement('em'); em.textContent=d.em; heading.append(em);
    preview.querySelector('.preview-copy p').textContent=d.text;
    document.getElementById('direction-readout').textContent=d.number+' / '+d.name.toUpperCase();
    document.querySelectorAll('[data-direction][aria-pressed]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.direction===direction)));
    wake();
  }
  document.querySelectorAll('[data-direction][aria-pressed]').forEach(b=>b.addEventListener('click',()=>{direction=b.dataset.direction;updateDirection();}));
  slider.addEventListener('input',()=>{energy=Number(slider.value);document.getElementById('energy-value').textContent=energy+'%';wake();});
  document.querySelector('.lab-send').addEventListener('click',()=>{
    const form=document.getElementById('project-form');
    form.elements.subject.value='My NVTRA project — '+directions[direction].name+' direction';
    const note=`Design direction: ${directions[direction].name}. Visual energy: ${energy}%.`;
    form.elements.message.value=form.elements.message.value.replace(/^Design direction:.*\n\n/,'');
    form.elements.message.value=note+'\n\n'+form.elements.message.value;
    go('contact'); form.elements.name.focus({preventScroll:true});
  });
  // A field of fine contours responds to pointer position and creative energy.
  const canvas=document.getElementById('vision-field');
  const ctx=canvas.getContext('2d');
  let width=0,height=0,frame=0,visible=false,phase=0,last=0;
  const pointer={x:.72,y:.45};
  function draw(time=0) {
    frame=0;
    if (!ctx || !width || !height) return;
    const delta=last ? Math.min(time-last,50) : 0; last=time;
    if (!reduced.matches) phase+=delta*.00012*(.3+energy/100);
    ctx.clearRect(0,0,width,height);
    ctx.strokeStyle=directions[direction].color;
    ctx.lineWidth=.7;
    const count=22+Math.round(energy*.18),cx=width*pointer.x,cy=height*pointer.y;
    for(let ring=0;ring<count;ring++){
      ctx.beginPath();ctx.globalAlpha=.14+ring/count*.28;
      for(let step=0;step<=160;step++){
        const angle=step/160*Math.PI*2;
        const radius=35+ring*8;
        const wave=Math.sin(angle*3+phase+ring*.09)*(9+energy*.3)+Math.cos(angle*5-phase)*energy*.12;
        const x=cx+Math.cos(angle)*(radius+wave),y=cy+Math.sin(angle)*(radius+wave)*1.22;
        if(!step)ctx.moveTo(x,y);else ctx.lineTo(x,y);
      }
      ctx.closePath();ctx.stroke();
    }
    if(visible && !document.hidden && !reduced.matches)frame=requestAnimationFrame(draw);
  }
  function wake(){if(frame)cancelAnimationFrame(frame);frame=0;last=0;if(visible&&!document.hidden)frame=requestAnimationFrame(draw);}
  new ResizeObserver(entries=>{
    const rect=entries[0].contentRect;width=rect.width;height=rect.height;
    const dpr=Math.min(devicePixelRatio||1,1.5);
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
    if(ctx)ctx.setTransform(dpr,0,0,dpr,0,0);wake();
  }).observe(preview);
  new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;wake();},{threshold:0}).observe(preview);
  preview.addEventListener('pointermove',e=>{if(e.pointerType==='touch'||reduced.matches)return;const rect=preview.getBoundingClientRect();pointer.x=.6+(e.clientX-rect.left)/rect.width*.25;pointer.y=.25+(e.clientY-rect.top)/rect.height*.4;});
  preview.addEventListener('pointerleave',()=>{pointer.x=.72;pointer.y=.45;});
  document.addEventListener('visibilitychange',wake);
  reduced.addEventListener('change',wake);
  document.addEventListener('nvtra:preferences',wake);
})();
