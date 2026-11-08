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
import android.provider.DocumentsContract;
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
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/** All legal content is bundled; external publications open in the user's browser. */
public final class MainActivity extends Activity {
    private static final String HOST = "law.local";
    private static final String HOME = "https://" + HOST + "/index.html";
    private WebView web;
    private boolean ready;
    private String pendingExport;
    private static final int EXPORT_SETTINGS = 2101, IMPORT_SETTINGS = 2102;
    private static final int MAX_BACKUP = 1000000;

    /**
     * Only the three canonical HTTPS snapshot locations may be reached from the
     * bundled legal document. External scripts, images, frames and arbitrary
     * fetch destinations remain blocked by the local asset interceptor.
     */
    private static boolean isApprovedDateSource(Uri uri) {
        if (uri == null || !"https".equals(uri.getScheme()) || uri.getPort() != -1 || uri.getUserInfo() != null || uri.getFragment() != null) return false;
        String host = uri.getHost();
        String path = uri.getPath();
        for (String key : uri.getQueryParameterNames()) {
            if ("_t".equals(key)) { if (!uri.getQueryParameter(key).matches("[0-9]{1,16}")) return false; }
            else if (!("ref".equals(key) && "api.github.com".equals(host) && "main".equals(uri.getQueryParameter(key)))) return false;
            if (uri.getQueryParameters(key).size() != 1) return false;
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
        if(savedInstanceState!=null)pendingExport=savedInstanceState.getString("pendingExport");
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
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
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
                view.evaluateJavascript("document.documentElement.dataset.lawReady === 'true'",result -> ready="true".equals(result));
            }
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error) {
                if(request.isForMainFrame()) { ready=false; showLoadError(); }
            }
            @Override public boolean onRenderProcessGone(WebView view,RenderProcessGoneDetail detail) {
                ready=false;
                new AlertDialog.Builder(MainActivity.this).setMessage("תהליך הקריאה נסגר. ההעדפות נשמרו; אפשר לפתוח מחדש.")
                    .setPositiveButton("פתיחה מחדש",(d,w)->recreate()).setCancelable(false).show();
                ((android.view.ViewGroup)view.getParent()).removeView(view);view.destroy();web=null;return true;
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!isLocalDocument(uri)) {
                    // A null response allows WebView to perform its normal CORS
                    // fetch. All non-allowlisted external resources stay denied.
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
        if (savedInstanceState == null || web.restoreState(savedInstanceState)==null) web.loadUrl(HOME);
    }

    private void showLoadError() {
        new AlertDialog.Builder(this).setMessage("טעינת נוסח החוק המקומי נכשלה.")
            .setPositiveButton("ניסיון נוסף",(d,w)->web.loadUrl(HOME)).setNegativeButton("ביטול",null).show();
    }
    private boolean trusted() {
        if(web==null || !ready || web.getUrl()==null)return false;
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
        @JavascriptInterface public void exportSettings() { runOnUiThread(() -> { if(trusted())beginExport(); }); }
        @JavascriptInterface public void importSettings() { runOnUiThread(() -> { if(trusted())beginImport(); }); }
        @JavascriptInterface public void share(final String url) { runOnUiThread(() -> {
            if(!trusted() || url==null || url.length()>2048 || !url.startsWith("https://sargon17-green.github.io/consumer-law-reader/#"))return;
            try{startActivity(Intent.createChooser(new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,url),"שיתוף קישור לסעיף"));}
            catch(Exception ex){Toast.makeText(MainActivity.this,"השיתוף אינו זמין",Toast.LENGTH_LONG).show();}
        }); }
        @JavascriptInterface public void copy(final String text) {
            runOnUiThread(() -> {
                if(!trusted() || text==null || text.length()>1000000)return;
                ClipboardManager clipboard = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(ClipData.newPlainText("חוק הגנת הצרכן, התשמ\"א–1981",text==null?"":text));
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
        web.evaluateJavascript("window.lawSettings.exportJSON()",result -> {
            try {
                Object value=new JSONTokener(result).nextValue();
                if(!(value instanceof String) || ((String)value).getBytes("UTF-8").length>MAX_BACKUP)throw new Exception();
                pendingExport=(String)value;
                Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json");
                intent.putExtra(Intent.EXTRA_TITLE,"consumer-law-settings.json");startActivityForResult(intent,EXPORT_SETTINGS);
            }catch(Exception ex){pendingExport=null;Toast.makeText(this,"לא ניתן ליצור גיבוי",Toast.LENGTH_LONG).show();}
        });
    }
    private void beginImport() {
        try{startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json"),IMPORT_SETTINGS);}
        catch(Exception ex){Toast.makeText(this,"בחירת קובץ אינה זמינה",Toast.LENGTH_LONG).show();}
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK || data==null || data.getData()==null){if(request==EXPORT_SETTINGS)pendingExport=null;return;}
        final Uri uri=data.getData();
        if(request==EXPORT_SETTINGS){
            final String contents=pendingExport;pendingExport=null;if(contents==null)return;
            new Thread(() -> {try(OutputStream output=getContentResolver().openOutputStream(uri,"wt")){if(output==null)throw new IOException();output.write(contents.getBytes("UTF-8"));runOnUiThread(()->Toast.makeText(this,"הגיבוי נשמר",Toast.LENGTH_LONG).show());}
                catch(Exception ex){runOnUiThread(()->Toast.makeText(this,"שמירת הגיבוי נכשלה",Toast.LENGTH_LONG).show());}},"settings-export").start();
        }else if(request==IMPORT_SETTINGS){
            new Thread(() -> {try{final String raw=new String(readBounded(getContentResolver().openInputStream(uri),MAX_BACKUP),"UTF-8");runOnUiThread(()->previewImport(raw));}
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
    @Override public void onBackPressed() {
        if(web==null){super.onBackPressed();return;}
        web.evaluateJavascript("Boolean(window.lawMobileBack && window.lawMobileBack())",new ValueCallback<String>() {
            @Override public void onReceiveValue(String result) {
                if ("true".equals(result)) return;
                if (web.canGoBack()) web.goBack(); else MainActivity.super.onBackPressed();
            }
        });
    }
    @Override protected void onSaveInstanceState(Bundle state) { if(web!=null)web.saveState(state);if(pendingExport!=null)state.putString("pendingExport",pendingExport);super.onSaveInstanceState(state); }
    @Override protected void onPause() { if(web!=null){web.evaluateJavascript("window.lawMobile?.saveSession()",null);web.onPause();}super.onPause(); }
    @Override protected void onResume() { super.onResume();if(web!=null)web.onResume(); }
    @Override protected void onDestroy() { if(web!=null){web.removeJavascriptInterface("NativeLaw");web.destroy();}super.onDestroy(); }
}
