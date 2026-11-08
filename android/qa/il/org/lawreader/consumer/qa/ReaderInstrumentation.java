package il.org.lawreader.consumer.qa;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.view.accessibility.AccessibilityNodeInfo;
import android.os.ParcelFileDescriptor;
import java.io.ByteArrayOutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

/** Runs inside the actual installed app, against its actual bundled legal DOM. */
public final class ReaderInstrumentation extends Instrumentation {
    private Activity activity;
    private WebView web;
    private boolean expectDate,seed,verifySeed,verifyUpgrade;
    private String expectedFont;
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);expectedFont=arguments==null?null:arguments.getString("expectedFont");expectDate=arguments!=null&&"true".equals(arguments.getString("expectDate"));seed=arguments!=null&&"true".equals(arguments.getString("seed"));verifySeed=arguments!=null&&"true".equals(arguments.getString("verifySeed"));verifyUpgrade=arguments!=null&&"true".equals(arguments.getString("verifyUpgrade"));start(); }
    private WebView find(View view) {
        if(view instanceof WebView)return (WebView)view;
        if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++){WebView found=find(g.getChildAt(i));if(found!=null)return found;}}
        return null;
    }
    private String js(final String source) throws Exception {
        final String[] value={null};CountDownLatch done=new CountDownLatch(1);
        runOnMainSync(()->web.evaluateJavascript(source,result->{value[0]=result;done.countDown();}));
        if(!done.await(30,TimeUnit.SECONDS))throw new Exception("JavaScript callback timeout: "+source.substring(0,Math.min(source.length(),180)));
        return value[0];
    }
    private void check(boolean value,String label) throws Exception {if(!value)throw new Exception(label);}
    private void ready() throws Exception {
        for(int i=0;i<240;i++) {if("true".equals(js((seed||verifySeed)?"!!window.lawMobile":"document.documentElement.dataset.lawReady === 'true'")))return;Thread.sleep(250);}
        throw new Exception("No application readiness; WebView="+WebView.getCurrentWebViewPackage());
    }
    private String shell(String command) throws Exception {
        try(ParcelFileDescriptor descriptor=getUiAutomation().executeShellCommand(command);
            ParcelFileDescriptor.AutoCloseInputStream input=new ParcelFileDescriptor.AutoCloseInputStream(descriptor);
            ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int n,total=0;
            while((n=input.read(buffer))!=-1){total+=n;if(total>1000000)throw new Exception("QA shell output limit");output.write(buffer,0,n);}
            return new String(output.toByteArray(),"UTF-8");
        }
    }
    private AccessibilityNodeInfo findText(AccessibilityNodeInfo node,String text) {
        if(node==null)return null;
        if((node.getText()!=null&&text.equalsIgnoreCase(node.getText().toString())) || (node.getContentDescription()!=null&&text.equalsIgnoreCase(node.getContentDescription().toString())))return node;
        for(int i=0;i<node.getChildCount();i++){AccessibilityNodeInfo found=findText(node.getChild(i),text);if(found!=null)return found;}
        return null;
    }
    private void clickSystemText(String text) throws Exception {
        try{getUiAutomation().waitForIdle(700,8000);}catch(java.util.concurrent.TimeoutException busy){}
        for(int attempt=0;attempt<100;attempt++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            AccessibilityNodeInfo node=findText(root,text);
            for(int depth=0;node!=null&&depth<6;depth++,node=node.getParent())
                if(node.isClickable()&&node.isEnabled()&&node.performAction(AccessibilityNodeInfo.ACTION_CLICK))return;
            Thread.sleep(100);
        }
        throw new Exception("Native control not found: "+text);
    }
    private void testNativeSettingsFiles() throws Exception {
        shell("rm -f /sdcard/Download/consumer-law-settings.json");
        // A portable legacy-size backup must not travel inside Activity saved
        // state (Binder has a process-wide, approximately 1 MB transaction limit).
        check("true".equals(js("(()=>{const data={schema:1,userTopics:[{id:'u:large',title:'large',parent:null,index:1000}],links:[],titles:{},hidden:{},ranks:{}};for(let i=0;i<2000;i++)data.links.push({id:'u:large-'+i,topic:'u:large',target:'article_14',title:'א'.repeat(90)});localStorage.setItem('law-reader-topics-v1',JSON.stringify(data));return lawSettings.exportJSON().length>300000})()")),"Large valid portable backup fixture");
        js("NativeLaw.exportSettings()");
        Thread.sleep(800);
        final Bundle state=new Bundle();
        runOnMainSync(()->callActivityOnSaveInstanceState(activity,state));
        android.os.Parcel parcel=android.os.Parcel.obtain();
        try{state.writeToParcel(parcel,0);check(parcel.dataSize()<100000,"Large export does not inflate Activity saved state");}
        finally{parcel.recycle();}
        clickSystemText("Save");
        JSONObject exported=null;
        for(int i=0;i<60;i++){
            try{exported=new JSONObject(shell("cat /sdcard/Download/consumer-law-settings.json"));break;}
            catch(Exception pending){Thread.sleep(100);}
        }
        check(exported!=null&&"consumer-law-reader-settings".equals(exported.optString("format")),"Actual SAF export file");
        check("24".equals(exported.getJSONObject("settings").getString("law-reader-font")),"SAF export includes real preferences");
        js("localStorage.setItem('law-reader-font','20');NativeLaw.importSettings()");
        clickSystemText("consumer-law-settings.json");
        clickSystemText("החלפת ההגדרות");
        Thread.sleep(500);ready();
        check("\"24\"".equals(js("localStorage.getItem('law-reader-font')")),"Actual SAF confirmed import");
    }
    private void testAttachmentAndClipboard() throws Exception {
        final String[] result={null};final CountDownLatch received=new CountDownLatch(1);
        android.content.BroadcastReceiver receiver=new android.content.BroadcastReceiver(){
            @Override public void onReceive(android.content.Context context,Intent intent){result[0]=intent.getStringExtra("sha256");received.countDown();}
        };
        android.content.IntentFilter filter=new android.content.IntentFilter("il.org.lawreader.consumer.QA_ATTACHMENT");
        if(android.os.Build.VERSION.SDK_INT>=33)getTargetContext().registerReceiver(receiver,filter,android.content.Context.RECEIVER_EXPORTED);
        else getTargetContext().registerReceiver(receiver,filter);
        try{
            String name=null;for(String file:getTargetContext().getAssets().list("www"))if(file.endsWith(".doc")){name=file;break;}
            check(name!=null,"Bundled Word attachment exists");
            java.security.MessageDigest digest=java.security.MessageDigest.getInstance("SHA-256");
            try(java.io.InputStream input=getTargetContext().getAssets().open("www/"+name)){byte[] bytes=new byte[16384];int n;while((n=input.read(bytes))!=-1)digest.update(bytes,0,n);}
            StringBuilder expected=new StringBuilder();for(byte b:digest.digest())expected.append(String.format("%02x",b&255));
            js("NativeLaw.openAttachment("+JSONObject.quote(name)+")");
            check(received.await(15,TimeUnit.SECONDS),"Cross-UID attachment intent received");
            check(expected.toString().equals(result[0]),"Attachment bytes and read-only URI permission");
            Thread.sleep(300);js("NativeLaw.copy('QA clipboard fixture')");Thread.sleep(150);
            final String[] clipboard={null};runOnMainSync(()->{
                android.content.ClipboardManager manager=(android.content.ClipboardManager)getTargetContext().getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                if(manager.hasPrimaryClip())clipboard[0]=manager.getPrimaryClip().getItemAt(0).getText().toString();
            });
            check("QA clipboard fixture".equals(clipboard[0]),"Native clipboard bridge");
            android.os.Parcel parcel=android.os.Parcel.obtain();
            try{
                android.content.ClipData.newPlainText("QA",new String(new char[600000]).replace('\0','א')).writeToParcel(parcel,0);
                check(parcel.dataSize()>1048576,"Previous clipboard bound could exceed the actual Binder transaction limit");
            }finally{parcel.recycle();}
            js("NativeLaw.copy('א'.repeat(450001))");Thread.sleep(300);
            check("true".equals(js("document.getElementById('mobile-toast').textContent.includes('לא הושלמה')")),"Oversized native clipboard rejected honestly without crashing");
            runOnMainSync(()->{
                android.content.ClipboardManager manager=(android.content.ClipboardManager)getTargetContext().getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                clipboard[0]=manager.hasPrimaryClip()?manager.getPrimaryClip().getItemAt(0).getText().toString():null;
            });
            check("QA clipboard fixture".equals(clipboard[0]),"Rejected clipboard data cannot replace the previous clip");
            check("true".equals(js("(()=>{const e=document.createElement('div');e.id='qa-copy';e.style.cssText='position:fixed;left:-10000px;top:0;width:300px;height:1px;overflow:hidden;contain:strict;white-space:pre';e.textContent=('א'.repeat(999)+'\\n').repeat(600);document.body.append(e);return true})()")),"Large representative multiline clipboard fixture");
            check("true".equals(js("(()=>{getSelection().selectAllChildren(document.getElementById('qa-copy'));window.__qaCopiedText=getSelection().toString();return __qaCopiedText.length>450000})()")),"Actual large DOM selection");
            check("true".equals(js("(()=>{copy_selected();return document.querySelector('#mobile-sheet textarea')?.value===window.__qaCopiedText})()")),"Oversized selection retains the entire text in an accessible fallback");
            js("lawMobileBack();document.getElementById('qa-copy').remove();getSelection().removeAllRanges();delete window.__qaCopiedText");
        }finally{getTargetContext().unregisterReceiver(receiver);}
    }
    private void testNativeShare() throws Exception {
        final String[] text={null};final CountDownLatch received=new CountDownLatch(1);
        android.content.BroadcastReceiver receiver=new android.content.BroadcastReceiver(){
            @Override public void onReceive(android.content.Context context,Intent intent){text[0]=intent.getStringExtra("text");received.countDown();}
        };
        android.content.IntentFilter filter=new android.content.IntentFilter("il.org.lawreader.consumer.QA_SHARE");
        if(android.os.Build.VERSION.SDK_INT>=33)getTargetContext().registerReceiver(receiver,filter,android.content.Context.RECEIVER_EXPORTED);
        else getTargetContext().registerReceiver(receiver,filter);
        try{
            js("lawMobile.shareLink('article_14')");
            for(int attempt=0;attempt<3&&received.getCount()>0;attempt++){
                clickSystemText("Reader QA link receiver");
                if(received.await(3,TimeUnit.SECONDS))break;
            }
            check(received.await(15,TimeUnit.SECONDS),"Real sharesheet destination received the intent");
            check("https://sargon17-green.github.io/consumer-law-reader/reader/#article_14".equals(text[0]),"Native share retains the exact public section URL");
            Thread.sleep(300);
        }finally{getTargetContext().unregisterReceiver(receiver);}
    }
    private void testNativePrintPresentation() throws Exception {
        js("NativeLaw.printDocument()");
        boolean opened=false;
        for(int i=0;i<80;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&"com.android.printspooler".contentEquals(root.getPackageName())){opened=true;break;}
            Thread.sleep(250);
        }
        check(opened,"Real Android system print interface opens");
        shell("input keyevent KEYCODE_BACK");
        for(int i=0;i<80;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&"il.org.lawreader.consumer".contentEquals(root.getPackageName()))return;
            Thread.sleep(250);
        }
        throw new Exception("Reader resumes after cancelling system print");
    }
    @Override public void onStart() {
        Bundle report=new Bundle();
        final long launchStart=android.os.SystemClock.elapsedRealtime();
        final long cpuStart=android.os.Process.getElapsedCpuTime();
        try{
            Intent intent=getTargetContext().getPackageManager().getLaunchIntentForPackage("il.org.lawreader.consumer");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
            activity=startActivitySync(intent);
            runOnMainSync(()->web=find(activity.findViewById(android.R.id.content)));
            check(web!=null,"No native WebView");
            report.putString("webview",WebView.getCurrentWebViewPackage().versionName);
            ready();
            report.putLong("activityToReadyMilliseconds",android.os.SystemClock.elapsedRealtime()-launchStart);
            android.os.Debug.MemoryInfo initialMemory=new android.os.Debug.MemoryInfo();
            android.os.Debug.getMemoryInfo(initialMemory);
            report.putInt("mainProcessPssKBAtReady",initialMemory.getTotalPss());
            if(seed){
                js("localStorage.setItem('law-reader-font','23');localStorage.setItem('law-reader-align','right');localStorage.setItem('law-reader-topics-v1',JSON.stringify({schema:1,userTopics:[{id:'u:upgrade',title:'נושא בדיקת שדרוג',parent:null,index:1000}],links:[{id:'u:upgrade-link',topic:'u:upgrade',target:'article_14',title:'סעיף 14'}],titles:{},hidden:{},ranks:{}}))");
                check("\"23\"".equals(js("localStorage.getItem('law-reader-font')")),"Seed readback");
                runOnMainSync(()->activity.moveTaskToBack(true));Thread.sleep(6000);
                report.putString("QA_STATUS","PASS");report.putString("coverage","Seeded public-beta COPY using disposable QA identity");finish(Activity.RESULT_OK,report);return;
            }
            if(verifySeed){
                report.putString("seedFont",js("localStorage.getItem('law-reader-font')"));
                check("\"23\"".equals(js("localStorage.getItem('law-reader-font')")),"Seed persisted after original app process restart");
                report.putString("QA_STATUS","PASS");finish(Activity.RESULT_OK,report);return;
            }
            if(expectedFont!=null){
                report.putString("reopenedFont",js("localStorage.getItem('law-reader-font')"));
                check(expectedFont.equals(new org.json.JSONTokener(js("localStorage.getItem('law-reader-font')")).nextValue()),"Preferences persist after actual process restart");
            }
            if(verifyUpgrade){
                report.putString("upgradedFont",js("localStorage.getItem('law-reader-font')"));
                report.putString("upgradedOrigin",js("location.origin"));
                check("\"23\"".equals(js("localStorage.getItem('law-reader-font')")),"Font preserved across APK upgrade");
                check("1".equals(js("LawTopics.inspect().userTopics")),"Personal topics preserved across APK upgrade");
            }
            if(expectDate){
                boolean date=false;
                for(int i=0;i<220;i++){if(js("document.getElementById('pastafari_current_date_text').textContent").contains("התאריך הפסטפרי היום:")){date=true;break;}Thread.sleep(250);}
                check(date,"Fresh upstream Seer snapshot must render through actual native WebView/CORS policy");
                report.putString("date",js("document.getElementById('pastafari_current_date_text').textContent"));
            }
            js("lawMobile.showToc()");sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);Thread.sleep(350);
            check("false".equals(js("document.getElementById('mobile-sheet').open")),"Actual Android Back closes the sheet");
            report.putString("indexMilliseconds",js("(()=>{const t=performance.now();lawMobile.buildSearch();return performance.now()-t})()"));
            String test="(function(){const check=(v,m)=>{if(!v)throw Error(m)};"+
                "check(lawMobile.buildSearch().length>500,'full offline index');"+
                "check(LawCore.snippet('אָב שָׁלוֹם סוף','שלום').mark==='שָׁלוֹם','UTF16 mapping');"+
                "localStorage.setItem('outside-backup','keep');localStorage.setItem('law-reader-font','24');localStorage.removeItem('law-reader-align');"+
                "const raw=lawSettings.exportJSON();localStorage.setItem('law-reader-align','right');"+
                "check(lawSettings.prepareImport(raw).ok,'preview');check(lawSettings.applyImport(raw).ok,'restore');"+
                "check(localStorage.getItem('law-reader-align')===null,'no stale preference');"+
                "check(localStorage.getItem('outside-backup')==='keep','unrelated preserved');"+
                "check(!lawSettings.prepareImport('{\"schema\":99}').ok,'invalid backup');"+
                "document.querySelector('[data-mobile=search]').click();const input=document.getElementById('mobile-search');"+
                "input.value='14';input.dispatchEvent(new Event('input'));return true;})()";
            check("true".equals(js(test)),"Shared reader checks");Thread.sleep(500);
            check("true".equals(js("document.querySelectorAll('.m-result').length>0")),"Search through actual DOM");
            js("document.querySelector('.m-result').click()");
            check("true".equals(js("location.hash.length>1")),"Result navigation");
            js("lawMobile.goTo('article_14');lawMobile.saveSession()");
            runOnMainSync(()->activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE));Thread.sleep(500);
            check("true".equals(js("!!document.getElementById('article_14')")),"Rotation");
            runOnMainSync(()->web.reload());Thread.sleep(500);ready();
            check("\"24\"".equals(js("localStorage.getItem('law-reader-font')")),"Preferences after reload");
            check("\"#article_14\"".equals(js("location.hash")),"Reading location after reload");
            js("window.__remoteBlocked=null;fetch('https://example.com/blocked').then(r=>window.__remoteBlocked=!r.ok).catch(()=>window.__remoteBlocked=true)");
            for(int i=0;i<40&& !"true".equals(js("window.__remoteBlocked"));i++)Thread.sleep(100);
            check("true".equals(js("window.__remoteBlocked")),"Unauthorized resources blocked");
            js("window.__frameExecuted=false;const f=document.createElement('iframe');f.srcdoc='<script>parent.__frameExecuted=true<'+ '/script>';document.body.append(f)");Thread.sleep(300);
            check("false".equals(js("window.__frameExecuted")),"Subframe scripts blocked");
            report.putString("stage","native attachment and bounded clipboard");
            testAttachmentAndClipboard();
            report.putString("attachments","PASS: native intent, cross-UID read grant and exact bundled bytes; no Word rendering claim");
            report.putString("stage","native sharesheet");
            testNativeShare();
            report.putString("share","PASS: native sharesheet delivery -> cross-UID receiver -> exact section URL");
            report.putString("stage","native SAF");
            testNativeSettingsFiles();
            report.putString("SAF","PASS: native CreateDocument -> saved JSON -> OpenDocument -> explicit confirmation -> restored preference");
            report.putString("stage","native print");
            testNativePrintPresentation();
            report.putString("print","PASS: actual system print presentation and cancel; no physical printer or PDF byte validation claim");
            // Stress real navigation and search index cache without constructing duplicate indexes.
            check("true".equals(js("(()=>{const first=lawMobile.buildSearch();for(let i=0;i<100;i++){lawMobile.goTo('article_'+(i%10+1),false);if(lawMobile.buildSearch()!==first)return false;}return true})()")),"Navigation stress");
            android.os.Debug.MemoryInfo finalMemory=new android.os.Debug.MemoryInfo();
            android.os.Debug.getMemoryInfo(finalMemory);
            report.putInt("mainProcessPssKBAfterStress",finalMemory.getTotalPss());
            report.putLong("mainProcessCpuMilliseconds",android.os.Process.getElapsedCpuTime()-cpuStart);
            report.putString("QA_STATUS","PASS");report.putString("coverage","real WebView, offline content, Hebrew offsets, search->result, restore, rotation, reload, URL/frame isolation, stress");
            finish(Activity.RESULT_OK,report);
        }catch(Throwable error){report.putString("QA_STATUS","FAIL");report.putString("error",error.toString());finish(Activity.RESULT_CANCELED,report);}
    }
}
