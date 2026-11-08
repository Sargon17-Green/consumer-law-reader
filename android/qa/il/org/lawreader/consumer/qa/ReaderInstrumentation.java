package il.org.lawreader.consumer.qa;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

/** Runs inside the actual installed app, against its actual bundled legal DOM. */
public final class ReaderInstrumentation extends Instrumentation {
    private Activity activity;
    private WebView web;
    private boolean expectDate,seed,verifyUpgrade;
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);expectDate=arguments!=null&&"true".equals(arguments.getString("expectDate"));seed=arguments!=null&&"true".equals(arguments.getString("seed"));verifyUpgrade=arguments!=null&&"true".equals(arguments.getString("verifyUpgrade"));start(); }
    private WebView find(View view) {
        if(view instanceof WebView)return (WebView)view;
        if(view instanceof ViewGroup){ViewGroup g=(ViewGroup)view;for(int i=0;i<g.getChildCount();i++){WebView found=find(g.getChildAt(i));if(found!=null)return found;}}
        return null;
    }
    private String js(final String source) throws Exception {
        final String[] value={null};CountDownLatch done=new CountDownLatch(1);
        runOnMainSync(()->web.evaluateJavascript(source,result->{value[0]=result;done.countDown();}));
        if(!done.await(30,TimeUnit.SECONDS))throw new Exception("JavaScript callback timeout");
        return value[0];
    }
    private void check(boolean value,String label) throws Exception {if(!value)throw new Exception(label);}
    private void ready() throws Exception {
        for(int i=0;i<240;i++) {if("true".equals(js(seed?"!!window.lawMobile":"document.documentElement.dataset.lawReady === 'true'")))return;Thread.sleep(250);}
        throw new Exception("No application readiness; WebView="+WebView.getCurrentWebViewPackage());
    }
    @Override public void onStart() {
        Bundle report=new Bundle();
        try{
            Intent intent=getTargetContext().getPackageManager().getLaunchIntentForPackage("il.org.lawreader.consumer");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
            activity=startActivitySync(intent);
            runOnMainSync(()->web=find(activity.findViewById(android.R.id.content)));
            check(web!=null,"No native WebView");ready();
            report.putString("webview",WebView.getCurrentWebViewPackage().versionName);
            if(seed){
                js("localStorage.setItem('law-reader-font','23');localStorage.setItem('law-reader-align','right');localStorage.setItem('law-reader-topics-v1',JSON.stringify({schema:1,userTopics:[{id:'u:upgrade',title:'נושא בדיקת שדרוג',parent:null,index:1000}],links:[{id:'u:upgrade-link',topic:'u:upgrade',target:'article_14',title:'סעיף 14'}],titles:{},hidden:{},ranks:{}}))");
                report.putString("QA_STATUS","PASS");report.putString("coverage","Seeded public-beta COPY using disposable QA identity");finish(Activity.RESULT_OK,report);return;
            }
            if(verifyUpgrade){
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
            String test="(function(){const check=(v,m)=>{if(!v)throw Error(m)};"+
                "check(lawMobile.buildSearch().length>500,'full offline index');"+
                "check(LawCore.snippet('אָב שָׁלוֹם סוף','שלום').mark==='שָׁלוֹם','UTF16 mapping');"+
                "localStorage.setItem('outside-backup','keep');localStorage.setItem('law-reader-font','24');"+
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
            // Stress real navigation and search index cache without constructing duplicate indexes.
            check("true".equals(js("(()=>{const first=lawMobile.buildSearch();for(let i=0;i<100;i++){lawMobile.goTo('article_'+(i%10+1),false);if(lawMobile.buildSearch()!==first)return false;}return true})()")),"Navigation stress");
            report.putString("QA_STATUS","PASS");report.putString("coverage","real WebView, offline content, Hebrew offsets, search->result, restore, rotation, reload, URL/frame isolation, stress");
            finish(Activity.RESULT_OK,report);
        }catch(Throwable error){report.putString("QA_STATUS","FAIL");report.putString("error",error.toString());finish(Activity.RESULT_CANCELED,report);}
    }
}
