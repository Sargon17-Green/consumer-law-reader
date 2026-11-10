package il.org.lawreader.consumer;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.os.Build;
import android.os.Bundle;
import android.os.Parcel;
import android.util.AtomicFile;
import android.webkit.WebView;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.UUID;

/** Transient opaque WebView history: Binder receives a small reference only.
 * Parcel is not portable storage. Cached bytes require the exact same OS,
 * app installation and provider installation; other versions use the durable
 * logical reading session instead. Durable user preferences are stored separately.
 */
final class WebViewStateCache {
    static final String KEY="lawWebStateToken";
    private static final int MAX_BYTES=8*1024*1024,MAGIC=0x4c575331;
    private final File directory;
    private final String signature;
    private String token;
    WebViewStateCache(Context context) {
        directory=new File(context.getCacheDir(),"reader-web-state");
        String identity=null;
        try {
            PackageInfo app=context.getPackageManager().getPackageInfo(context.getPackageName(),0);
            PackageInfo provider=WebView.getCurrentWebViewPackage();
            if(provider!=null)identity=Build.FINGERPRINT+"\n"+app.packageName+":"+app.lastUpdateTime+"\n"+provider.packageName+":"+provider.versionName+":"+provider.lastUpdateTime;
        }catch(Exception unavailable){ /* Durable local reading remains available. */ }
        signature=identity;
    }
    private static boolean validToken(String value) {return value!=null&&value.matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}");}
    private static String hex(byte[] bytes) {StringBuilder value=new StringBuilder();for(byte b:bytes)value.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return value.toString();}
    private AtomicFile file(String value) {return new AtomicFile(new File(directory,value+".bin"));}
    String write(Bundle history) {
        if(signature==null)return null;
        Parcel parcel=Parcel.obtain();FileOutputStream stream=null;AtomicFile target=null;
        try {
            history.writeToParcel(parcel,0);if(parcel.dataSize()>MAX_BYTES)return null;
            byte[] bytes=parcel.marshall(),digest=MessageDigest.getInstance("SHA-256").digest(bytes);
            if(!directory.isDirectory()&&!directory.mkdirs())return null;
            if(token==null)token=UUID.randomUUID().toString();
            target=file(token);stream=target.startWrite();DataOutputStream data=new DataOutputStream(stream);
            data.writeInt(MAGIC);data.writeUTF(signature);data.writeInt(bytes.length);data.write(digest);data.write(bytes);data.flush();
            target.finishWrite(stream);stream=null;prune();
            // The reference digest also rejects an older file if a final atomic
            // rename fails. Corrupt/missing cache never replaces durable data.
            return token+":"+hex(digest);
        }catch(Exception failure){if(target!=null&&stream!=null)target.failWrite(stream);return null;}
        finally{parcel.recycle();}
    }
    Bundle read(String reference) {
        if(signature==null||reference==null||reference.length()!=101||reference.charAt(36)!=':')return null;
        String value=reference.substring(0,36),expected=reference.substring(37);
        if(!validToken(value)||!expected.matches("[0-9a-f]{64}"))return null;
        Parcel parcel=Parcel.obtain();
        try(InputStream input=file(value).openRead();ByteArrayOutputStream buffer=new ByteArrayOutputStream()) {
            byte[] block=new byte[16384];int count,total=0;
            while((count=input.read(block))!=-1){total+=count;if(total>MAX_BYTES+16384)return null;buffer.write(block,0,count);}
            DataInputStream data=new DataInputStream(new ByteArrayInputStream(buffer.toByteArray()));
            if(data.readInt()!=MAGIC||!signature.equals(data.readUTF()))return null;
            int length=data.readInt();if(length<=0||length>MAX_BYTES||data.available()!=length+32)return null;
            byte[] digest=new byte[32],bytes=new byte[length];data.readFully(digest);data.readFully(bytes);
            if(!expected.equals(hex(digest))||!MessageDigest.isEqual(digest,MessageDigest.getInstance("SHA-256").digest(bytes)))return null;
            parcel.unmarshall(bytes,0,bytes.length);parcel.setDataPosition(0);
            Bundle history=parcel.readBundle(WebView.class.getClassLoader());if(history==null)return null;
            history.size();token=value;return history;
        }catch(Exception invalid){return null;}
        finally{parcel.recycle();}
    }
    private void prune() {
        File[] entries=directory.listFiles();if(entries==null)return;
        long old=System.currentTimeMillis()-24*60*60*1000L;
        for(File entry:entries){String name=entry.getName();if(name.matches("[0-9a-f-]{36}\\.bin\\.(new|bak)")&&entry.lastModified()<old)entry.delete();}
        File[] files=directory.listFiles((parent,name)->name.endsWith(".bin")&&validToken(name.substring(0,name.length()-4)));
        if(files==null)return;Arrays.sort(files,(a,b)->Long.compare(b.lastModified(),a.lastModified()));
        for(int i=4;i<files.length;i++)if(!files[i].getName().equals(token+".bin"))new AtomicFile(files[i]).delete();
    }
}
