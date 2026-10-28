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

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
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
        settings.setTextZoom(100);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        web.addJavascriptInterface(new LocalBridge(), "NativeLaw");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return request.isForMainFrame() ? handleNavigation(request.getUrl()) : !isLocalDocument(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleNavigation(Uri.parse(url));
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!"https".equals(uri.getScheme()) || !HOST.equals(uri.getHost()) || uri.getPort() != -1) return missing();
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
                            "default-src 'self'; script-src 'self' 'unsafe-inline'; " +
                            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; " +
                            "font-src 'self' data:; connect-src 'none'; frame-src 'none'; " +
                            "object-src 'none'; base-uri 'none'; form-action 'none'");
                    }
                    return new WebResourceResponse(mime,"UTF-8",200,"OK",headers,getAssets().open("www"+path));
                } catch (IOException ex) { return missing(); }
            }
        });
        root.addView(web,new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
        if (savedInstanceState == null || web.restoreState(savedInstanceState)==null) web.loadUrl(HOME);
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
        return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && uri.getPort() == -1;
    }
    private boolean handleNavigation(Uri uri) {
        if (isLocalDocument(uri)) {
            if (uri.getPath()!=null && uri.getPath().endsWith(".doc")) {
                openAttachment(uri.getLastPathSegment());
                return true;
            }
            return false;
        }
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
        @JavascriptInterface public void copy(final String text) {
            runOnUiThread(() -> {
                ClipboardManager clipboard = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(ClipData.newPlainText("חוק הגנת הצרכן, התשמ"א–1981",text==null?"":text));
            });
        }
        @JavascriptInterface public void openAttachment(final String name) { runOnUiThread(() -> MainActivity.this.openAttachment(name)); }
        @JavascriptInterface public void printDocument() {
            runOnUiThread(() -> {
                PrintManager manager = (PrintManager)getSystemService(PRINT_SERVICE);
                manager.print("חוק הגנת הצרכן, התשמ"א–1981",web.createPrintDocumentAdapter("חוק הגנת הצרכן, התשמ"א–1981"),null);
            });
        }
    }
    @Override public void onBackPressed() {
        web.evaluateJavascript("Boolean(window.lawMobileBack && window.lawMobileBack())",new ValueCallback<String>() {
            @Override public void onReceiveValue(String result) {
                if ("true".equals(result)) return;
                if (web.canGoBack()) web.goBack(); else MainActivity.super.onBackPressed();
            }
        });
    }
    @Override protected void onSaveInstanceState(Bundle state) { web.saveState(state);super.onSaveInstanceState(state); }
    @Override protected void onPause() { web.onPause();super.onPause(); }
    @Override protected void onResume() { super.onResume();if(web!=null)web.onResume(); }
    @Override protected void onDestroy() { if(web!=null){web.removeJavascriptInterface("NativeLaw");web.destroy();}super.onDestroy(); }
}
