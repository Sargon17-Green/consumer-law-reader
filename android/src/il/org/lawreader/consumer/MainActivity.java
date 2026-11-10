package il.org.lawreader.consumer;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.webkit.WebResourceError;
import android.webkit.RenderProcessGoneDetail;
import org.json.JSONObject;
import org.json.JSONTokener;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;
import android.print.PrintManager;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.File;
import java.io.FileOutputStream;
import android.util.AtomicFile;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/** All legal content is bundled; external publications open in the user's browser. */
public final class MainActivity extends Activity {
    private static final String HOST = "law.local";
    private static final String HOME = "https://" + HOST + "/index.html";
    private WebView web;
    private WebViewStateCache webStateCache;
    private boolean ready;
    private android.window.OnBackInvokedCallback systemBack;
    private boolean pendingExport;
    private boolean settingsBusy;
    private Uri settingsPickerLocation;
    private static final int EXPORT_SETTINGS = 2101, IMPORT_SETTINGS = 2102;
    private static final int MAX_BACKUP = 1000000;
    private static final int MAX_COPY = 450000; // UTF-16 payload stays below Binder's shared 1 MB buffer.

    /**
     * Only the three canonical HTTPS snapshot locations may be reached from the
     * bundled legal document. External scripts, images, frames and arbitrary
     * fetch destinations remain blocked by the local asset interceptor.
     */
    private static boolean isApprovedDateSource(Uri uri) {
        if (uri == null || !uri.isHierarchical() || !"https".equals(uri.getScheme()) || uri.getPort() != -1 || uri.getUserInfo() != null || uri.getFragment() != null) return false;
        String host = uri.getHost();
        String path = uri.getEncodedPath();
        String query = uri.getEncodedQuery();
        if (query != null) {
            if (query.length() > 64) return false;
            boolean timestamp=false, revision=false;
            // Match the canonical wire query. Decoded-name enumeration can
            // overlook aliases such as ref=main&r%65f=another-branch.
            for (String item : query.split("&",-1)) {
                if (!timestamp && item.matches("_t=[0-9]{1,16}")) timestamp=true;
                else if (!revision && "api.github.com".equals(host) && "ref=main".equals(item)) revision=true;
                else return false;
            }
        }
        return ("raw.githubusercontent.com".equals(host)
                    && "/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json".equals(path))
            || ("api.github.com".equals(host)
                    && "/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json".equals(path))
            || ("sargon17-green.github.io".equals(host)
                    && "/pastafari-calendar/api/seer-now.json".equals(path));
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if(savedInstanceState!=null){
            pendingExport=savedInstanceState.getBoolean("pendingExport");
            String picker=savedInstanceState.getString("settingsPickerLocation");
            if(picker!=null&&picker.length()<=4096){
                Uri candidate=Uri.parse(picker);
                if("content".equals(candidate.getScheme()))settingsPickerLocation=candidate;
            }
        }
        if(!pendingExport)pendingExportFile().delete();
        final FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(20,47,65));
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((view, insets) -> {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                android.graphics.Insets keyboard = insets.getInsets(WindowInsets.Type.ime());
                root.setPadding(bars.left,bars.top,bars.right,Math.max(bars.bottom,keyboard.bottom));
                return insets;
            });
        }
        web = new WebView(this);
        webStateCache = new WebViewStateCache(this);
        web.setBackgroundColor(Color.WHITE);
        web.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        settings.setTextZoom(Math.round(100 * getResources().getConfiguration().fontScale));
        settings.setSupportMultipleWindows(false);
        settings.setSafeBrowsingEnabled(true);
        android.webkit.CookieManager.getInstance().setAcceptCookie(false);
        android.webkit.CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        web.addJavascriptInterface(new LocalBridge(), "NativeLaw");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return request.isForMainFrame() ? handleNavigation(request.getUrl()) : !isLocalDocument(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleNavigation(Uri.parse(url));
            }
            @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap icon) { ready=false; }
            @Override public void onPageFinished(WebView view,String url) {
                view.evaluateJavascript("document.documentElement.dataset.lawReady === 'true'",result -> {
                    ready="true".equals(result);
                    if(!ready && !isFinishing() && !isDestroyed())new AlertDialog.Builder(MainActivity.this)
                        .setMessage("ממשק הקריאה לא אותחל. יש לוודא ש־Android System WebView או Chrome מעודכנים, ולנסות שוב.")
                        .setPositiveButton("ניסיון נוסף",(d,w)->web.loadUrl(HOME)).setNegativeButton("ביטול",null).show();
                });
            }
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error) {
                if(request.isForMainFrame()) { ready=false; showLoadError(); }
            }
            @Override public boolean onRenderProcessGone(WebView view,RenderProcessGoneDetail detail) {
                ready=false;
                if(!isFinishing() && !isDestroyed())new AlertDialog.Builder(MainActivity.this).setMessage("תהליך הקריאה נסגר. ההעדפות נשמרו; אפשר לפתוח מחדש.")
                    .setPositiveButton("פתיחה מחדש",(d,w)->recreate()).setCancelable(false).show();
                if(view.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)view.getParent()).removeView(view);
                view.destroy();if(web==view)web=null;return true;
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!isLocalDocument(uri)) {
                    // The bounded native proxy adds the local origin's CORS
                    // response. Other remote resources remain denied.
                    if ("GET".equals(request.getMethod()) && isApprovedDateSource(uri)) return dateResponse(uri);
                    return missing();
                }
                String path = uri.getPath();
                if (path == null || path.equals("/")) path = "/index.html";
                if (path.contains("..") || path.contains("\\") || !"GET".equals(request.getMethod())) return missing();
                String mime = mime(path);
                try {
                    Map<String,String> headers = new HashMap<>();
                    headers.put("X-Content-Type-Options","nosniff");
                    headers.put("Cache-Control","no-cache");
                    if ("/index.html".equals(path)) {
                        headers.put("Content-Security-Policy",
                            "frame-src 'none'; child-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'");
                    }
                    return new WebResourceResponse(mime,"UTF-8",200,"OK",headers,getAssets().open("www"+path));
                } catch (IOException ex) { return missing(); }
            }
        });
        root.addView(web,new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
        if(Build.VERSION.SDK_INT>=33){systemBack=()->handleBack();getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,systemBack);}
        Bundle history=savedInstanceState;
        if(savedInstanceState!=null&&savedInstanceState.containsKey(WebViewStateCache.KEY))history=webStateCache.read(savedInstanceState.getString(WebViewStateCache.KEY));
        boolean restored=false;
        if(history!=null)try{restored=web.restoreState(history)!=null;}catch(RuntimeException invalid){ /* Fall back to the durable logical session. */ }
        if(!restored)web.loadUrl(HOME);
    }

    private void showLoadError() {
        if(isFinishing() || isDestroyed() || web==null)return;
        new AlertDialog.Builder(this).setMessage("טעינת נוסח החוק המקומי נכשלה.")
            .setPositiveButton("ניסיון נוסף",(d,w)->web.loadUrl(HOME)).setNegativeButton("ביטול",null).show();
    }
    private boolean trusted() {
        if(isFinishing() || isDestroyed() || web==null || !ready || web.getUrl()==null)return false;
        Uri uri=Uri.parse(web.getUrl());
        return isLocalDocument(uri) && "/index.html".equals(uri.getPath()) && uri.getQuery()==null;
    }
    private static WebResourceResponse dateResponse(Uri uri) {
        HttpsURLConnection connection=null;
        try {
            connection=(HttpsURLConnection)new URL(uri.toString()).openConnection();
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(6000);connection.setReadTimeout(6000);
            connection.setUseCaches(false);connection.setRequestProperty("Accept","application/json");
            if(connection.getResponseCode()!=200)return missing();
            if(connection.getContentLengthLong()>262144)return missing();
            byte[] bytes=readBounded(connection.getInputStream(),262144);
            Map<String,String> headers=new HashMap<>();
            headers.put("Access-Control-Allow-Origin","https://law.local");
            headers.put("Cache-Control","no-store");headers.put("X-Content-Type-Options","nosniff");
            return new WebResourceResponse("application/json","UTF-8",200,"OK",headers,new ByteArrayInputStream(bytes));
        }catch(Exception ex){return missing();}finally{if(connection!=null)connection.disconnect();}
    }
    private static byte[] readBounded(InputStream stream,int limit) throws IOException {
        try(InputStream input=stream;ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[16384];int n,total=0;
            while((n=input.read(buffer))!=-1){total+=n;if(total>limit)throw new IOException("File too large");output.write(buffer,0,n);}
            return output.toByteArray();
        }
    }
    private static WebResourceResponse missing() {
        return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
    }
    private static String mime(String path) {
        if (path.endsWith(".js")) return "application/javascript";
        if (path.endsWith(".css")) return "text/css";
        if (path.endsWith(".html")) return "text/html";
        if (path.endsWith(".svg")) return "image/svg+xml";
        if (path.endsWith(".webmanifest")) return "application/manifest+json";
        String extension = MimeTypeMap.getFileExtensionFromUrl(path);
        String result = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
        return result == null ? "application/octet-stream" : result;
    }
    private static boolean isLocalDocument(Uri uri) {
        return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && uri.getPort() == -1 && uri.getUserInfo() == null;
    }
    private boolean handleNavigation(Uri uri) {
        if (isLocalDocument(uri)) {
            if (uri.getPath()!=null && uri.getPath().endsWith(".doc")) {
                openAttachment(uri.getLastPathSegment());
                return true;
            }
            if (("/index.html".equals(uri.getPath()) || "/".equals(uri.getPath())) && uri.getQuery()==null) return false;
            return true;
        }
        if (uri.getUserInfo()!=null) return true;
        if ("https".equals(uri.getScheme()) || "http".equals(uri.getScheme()) || "mailto".equals(uri.getScheme())) {
            try { startActivity(new Intent(Intent.ACTION_VIEW,uri)); }
            catch (Exception ex) { Toast.makeText(this,"לא נמצאה אפליקציה לפתיחת הקישור",Toast.LENGTH_LONG).show(); }
        }
        return true;
    }
    private void openAttachment(final String name) {
        if (name == null || name.contains("/") || name.contains("\\") || name.contains("..") || !name.endsWith(".doc")) return;
        try {
            Uri uri = new Uri.Builder().scheme("content").authority(getPackageName()+".attachments").appendPath(name).build();
            Intent intent = new Intent(Intent.ACTION_VIEW).setDataAndType(uri,"application/msword").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.setClipData(ClipData.newRawUri("מסמך מצורף",uri));
            startActivity(intent);
        } catch (Exception ex) { Toast.makeText(this,"לפתיחת המסמך המצורף נדרשת אפליקציה שקוראת קובצי Word",Toast.LENGTH_LONG).show(); }
    }
    private final class LocalBridge {
        @JavascriptInterface public int copyLimit(){return MAX_COPY;}
        @JavascriptInterface public void exportSettings() { runOnUiThread(() -> { if(trusted())beginExport(); }); }
        @JavascriptInterface public void importSettings() { runOnUiThread(() -> { if(trusted())beginImport(); }); }
        @JavascriptInterface public void share(final String url) { runOnUiThread(() -> {
            if(!trusted() || url==null || url.length()>2048 || !url.startsWith("https://sargon17-green.github.io/consumer-law-reader/reader/#"))return;
            try{startActivity(Intent.createChooser(new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,url),"שיתוף קישור לסעיף"));}
            catch(Exception ex){Toast.makeText(MainActivity.this,"השיתוף אינו זמין",Toast.LENGTH_LONG).show();}
        }); }
        @JavascriptInterface public void copy(final String text) {
            runOnUiThread(() -> {
                if(!trusted())return;
                boolean copied=false;
                if(text!=null && text.length()<=MAX_COPY){
                    try{
                        ClipboardManager clipboard = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                        clipboard.setPrimaryClip(ClipData.newPlainText("חוק הגנת הצרכן, התשמ\"א–1981",text));
                        copied=true;
                    }catch(RuntimeException failure){/* A rejected IPC must not crash the reader. */}
                }
                web.evaluateJavascript("window.lawMobile?.copyResult?.("+copied+")",null);
            });
        }
        @JavascriptInterface public void openAttachment(final String name) { runOnUiThread(() -> { if(trusted())MainActivity.this.openAttachment(name); }); }
        @JavascriptInterface public void printDocument() {
            runOnUiThread(() -> {
                if(!trusted())return;
                PrintManager manager = (PrintManager)getSystemService(PRINT_SERVICE);
                manager.print("חוק הגנת הצרכן, התשמ\"א–1981",web.createPrintDocumentAdapter("חוק הגנת הצרכן, התשמ\"א–1981"),null);
            });
        }
    }
    private void beginExport() {
        if(settingsBusy || pendingExport)return;
        settingsBusy=true;
        web.evaluateJavascript("window.lawSettings.exportJSON()",result -> {
            try {
                Object value=new JSONTokener(result).nextValue();
                if(!(value instanceof String) || ((String)value).getBytes("UTF-8").length>MAX_BACKUP)throw new Exception();
                final byte[] contents=((String)value).getBytes("UTF-8");
                new Thread(()->{
                    AtomicFile file=pendingExportFile();FileOutputStream output=null;
                    try{
                        output=file.startWrite();output.write(contents);file.finishWrite(output);output=null;
                        runOnUiThread(()->{
                            settingsBusy=false;
                            if(isFinishing() || isDestroyed()){file.delete();return;}
                            try{
                                pendingExport=true;
                                Intent intent=settingsPicker(Intent.ACTION_CREATE_DOCUMENT);
                                intent.putExtra(Intent.EXTRA_TITLE,"consumer-law-settings.json");startActivityForResult(intent,EXPORT_SETTINGS);
                            }catch(Exception ex){pendingExport=false;file.delete();Toast.makeText(this,"בחירת קובץ אינה זמינה",Toast.LENGTH_LONG).show();}
                        });
                    }catch(Exception ex){file.failWrite(output);runOnUiThread(()->{settingsBusy=false;Toast.makeText(this,"לא ניתן ליצור גיבוי",Toast.LENGTH_LONG).show();});}
                },"settings-prepare-export").start();
            }catch(Exception ex){settingsBusy=false;Toast.makeText(this,"לא ניתן ליצור גיבוי",Toast.LENGTH_LONG).show();}
        });
    }
    private AtomicFile pendingExportFile(){return new AtomicFile(new File(getCacheDir(),"pending-settings-export.json"));}
    private Intent settingsPicker(String action){
        Uri start=settingsPickerLocation;
        // Oreo's Downloads provider does not list every local raw document.
        // The storage provider lists the actual folder, including older backups.
        if(start==null||"com.android.providers.downloads.documents".equals(start.getAuthority()))
            start=android.provider.DocumentsContract.buildDocumentUri("com.android.externalstorage.documents","primary:Download");
        return new Intent(action).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json")
            .putExtra(android.provider.DocumentsContract.EXTRA_INITIAL_URI,start);
    }
    private void beginImport() {
        try{
            Intent picker=settingsPicker(Intent.ACTION_OPEN_DOCUMENT).setType("*/*");
            // Older document providers classify .json as generic binary or text.
            // MIME is only a picker hint; UTF-8, size and schema remain mandatory.
            picker.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/json","text/json","text/plain","application/octet-stream"});
            startActivityForResult(picker,IMPORT_SETTINGS);
        }
        catch(Exception ex){Toast.makeText(this,"בחירת קובץ אינה זמינה",Toast.LENGTH_LONG).show();}
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK || data==null || data.getData()==null){if(request==EXPORT_SETTINGS){pendingExport=false;pendingExportFile().delete();}return;}
        final Uri uri=data.getData();
        if(!"content".equals(uri.getScheme())||uri.toString().length()>4096){
            if(request==EXPORT_SETTINGS){pendingExport=false;pendingExportFile().delete();}
            Toast.makeText(this,"כתובת הקובץ אינה תקינה",Toast.LENGTH_LONG).show();return;
        }
        if(request==EXPORT_SETTINGS||request==IMPORT_SETTINGS)settingsPickerLocation=uri;
        if(request==EXPORT_SETTINGS){
            if(!pendingExport)return;pendingExport=false;settingsBusy=true;
            new Thread(() -> {try{
                    byte[] contents=readBounded(pendingExportFile().openRead(),MAX_BACKUP);
                    try(OutputStream output=getContentResolver().openOutputStream(uri,"wt")){if(output==null)throw new IOException();output.write(contents);}
                    runOnUiThread(()->Toast.makeText(this,"הגיבוי נשמר",Toast.LENGTH_LONG).show());
                }catch(Exception ex){runOnUiThread(()->Toast.makeText(this,"שמירת הגיבוי נכשלה",Toast.LENGTH_LONG).show());}
                finally{pendingExportFile().delete();runOnUiThread(()->settingsBusy=false);}},"settings-export").start();
        }else if(request==IMPORT_SETTINGS){
            new Thread(() -> {try{final String raw=java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT).onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                    .decode(java.nio.ByteBuffer.wrap(readBounded(getContentResolver().openInputStream(uri),MAX_BACKUP))).toString();runOnUiThread(()->previewImport(raw));}
                catch(Exception ex){runOnUiThread(()->Toast.makeText(this,"קריאת הגיבוי נכשלה או שהקובץ גדול מדי",Toast.LENGTH_LONG).show());}},"settings-import").start();
        }
    }
    private void previewImport(final String raw) {
        if(!trusted())return;
        web.evaluateJavascript("window.lawSettings.prepareImport("+JSONObject.quote(raw)+")",result -> {
            try{JSONObject preview=new JSONObject(result);if(!preview.optBoolean("ok")){new AlertDialog.Builder(this).setMessage(preview.optString("error")).setPositiveButton("אישור",null).show();return;}
                new AlertDialog.Builder(this).setTitle("שחזור הגדרות").setMessage(preview.getString("preview"))
                    .setNegativeButton("ביטול",null).setPositiveButton("החלפת ההגדרות",(d,w)-> {
                        if(!trusted())return;
                        web.evaluateJavascript("window.lawSettings.applyImport("+JSONObject.quote(raw)+")",applied -> {
                            try{JSONObject status=new JSONObject(applied);if(status.optBoolean("ok"))web.reload();else Toast.makeText(this,status.optString("error"),Toast.LENGTH_LONG).show();}
                            catch(Exception ex){Toast.makeText(this,"השחזור נכשל",Toast.LENGTH_LONG).show();}
                        });
                    }).show();
            }catch(Exception ex){Toast.makeText(this,"קובץ הגיבוי אינו תקין",Toast.LENGTH_LONG).show();}
        });
    }
    @Override public void onBackPressed() { handleBack(); }
    private void handleBack() {
        if(web==null){finish();return;}
        final WebView current=web;
        current.evaluateJavascript("Boolean(window.lawMobileBack && window.lawMobileBack())",new ValueCallback<String>() {
            @Override public void onReceiveValue(String result) {
                if(web!=current || isFinishing() || isDestroyed())return;
                if ("true".equals(result)) return;
                if (web.canGoBack()) web.goBack(); else if(Build.VERSION.SDK_INT>=31)moveTaskToBack(true);else finish();
            }
        });
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        if(web!=null){Bundle history=new Bundle();if(web.saveState(history)!=null){String reference=webStateCache.write(history);if(reference!=null)state.putString(WebViewStateCache.KEY,reference);}}
        state.putBoolean("pendingExport",pendingExport);
        if(settingsPickerLocation!=null)state.putString("settingsPickerLocation",settingsPickerLocation.toString());
        super.onSaveInstanceState(state);
    }
    @Override protected void onPause() { if(web!=null){web.evaluateJavascript("window.lawMobile?.saveSession()",null);web.onPause();}super.onPause(); }
    @Override protected void onResume() { super.onResume();if(web!=null)web.onResume(); }
    @Override protected void onDestroy() { if(Build.VERSION.SDK_INT>=33&&systemBack!=null)getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(systemBack);if(web!=null){web.removeJavascriptInterface("NativeLaw");web.destroy();}super.onDestroy(); }
}
