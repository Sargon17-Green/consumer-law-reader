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
    private boolean expectDate,seed,verifySeed,verifyUpgrade,rendererOnly;
    private String expectedFont;
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);rendererOnly=arguments!=null&&"true".equals(arguments.getString("rendererOnly"));expectedFont=arguments==null?null:arguments.getString("expectedFont");expectDate=arguments!=null&&"true".equals(arguments.getString("expectDate"));seed=arguments!=null&&"true".equals(arguments.getString("seed"));verifySeed=arguments!=null&&"true".equals(arguments.getString("verifySeed"));verifyUpgrade=arguments!=null&&"true".equals(arguments.getString("verifyUpgrade"));start(); }
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
    private void awaitJS(String expression,String label) throws Exception {
        long deadline=android.os.SystemClock.elapsedRealtime()+20000;
        do{
            if("true".equals(js("Boolean("+expression+")")))return;
            Thread.sleep(100);
        }while(android.os.SystemClock.elapsedRealtime()<deadline);
        throw new Exception(label+"; condition="+expression);
    }
    private void ready() throws Exception {
        for(int i=0;i<240;i++) {
            if("true".equals(js((seed||verifySeed)?"!!window.lawMobile":"document.documentElement.dataset.lawReady === 'true' && document.visibilityState === 'visible' && !matchMedia('print').matches"))){
                if(seed||verifySeed)return;
                final boolean[] nativeReady={false};
                runOnMainSync(()->{
                    try{java.lang.reflect.Field field=activity.getClass().getDeclaredField("ready");field.setAccessible(true);nativeReady[0]=field.getBoolean(activity);}
                    catch(ReflectiveOperationException failure){throw new RuntimeException(failure);}
                });
                final boolean[] focused={false};
                runOnMainSync(()->focused[0]=activity.hasWindowFocus());
                if(nativeReady[0]&&focused[0])return;
            }
            Thread.sleep(250);
        }
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
    private String systemLabels(AccessibilityNodeInfo node,int depth){
        if(node==null||depth>9)return "";
        StringBuilder out=new StringBuilder();
        if(node.getText()!=null)out.append(node.getText().toString().replace('\n',' ')).append(" ");
        if(node.getContentDescription()!=null)out.append("[").append(node.getContentDescription()).append("] ");
        for(int i=0;i<node.getChildCount()&&out.length()<4000;i++)out.append(systemLabels(node.getChild(i),depth+1));
        return out.substring(0,Math.min(4000,out.length()));
    }
    private void clickSystemText(String text) throws Exception {
        clickSystemText(text,null);
    }
    private void clickSystemText(String text,CountDownLatch completed) throws Exception {
        try{getUiAutomation().waitForIdle(700,8000);}catch(java.util.concurrent.TimeoutException busy){}
        android.accessibilityservice.AccessibilityServiceInfo info=getUiAutomation().getServiceInfo();
        int originalFlags=info==null?0:info.flags;
        try{
            for(int attempt=0;attempt<100;attempt++){
                if(completed!=null&&completed.getCount()==0)return;
                AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
                // Expand Oreo's grouped filename only in the small system
                // picker, never across the large reading WebView.
                boolean picker=root!=null&&String.valueOf(root.getPackageName()).endsWith(".documentsui");
                int flags=picker?originalFlags|android.accessibilityservice.AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS:originalFlags;
                if(info!=null&&info.flags!=flags){info.flags=flags;getUiAutomation().setServiceInfo(info);root=getUiAutomation().getRootInActiveWindow();}
                if(completed!=null&&root!=null&&"il.org.lawreader.consumer".contentEquals(String.valueOf(root.getPackageName()))){Thread.sleep(100);continue;}
                AccessibilityNodeInfo named=findText(root,text),node=named;
                for(int depth=0;node!=null&&depth<6;depth++,node=node.getParent())
                    if(node.isClickable()&&node.isEnabled()&&node.performAction(AccessibilityNodeInfo.ACTION_CLICK))return;
                // Oreo DocumentsUI handles row touches in RecyclerView's item listener;
                // neither the named filename nor its parents expose ACTION_CLICK.
                // Target the exact visible label's measured bounds, never guessed coordinates.
                if(picker&&named!=null&&named.isVisibleToUser()&&named.isEnabled()){
                    android.graphics.Rect target=new android.graphics.Rect(),window=new android.graphics.Rect();
                    named.getBoundsInScreen(target);root.getBoundsInScreen(window);
                    if(!target.isEmpty()&&window.contains(target.centerX(),target.centerY())){
                        long downTime=android.os.SystemClock.uptimeMillis();
                        android.view.MotionEvent down=android.view.MotionEvent.obtain(downTime,downTime,android.view.MotionEvent.ACTION_DOWN,target.centerX(),target.centerY(),0);
                        down.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);
                        boolean delivered=getUiAutomation().injectInputEvent(down,true);down.recycle();
                        Thread.sleep(60);
                        android.view.MotionEvent up=android.view.MotionEvent.obtain(downTime,android.os.SystemClock.uptimeMillis(),android.view.MotionEvent.ACTION_UP,target.centerX(),target.centerY(),0);
                        up.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);
                        boolean released=getUiAutomation().injectInputEvent(up,true);up.recycle();
                        if(delivered&&released)return;
                    }
                }
                Thread.sleep(100);
            }
            throw new Exception("Native control not found: "+text+"; "+systemLabels(getUiAutomation().getRootInActiveWindow(),0));
        }finally{
            if(info!=null&&info.flags!=originalFlags){info.flags=originalFlags;getUiAutomation().setServiceInfo(info);}
        }
    }
    private void recordSystemTree(AccessibilityNodeInfo node,org.json.JSONArray nodes,int depth) throws Exception {
        if(node==null||depth>24||nodes.length()>=512)return;
        JSONObject item=new JSONObject();android.graphics.Rect bounds=new android.graphics.Rect();node.getBoundsInScreen(bounds);
        item.put("class",String.valueOf(node.getClassName()));item.put("id",node.getViewIdResourceName());item.put("bounds",bounds.toShortString());
        item.put("text",String.valueOf(node.getText()).substring(0,Math.min(180,String.valueOf(node.getText()).length())));
        item.put("description",String.valueOf(node.getContentDescription()).substring(0,Math.min(180,String.valueOf(node.getContentDescription()).length())));
        item.put("clickable",node.isClickable());item.put("enabled",node.isEnabled());item.put("depth",depth);nodes.put(item);
        for(int i=0;i<node.getChildCount()&&nodes.length()<512;i++)recordSystemTree(node.getChild(i),nodes,depth+1);
    }
    private void testNativeSettingsFiles(Bundle report) throws Exception {
        ready();
        shell("rm -f /sdcard/Download/consumer-law-settings.json");
        // A portable legacy-size backup must not travel inside Activity saved
        // state (Binder has a process-wide, approximately 1 MB transaction limit).
        check("true".equals(js("(()=>{const data={schema:1,userTopics:[{id:'u:large',title:'large',parent:null,index:1000}],links:[],titles:{},hidden:{},ranks:{}};for(let i=0;i<2000;i++)data.links.push({id:'u:large-'+i,topic:'u:large',target:'article_14',title:'א'.repeat(90)});localStorage.setItem('law-reader-topics-v1',JSON.stringify(data));return lawSettings.exportJSON().length>300000})()")),"Large valid portable backup fixture");
        js("NativeLaw.exportSettings()");
        long chooserDeadline=android.os.SystemClock.elapsedRealtime()+20000;
        boolean chooserReady=false;
        while(android.os.SystemClock.elapsedRealtime()<chooserDeadline){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&String.valueOf(root.getPackageName()).endsWith(".documentsui")){chooserReady=true;break;}
            Thread.sleep(100);
        }
        check(chooserReady,"Real SAF save picker opens before saved-state measurement");
        final Bundle state=new Bundle();
        runOnMainSync(()->callActivityOnSaveInstanceState(activity,state));
        android.os.Parcel parcel=android.os.Parcel.obtain();
        try{
            state.writeToParcel(parcel,0);
            report.putInt("activitySavedStateBytes",parcel.dataSize());
            check(Boolean.TRUE.equals(state.get("pendingExport")),"Pending backup state is a small flag, never the JSON payload");
            check(parcel.dataSize()<750000,"Activity saved state must leave margin below Binder's shared limit: "+parcel.dataSize());
        }
        finally{parcel.recycle();}
        clickSystemText("Save");
        JSONObject exported=null;
        for(int i=0;i<60;i++){
            try{exported=new JSONObject(shell("cat /sdcard/Download/consumer-law-settings.json"));break;}
            catch(Exception pending){Thread.sleep(100);}
        }
        check(exported!=null&&"consumer-law-reader-settings".equals(exported.optString("format")),"Actual SAF export file");
        check("24".equals(exported.getJSONObject("settings").getString("law-reader-font")),"SAF export includes real preferences");
        runOnMainSync(()->{
            try{
                java.lang.reflect.Field location=activity.getClass().getDeclaredField("settingsPickerLocation");location.setAccessible(true);
                android.net.Uri uri=(android.net.Uri)location.get(activity);
                report.putString("exportProviderMime",String.valueOf(getTargetContext().getContentResolver().getType(uri)));
            }catch(Exception failure){throw new RuntimeException(failure);}
        });
        js("window.__qaImportGeneration=true;localStorage.setItem('law-reader-font','20');NativeLaw.importSettings()");
        clickSystemText("consumer-law-settings.json");
        clickSystemText("החלפת ההגדרות");
        for(int i=0;i<120;i++){
            if("true".equals(js("typeof window.__qaImportGeneration === 'undefined'")))break;
            Thread.sleep(250);
        }
        check("true".equals(js("typeof window.__qaImportGeneration === 'undefined'")),"Import must load a new document generation");
        ready();
        check("\"24\"".equals(js("localStorage.getItem('law-reader-font')")),"Actual SAF confirmed import");
    }
    private void testAttachmentAndClipboard() throws Exception {
        ready();
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
            ready();js("NativeLaw.copy('QA clipboard fixture')");
            awaitJS("document.getElementById('mobile-toast').textContent==='הטקסט הועתק'","Native clipboard completion acknowledgement");
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
            js("NativeLaw.copy('א'.repeat(450001))");
            awaitJS("document.getElementById('mobile-toast').textContent.includes('לא הושלמה')","Oversized native clipboard rejected honestly without crashing");
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
        ready();
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
                clickSystemText("Reader QA link receiver",received);
                if(received.await(10,TimeUnit.SECONDS))break;
            }
            check(received.await(15,TimeUnit.SECONDS),"Real sharesheet destination received the intent");
            check("https://sargon17-green.github.io/consumer-law-reader/reader/#article_14".equals(text[0]),"Native share retains the exact public section URL");
            ready();
        }finally{getTargetContext().unregisterReceiver(receiver);}
    }
    private void testNativeDateURLPolicy(Bundle report) throws Exception {
        java.lang.reflect.Method policy=activity.getClass().getDeclaredMethod("isApprovedDateSource",android.net.Uri.class);
        policy.setAccessible(true);
        check(Boolean.FALSE.equals(policy.invoke(null,(Object)null)),"Null URL is rejected");
        String[] approved={
            "https://raw.githubusercontent.com/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json",
            "https://api.github.com/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json",
            "https://sargon17-green.github.io/pastafari-calendar/api/seer-now.json"
        };
        int cases=1;
        for(String url:approved){
            check(Boolean.TRUE.equals(policy.invoke(null,android.net.Uri.parse(url))),"Canonical date URL is accepted");cases++;
            check(Boolean.TRUE.equals(policy.invoke(null,android.net.Uri.parse(url+"?_t=123"))),"Bounded timestamp is accepted");cases++;
            for(String invalid:new String[]{url.replace("https://","http://"),url.replace("https://","https://user@"),url.replace("seer-now.json","seer%2Dnow.json"),url+"/extra",url+"#fragment",url+"?_t=1&_t=2",url+"?_t=bad",url+"?other=1",url+"?%5Ft=1",url+"?_t=1&%5Ft=2",url+"?ref=main&r%65f=other",url+"?_t=%31",url+"?_t=12345678901234567",url+"?_t=1&"}){
                check(Boolean.FALSE.equals(policy.invoke(null,android.net.Uri.parse(invalid))),"Unsafe date URL is rejected: "+invalid);cases++;
            }
        }
        check(Boolean.TRUE.equals(policy.invoke(null,android.net.Uri.parse(approved[1]+"?ref=main&_t=123"))),"Canonical REST revision and timestamp are accepted");cases++;
        for(String invalid:new String[]{"https:opaque","https:opaque?x=1","https:","javascript:alert(1)","file:///data/data/secret","content://external/private","https://example.com/seer-now.json"}){
            check(Boolean.FALSE.equals(policy.invoke(null,android.net.Uri.parse(invalid))),"Malformed/foreign URI is rejected without throwing: "+invalid);cases++;
        }
        report.putInt("nativeDateURLPolicyCases",cases);
    }
    private AccessibilityNodeInfo editable(AccessibilityNodeInfo node){
        if(node==null)return null;
        if(node.isEditable()&&node.isEnabled())return node;
        for(int i=0;i<node.getChildCount();i++){AccessibilityNodeInfo found=editable(node.getChild(i));if(found!=null)return found;}
        return null;
    }
    private boolean hasPreparedPrintPage(AccessibilityNodeInfo node){
        if(node==null)return false;
        String label=String.valueOf(node.getText())+" "+String.valueOf(node.getContentDescription());
        if(node.isVisibleToUser()&&java.util.regex.Pattern.compile("\\bPage\\s+[0-9]+\\s+of\\s+[0-9]+\\b").matcher(label).find())return true;
        for(int i=0;i<node.getChildCount();i++)if(hasPreparedPrintPage(node.getChild(i)))return true;
        return false;
    }
    private boolean tapVisibleControl(AccessibilityNodeInfo node) throws Exception {
        if(node==null||!node.refresh()||!node.isVisibleToUser()||!node.isEnabled())return false;
        android.graphics.Rect bounds=new android.graphics.Rect();node.getBoundsInScreen(bounds);
        if(bounds.isEmpty())return false;
        long start=android.os.SystemClock.uptimeMillis();
        android.view.MotionEvent down=android.view.MotionEvent.obtain(start,start,android.view.MotionEvent.ACTION_DOWN,bounds.centerX(),bounds.centerY(),0);
        down.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);boolean pressed=getUiAutomation().injectInputEvent(down,true);down.recycle();
        Thread.sleep(60);
        android.view.MotionEvent up=android.view.MotionEvent.obtain(start,android.os.SystemClock.uptimeMillis(),android.view.MotionEvent.ACTION_UP,bounds.centerX(),bounds.centerY(),0);
        up.setSource(android.view.InputDevice.SOURCE_TOUCHSCREEN);boolean released=getUiAutomation().injectInputEvent(up,true);up.recycle();
        return pressed&&released;
    }
    private void capturePrintReady(Bundle report) throws Exception {
        AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
        report.putString("printReadyControls",systemLabels(root,0));
        org.json.JSONArray nodes=new org.json.JSONArray();recordSystemTree(root,nodes,0);
        try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(getTargetContext().getFilesDir(),"qa-print-ready.json"))){out.write(nodes.toString(2).getBytes("UTF-8"));}
        android.graphics.Bitmap shot=getUiAutomation().takeScreenshot();
        if(shot!=null){try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(getTargetContext().getFilesDir(),"qa-print-ready.png"))){shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}shot.recycle();}
    }
    private void saveAndVerifySystemPDF(Bundle report) throws Exception {
        shell("rm -f /sdcard/Download/consumer-law-qa.pdf");
        boolean clicked=false;
        for(int attempt=0;attempt<360;attempt++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&"com.android.printspooler".contentEquals(String.valueOf(root.getPackageName()))){
                if(findText(root,"Select a printer")!=null){
                    clickSystemText("Select a printer");clickSystemText("Save as PDF");continue;
                }
                if(findText(root,"Save as PDF")==null){Thread.sleep(250);continue;}
                for(AccessibilityNodeInfo button:root.findAccessibilityNodeInfosByViewId("com.android.printspooler:id/print_button"))
                    // The framework keeps this view enabled while setting it GONE
                    // until the document update is complete. ID lookup alone also finds hidden views.
                    if(hasPreparedPrintPage(root)&&button.refresh()&&button.isVisibleToUser()&&button.isClickable()&&button.isEnabled()){capturePrintReady(report);if(tapVisibleControl(button)){clicked=true;break;}}
            }
            if(clicked)break;
            Thread.sleep(250);
        }
        check(clicked,"A prepared print-preview page and visible Save as PDF control: "+systemLabels(getUiAutomation().getRootInActiveWindow(),0));
        boolean named=false;
        for(int attempt=0;attempt<160;attempt++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&String.valueOf(root.getPackageName()).endsWith(".documentsui")){
                AccessibilityNodeInfo input=editable(root);
                if(input!=null){Bundle value=new Bundle();value.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,"consumer-law-qa.pdf");named=input.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,value);if(named)break;}
            }
            Thread.sleep(250);
        }
        check(named,"Real PDF save picker exposes its filename input");
        clickSystemText("Save");
        boolean generated=false;
        for(int attempt=0;attempt<180;attempt++){
            if("%PDF-".equals(shell("head -c 5 /sdcard/Download/consumer-law-qa.pdf"))){generated=true;break;}
            Thread.sleep(500);
        }
        check(generated,"System print framework saved actual PDF bytes");
        ready();
        java.io.File file=new java.io.File(getTargetContext().getFilesDir(),"qa-native-document.pdf");
        android.util.Log.i("ReaderPDFQA","Reading completed SAF document into private QA evidence; no external cp/setattr");
        java.security.MessageDigest digest=java.security.MessageDigest.getInstance("SHA-256");
        try(ParcelFileDescriptor descriptor=getUiAutomation().executeShellCommand("cat /sdcard/Download/consumer-law-qa.pdf");
            java.io.InputStream input=new ParcelFileDescriptor.AutoCloseInputStream(descriptor);
            java.io.FileOutputStream output=new java.io.FileOutputStream(file)){
            byte[] buffer=new byte[16384];int count,total=0;
            while((count=input.read(buffer))!=-1){total+=count;check(total<=32*1024*1024,"Bounded PDF evidence stream");output.write(buffer,0,count);digest.update(buffer,0,count);}
        }
        android.util.Log.i("ReaderPDFQA","Private PDF evidence complete bytes="+file.length());
        int pages;
        try(android.graphics.pdf.PdfRenderer pdf=new android.graphics.pdf.PdfRenderer(ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY))){
            pages=pdf.getPageCount();check(pages>0,"Native saved PDF has pages");
            android.graphics.Bitmap image=android.graphics.Bitmap.createBitmap(120,170,android.graphics.Bitmap.Config.ARGB_8888);
            image.eraseColor(android.graphics.Color.WHITE);
            try(android.graphics.pdf.PdfRenderer.Page page=pdf.openPage(0)){page.render(image,null,null,android.graphics.pdf.PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);}
            int[] pixels=new int[120*170];image.getPixels(pixels,0,120,0,0,120,170);image.recycle();
            int ink=0;for(int pixel:pixels)if((pixel>>>24)>200&&(pixel&0x00ffffff)<0x00dddddd)ink++;
            check(ink>20,"Saved PDF must render visible ink, not an empty page");
        }
        StringBuilder checksum=new StringBuilder();for(byte b:digest.digest())checksum.append(String.format("%02x",b&255));
        report.putString("PDF","PASS: actual system Print -> Save as PDF -> SAF file; pages="+pages+" bytes="+file.length()+" sha256="+checksum);
    }
    private void testNativePrintPresentation(Bundle report) throws Exception {
        ready();
        js("NativeLaw.printDocument()");
        boolean opened=false;
        for(int i=0;i<80;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&"com.android.printspooler".contentEquals(root.getPackageName())){opened=true;break;}
            Thread.sleep(250);
        }
        check(opened,"Real Android system print interface opens; "+systemLabels(getUiAutomation().getRootInActiveWindow(),0));
        if(android.os.Build.VERSION.SDK_INT>=36){saveAndVerifySystemPDF(report);return;}
        shell("input keyevent KEYCODE_BACK");
        for(int i=0;i<80;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&"il.org.lawreader.consumer".contentEquals(root.getPackageName())){Thread.sleep(500);ready();return;}
            Thread.sleep(250);
        }
        throw new Exception("Reader resumes after cancelling system print");
    }
    private void testReadingLayout(Bundle report) throws Exception {
        String source;
        try(java.io.InputStream input=getContext().getAssets().open("reader_layout_probe.js");ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1)output.write(buffer,0,count);
            source=new String(output.toByteArray(),"UTF-8");
        }
        String options="{sizes:[18,28,48],regulationIds:['used_vehicle_trading_regulations','Calculation_of_annual_interest_rate','Calculation_of_annual_interest_rate_2','Disclosure_of_material_detail_regarding_diamonds_gems_pearls_and_gold_products']}";
        JSONObject result=new JSONObject(new org.json.JSONTokener(js("JSON.stringify(("+source+")("+options+"))")).nextValue().toString());
        check(result.getInt("regulations")==4,"Layout regression fixtures present");
        check(result.getJSONArray("issues").length()==0,"Native WebView horizontal layout: "+result.toString());
        report.putString("readingLayout",result.toString());
        js("lawMobile.goTo('article_14',false,false)");
        awaitJS("document.documentElement.scrollWidth<=innerWidth+1","Whole reading page fits after restoring font");
        final boolean[] overflow={false};runOnMainSync(()->overflow[0]=web.canScrollHorizontally(-1)||web.canScrollHorizontally(1));
        check(!overflow[0],"Actual native WebView cannot pan the whole reading page horizontally");
    }
    private void testRealRendererRecovery(Bundle report) throws Exception {
        check(android.os.Build.VERSION.SDK_INT>=29,"Public renderer termination requires API29+");
        ready();
        js("localStorage.setItem('law-reader-font','24');document.documentElement.style.setProperty('--reading-size','24px');lawMobile.goTo('article_14');lawMobile.saveSession('article_14')");
        Activity previous=activity;WebView previousWeb=web;
        CountDownLatch resumed=new CountDownLatch(1);final Activity[] replacement={null};
        android.app.Application application=(android.app.Application)getTargetContext().getApplicationContext();
        android.app.Application.ActivityLifecycleCallbacks observer=new android.app.Application.ActivityLifecycleCallbacks(){
            public void onActivityCreated(Activity a,Bundle b){}
            public void onActivityStarted(Activity a){}
            public void onActivityResumed(Activity a){if(a!=previous&&a.getClass().getName().equals("il.org.lawreader.consumer.MainActivity")){replacement[0]=a;resumed.countDown();}}
            public void onActivityPaused(Activity a){}
            public void onActivityStopped(Activity a){}
            public void onActivitySaveInstanceState(Activity a,Bundle b){}
            public void onActivityDestroyed(Activity a){}
        };
        runOnMainSync(()->application.registerActivityLifecycleCallbacks(observer));
        try{
            final boolean[] terminated={false};
            runOnMainSync(()->{android.webkit.WebViewRenderProcess process=web.getWebViewRenderProcess();terminated[0]=process!=null&&process.terminate();});
            check(terminated[0],"Actual isolated WebView renderer accepted public terminate()");
            clickSystemText("פתיחה מחדש");
            check(resumed.await(60,TimeUnit.SECONDS),"Native recovery must recreate and resume an actual Activity");
            activity=replacement[0];runOnMainSync(()->web=find(activity.findViewById(android.R.id.content)));
            check(web!=null&&web!=previousWeb,"Recovery replaces the unusable WebView");
            ready();
            check("\"24\"".equals(js("localStorage.getItem('law-reader-font')")),"Renderer termination preserves preferences");
            // Session restoration reconstructs the logical section without
            // inserting native WebView history entries. Verify the displayed
            // section and stored anchor, rather than requiring a URL hash.
            awaitJS("lawMobile.currentArticle()?.id==='article_14'","Renderer recovery displays the saved exact section");
            String state=js("({hash:location.hash,current:lawMobile.currentArticle()?.id,font:localStorage.getItem('law-reader-font'),session:JSON.parse(localStorage.getItem('law-reader-session-v1')||'null')})");
            report.putString("rendererState",state);
            try(java.io.FileOutputStream output=new java.io.FileOutputStream(new java.io.File(getTargetContext().getFilesDir(),"qa-renderer-state.json"))){output.write(state.getBytes("UTF-8"));}
            android.graphics.Bitmap shot=getUiAutomation().takeScreenshot();
            if(shot!=null){try(java.io.FileOutputStream output=new java.io.FileOutputStream(new java.io.File(getTargetContext().getFilesDir(),"qa-renderer-state.png"))){shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,output);}shot.recycle();}
            check("article_14".equals(new JSONObject(state).getJSONObject("session").getString("target")),"Renderer recovery keeps the logical stored section");
            check("true".equals(js("lawMobile.buildSearch().length>500")),"Recovered real renderer searches the offline law");
            report.putString("rendererRecovery","PASS: actual public renderer terminate -> native recovery alert -> new Activity/WebView -> actual Ready; font/section/search preserved");
        }finally{runOnMainSync(()->application.unregisterActivityLifecycleCallbacks(observer));}
    }
    @Override public void onStart() {
        Bundle report=new Bundle();
        final long launchStart=android.os.SystemClock.elapsedRealtime();
        final long cpuStart=android.os.Process.getElapsedCpuTime();
        try{
            android.accessibilityservice.AccessibilityServiceInfo automation=getUiAutomation().getServiceInfo();
            if(automation!=null){
                automation.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS|android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
                getUiAutomation().setServiceInfo(automation);
            }
            Intent intent=getTargetContext().getPackageManager().getLaunchIntentForPackage("il.org.lawreader.consumer");
            check(intent!=null&&intent.hasCategory(Intent.CATEGORY_LAUNCHER),"Installed app has a permanent launcher entry");
            check(getTargetContext().getPackageManager().getApplicationIcon("il.org.lawreader.consumer")!=null,"Installed app icon resolves");
            report.putString("launcher",intent.getComponent().flattenToShortString());
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
            if(rendererOnly){report.putString("stage","actual renderer termination and recovery");testRealRendererRecovery(report);report.putString("QA_STATUS","PASS");finish(Activity.RESULT_OK,report);return;}
            testNativeDateURLPolicy(report);
            report.putString("stage","responsive native reading layout");testReadingLayout(report);
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
            check("true".equals(js(test)),"Shared reader checks");
            awaitJS("document.querySelectorAll('.m-result').length>0","Search through actual DOM");
            js("document.querySelector('.m-result').click()");
            check("true".equals(js("location.hash.length>1")),"Result navigation");
            js("lawMobile.goTo('article_14');lawMobile.saveSession()");
            runOnMainSync(()->activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE));Thread.sleep(500);
            check("true".equals(js("!!document.getElementById('article_14')")),"Rotation");
            js("window.__qaReloadGeneration=true");
            runOnMainSync(()->web.reload());
            awaitJS("typeof window.__qaReloadGeneration==='undefined'","Reader reload must replace the document");
            ready();
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
            testNativeSettingsFiles(report);
            report.putString("SAF","PASS: native CreateDocument -> saved JSON -> OpenDocument -> explicit confirmation -> restored preference");
            report.putString("stage","native print");
            testNativePrintPresentation(report);
            report.putString("print",android.os.Build.VERSION.SDK_INT>=36?"PASS: system Print and PDF save; see PDF byte validation":"PASS: actual system print presentation and cancel; no physical printer claim");
            // Stress real navigation and search index cache without constructing duplicate indexes.
            report.putString("stage","navigation stress after native print");
            String stress=js("(()=>{try{const first=lawMobile.buildSearch();for(let i=0;i<100;i++){lawMobile.goTo('article_'+(i%10+1),false);if(lawMobile.buildSearch()!==first)throw Error('Index identity changed');}return {ok:true,records:first.length}}catch(error){return {ok:false,error:String(error),visibility:document.visibilityState,printing:matchMedia('print').matches}}})()");
            report.putString("navigationStressResult",stress);
            check(new JSONObject(stress).optBoolean("ok"),"Navigation stress: "+stress);
            android.os.Debug.MemoryInfo finalMemory=new android.os.Debug.MemoryInfo();
            android.os.Debug.getMemoryInfo(finalMemory);
            report.putInt("mainProcessPssKBAfterStress",finalMemory.getTotalPss());
            report.putLong("mainProcessCpuMilliseconds",android.os.Process.getElapsedCpuTime()-cpuStart);
            report.putString("QA_STATUS","PASS");report.putString("coverage","real WebView, offline content, Hebrew offsets, search->result, restore, rotation, reload, URL/frame isolation, stress");
            finish(Activity.RESULT_OK,report);
        }catch(Throwable error){
            report.putString("QA_STATUS","FAIL");report.putString("error",error.toString());
            try{
                AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
                String pkg=root==null?"":String.valueOf(root.getPackageName());
                if(pkg.endsWith(".documentsui")||pkg.equals("com.android.printspooler")){
                    org.json.JSONArray nodes=new org.json.JSONArray();recordSystemTree(root,nodes,0);
                    try(java.io.FileOutputStream output=new java.io.FileOutputStream(new java.io.File(getTargetContext().getFilesDir(),"qa-system-ui.json"))){output.write(nodes.toString(2).getBytes("UTF-8"));}
                }
                android.graphics.Bitmap shot=getUiAutomation().takeScreenshot();
                if(shot!=null){
                    java.io.File file=new java.io.File(getTargetContext().getFilesDir(),"qa-failure.png");
                    try(java.io.FileOutputStream output=new java.io.FileOutputStream(file)){shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,output);}
                    shot.recycle();report.putString("failureScreenshot",file.toString());
                }
            }catch(Exception screenshotError){report.putString("screenshotError",screenshotError.toString());}
            finish(Activity.RESULT_CANCELED,report);
        }
    }
}
