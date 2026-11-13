(options={})=>{
  options=options||{};
  const root=document.documentElement,style=root.style;
  const previous=style.getPropertyValue('--reading-size'),priority=style.getPropertyPriority('--reading-size');
  const sizes=options.sizes||[18,24,28,48];
  const regulations=[...document.querySelectorAll('#frame .delegated_legislation')]
    .filter(reg=>!options.regulationIds||options.regulationIds.includes(reg.id));
  const issues=[],tables=[];let checked=0,navigationTargets=0;
  const inspect=(element,label)=>{
    checked++;
    if(element.scrollWidth>element.clientWidth+1){
      const bounds=element===root?{left:0,right:innerWidth}:element.getBoundingClientRect();
      const offenders=[...element.querySelectorAll('*')].filter(node=>{
        if(node.closest('.m-table-scroll')||!node.getClientRects().length)return false;
        const rect=node.getBoundingClientRect();
        return rect.width>0&&(rect.left<bounds.left-1||rect.right>bounds.right+1);
      }).slice(0,4).map(node=>({tag:node.tagName,id:node.id,class:node.className}));
      issues.push({label,client:element.clientWidth,scroll:element.scrollWidth,offenders});
    }
    for(const region of element.querySelectorAll('.m-table-scroll')){
      if(!region.getClientRects().length||region.clientWidth===0)continue;
      if(region.scrollWidth>region.clientWidth+1){
        const initial=region.scrollLeft;
        region.scrollLeft=region.scrollWidth;const right=region.scrollLeft;
        region.scrollLeft=-region.scrollWidth;const left=region.scrollLeft;
        region.scrollLeft=initial;
        if(Math.abs(right-left)<1)issues.push({label,table:'Overflowing table cannot be scrolled'});
        tables.push({label,client:region.clientWidth,scroll:region.scrollWidth,reachable:Math.abs(right-left)});
      }
    }
  };
  try{
    lawMobile.closeRegulation();
    for(const size of sizes){
      style.setProperty('--reading-size',size+'px');
      inspect(root,'law font '+size);
      for(const reg of regulations){
        lawMobile.openRegulation(reg);inspect(reg,reg.id+' font '+size);
        const targets=[reg.querySelector('.article[id]'),reg.querySelector('.appendix_part[id]')].filter((node,index,list)=>node&&list.indexOf(node)===index);
        for(const target of targets){
          lawMobile.goTo(target,false,false);navigationTargets++;
          const actual=target.getBoundingClientRect().top,back=document.getElementById('mobile-regulation-back').getBoundingClientRect().bottom;
          if(actual<back+10)issues.push({label:reg.id+' font '+size,target:target.id,top:actual,backBottom:back,reason:'Linked target is obscured by the return control'});
        }
      }
      lawMobile.closeRegulation();
    }
  }finally{
    lawMobile.closeRegulation();
    if(previous)style.setProperty('--reading-size',previous,priority);else style.removeProperty('--reading-size');
  }
  return {viewport:innerWidth,sizes,regulations:regulations.length,checked,navigationTargets,scrollableTables:tables.length,tables,issues};
}
