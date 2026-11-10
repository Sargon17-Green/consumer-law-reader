import Foundation
import CoreGraphics
import PDFKit
guard CommandLine.arguments.count == 3,
      let expected=Int(CommandLine.arguments[2]),
      let pdf=PDFDocument(url:URL(fileURLWithPath:CommandLine.arguments[1])),
      let document=CGPDFDocument(URL(fileURLWithPath:CommandLine.arguments[1]) as CFURL),
      document.numberOfPages == expected, pdf.pageCount == expected,
      expected>10, expected<2000 else { fatalError("Actual saved PDF does not match full system preview") }
var samples=[[String:Any]]()
for index in Set([1,expected/2+1,expected]).sorted() {
    guard let page=document.page(at:index) else { fatalError("Missing PDF page") }
    let width=120,height=170
    var pixels=[UInt8](repeating:255,count:width*height*4)
    let ink=pixels.withUnsafeMutableBytes { raw -> Int in
        guard let context=CGContext(data:raw.baseAddress,width:width,height:height,bitsPerComponent:8,bytesPerRow:width*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else { return 0 }
        context.setFillColor(CGColor(gray:1,alpha:1));context.fill(CGRect(x:0,y:0,width:width,height:height))
        context.concatenate(page.getDrawingTransform(.mediaBox,rect:CGRect(x:0,y:0,width:width,height:height),rotate:0,preserveAspectRatio:true))
        context.drawPDFPage(page)
        let bytes=raw.bindMemory(to:UInt8.self)
        return stride(from:0,to:bytes.count,by:4).filter{bytes[$0+3]>200 && (bytes[$0]<220 || bytes[$0+1]<220 || bytes[$0+2]<220)}.count
    }
    guard ink>2 else { fatalError("Blank saved PDF page \(index)") }
    samples.append(["page":index,"ink":ink,"textCharacters":pdf.page(at:index-1)?.string?.count ?? 0])
}
let report:[String:Any]=["schema":1,"result":"PASS","pages":expected,"samples":samples,"scope":"Actual system Files-save output, full page count and first/mid/last raster ink; not a physical printer or tagged-PDF audit"]
let data=try JSONSerialization.data(withJSONObject:report,options:[.sortedKeys])
print(String(data:data,encoding:.utf8)!)
