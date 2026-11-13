package il.org.lawreader.consumer.qa;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
/** A controlled destination selected through the real Android sharesheet. */
public final class ShareReceiver extends Activity {
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        sendBroadcast(new Intent("il.org.lawreader.consumer.QA_SHARE")
            .setPackage("il.org.lawreader.consumer")
            .putExtra("text",getIntent().getStringExtra(Intent.EXTRA_TEXT)));
        finish();
    }
}
