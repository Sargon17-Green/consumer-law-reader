package il.org.lawreader.consumer.qa;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import java.io.InputStream;
import java.security.MessageDigest;
/** Controlled cross-UID consumer: verifies the real OS URI grant and provider bytes. */
public final class AttachmentReceiver extends Activity {
    @Override public void onCreate(Bundle state){
        super.onCreate(state);Intent result=new Intent("il.org.lawreader.consumer.QA_ATTACHMENT").setPackage("il.org.lawreader.consumer");
        try(InputStream input=getContentResolver().openInputStream(getIntent().getData())){
            MessageDigest digest=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[16384];int n,total=0;
            while((n=input.read(buffer))!=-1){total+=n;if(total>5000000)throw new Exception("Attachment limit");digest.update(buffer,0,n);}
            StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format("%02x",b&255));
            result.putExtra("sha256",hex.toString());result.putExtra("bytes",total);
        }catch(Exception error){result.putExtra("error",error.toString());}
        sendBroadcast(result);finish();
    }
}
