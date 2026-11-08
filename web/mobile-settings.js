/* Local portable settings files, shared validation and an explicit restore preview. */
(()=>{'use strict';
const options=()=>({hasTarget:id=>!!document.getElementById(id),baseTopics:new Set(['base:general',...Array.from(document.querySelectorAll('#navigator .nav_list_title[id]'),e=>'base:'+e.id)])});
function prepareImport(raw){try{const settings=LawCore.validateBackup(raw,options());return {ok:true,preview:LawCore.preview(settings)};}catch(e){return {ok:false,error:e.message};}}
function applyImport(raw){try{LawCore.applyBackup(localStorage,raw,options());return {ok:true};}catch(e){return {ok:false,error:e.message||'השחזור נכשל'};}}
function exportJSON(){return LawCore.exportBackup(localStorage,options());}
function exportFile(){
 if(window.NativeLaw?.exportSettings){window.NativeLaw.exportSettings();return;}
 try{const blob=new Blob([exportJSON()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='consumer-law-settings.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){showError(e.message);}
}
function showError(message){const panel=window.lawMobile.showMore();const note=document.getElementById('mobile-toast');note.textContent=message;note.hidden=false;setTimeout(()=>note.hidden=true,5000);}
function previewFile(raw){
 const result=prepareImport(raw),api=window.lawSettings;
 const dialog=document.getElementById('mobile-sheet'),body=document.getElementById('mobile-sheet-body');
 document.getElementById('mobile-sheet-title').textContent=result.ok?'שחזור הגדרות':'לא ניתן לשחזר';body.replaceChildren();
 const text=document.createElement('p');text.textContent=result.ok?result.preview:result.error;body.append(text);
 if(!dialog.open)dialog.showModal();
 if(result.ok){const button=document.createElement('button');button.className='m-action';button.id='mobile-confirm-restore';button.textContent='אישור החלפת ההגדרות';button.onclick=()=>{const applied=api.applyImport(raw);if(applied.ok)location.reload();else{text.textContent=applied.error;button.disabled=true;}};body.append(button);button.focus();}
}
function importFile(){
 if(window.NativeLaw?.importSettings){window.NativeLaw.importSettings();return;}
 const input=document.createElement('input');input.type='file';input.accept='.json,application/json';
 input.onchange=async()=>{const file=input.files[0];if(!file)return;if(file.size>LawCore.MAX_BACKUP){showError('קובץ הגיבוי גדול מדי');return;}try{previewFile(await file.text());}catch{showError('קריאת הגיבוי נכשלה');}};input.click();
}
window.lawSettings={prepareImport,applyImport,exportJSON,exportFile,importFile,previewFile};
})();
