package il.org.lawreader.consumer;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStream;

/** Read-only access to the Word attachment bundled with the user's source. */
public final class AttachmentProvider extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    private String name(Uri uri) throws FileNotFoundException {
        if (uri.getPathSegments().size()!=1) throw new FileNotFoundException();
        String name=uri.getLastPathSegment();
        if(name==null||!name.endsWith(".doc")||name.contains("/")||name.contains("\\")||name.contains(".."))throw new FileNotFoundException();
        return name;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        if(!"r".equals(mode))throw new FileNotFoundException("Read only");
        String name=name(uri);
        File dir=new File(getContext().getCacheDir(),"attachments");
        dir.mkdirs();
        File file=new File(dir,name);
        try(InputStream input=getContext().getAssets().open("www/"+name);FileOutputStream output=new FileOutputStream(file)){
            byte[] buffer=new byte[16384];int n;
            while((n=input.read(buffer))!=-1)output.write(buffer,0,n);
        }catch(Exception ex){throw new FileNotFoundException(name);}
        return ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public String getType(Uri uri){return "application/msword";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String sort){
        try{
            String name=name(uri);
            long length=getContext().getAssets().openFd("www/"+name).getLength();
            String[] columns=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;
            MatrixCursor cursor=new MatrixCursor(columns);
            MatrixCursor.RowBuilder row=cursor.newRow();
            for(String column:columns)row.add(OpenableColumns.DISPLAY_NAME.equals(column)?name:OpenableColumns.SIZE.equals(column)?length:null);
            return cursor;
        }catch(Exception ex){return null;}
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Read only");}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException("Read only");}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException("Read only");}
}
