import XCTest
import WebKit
import UIKit
@testable import ConsumerLawReader

private final class NativeGuardProbe: NSObject, WKScriptMessageHandler {
    var attempted=false
    func userContentController(_ controller: WKUserContentController,didReceive message: WKScriptMessage) {
        attempted = !message.frameInfo.isMainFrame
    }
}

@MainActor
private final class ReaderScriptReply {
    private var continuation: CheckedContinuation<Any, Error>?
    init(_ continuation: CheckedContinuation<Any, Error>) { self.continuation=continuation }
    func finish(_ result: Result<Any, Error>) {
        guard let continuation else { return }
        self.continuation=nil
        continuation.resume(with:result)
    }
}

@MainActor
private final class ReaderPDFRenderer: UIPrintPageRenderer {
    override var paperRect: CGRect { CGRect(x:0,y:0,width:595,height:842) }
    override var printableRect: CGRect { paperRect.insetBy(dx:24,dy:24) }
}

final class ReaderPolicyTests: XCTestCase {
    func testBuiltAppDeclaresAdaptiveIPadOrientations() throws {
        // Bundle.infoDictionary can resolve device-specific overrides into the
        // generic key. Read the actual packaged plist to verify both wire keys.
        let url=try XCTUnwrap(Bundle.main.url(forResource:"Info",withExtension:"plist"))
        let values=try XCTUnwrap(PropertyListSerialization.propertyList(from:Data(contentsOf:url),options:[],format:nil) as? [String:Any])
        let orientations=try XCTUnwrap(values["UISupportedInterfaceOrientations"] as? [String])
        XCTAssertEqual(Set(orientations),Set(["UIInterfaceOrientationPortrait","UIInterfaceOrientationLandscapeLeft","UIInterfaceOrientationLandscapeRight"]))
        let iPad=try XCTUnwrap((values["UISupportedInterfaceOrientations~ipad"] ?? values["UISupportedInterfaceOrientations~iPad"]) as? [String])
        XCTAssertEqual(Set(iPad),Set(["UIInterfaceOrientationPortrait","UIInterfaceOrientationPortraitUpsideDown","UIInterfaceOrientationLandscapeLeft","UIInterfaceOrientationLandscapeRight"]))
        XCTAssertNotEqual(values["UIRequiresFullScreen"] as? Bool,true)
    }

    func testDateURLsAndHostileInputs() throws {
        for (host,path) in ReaderPolicy.datePaths {
            XCTAssertTrue(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string: "https://" + host + path + "?_t=123"))))
            for bad in ["http://" + host + path, "https://" + host + ".invalid" + path,
                        "https://user@" + host + path, "https://" + host + ":8443" + path,
                        "https://" + host + path + "?ref=evil", "https://" + host + path + "/extra",
                        "https://" + host + path + "?_t=1&_t=2",
                        "https://" + host + path + "?_t=1&",
                        "https://" + host + path + "?%5Ft=1",
                        "https://" + host + path + "?_t=%31",
                        "https://" + host + path + "?ref=main&r%65f=other",
                        "https://" + host + path.replacingOccurrences(of:"seer-now",with:"seer%2Dnow"),
                        "https://" + host + path + "?_t=12345678901234567"] {
                XCTAssertFalse(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string: bad))), bad)
            }
        }
        XCTAssertTrue(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string:"https://api.github.com/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json?ref=main&_t=123"))))
        XCTAssertFalse(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string:"https:opaque?x=1"))))
        let website=URL(fileURLWithPath:"/app/dist/index.html")
        XCTAssertTrue(ReaderPolicy.isBundledDocument(website,website:website))
        XCTAssertFalse(ReaderPolicy.isBundledDocument(URL(fileURLWithPath:"/app/dist/other.html"),website:website))
        XCTAssertFalse(ReaderPolicy.isBundledDocument(URL(fileURLWithPath:"/app/dist/../secret.html"),website:website))
        XCTAssertFalse(ReaderPolicy.isExternalLink(try XCTUnwrap(URL(string:"javascript:alert(1)"))))
    }
}

@MainActor
final class ReaderIntegrationTests: XCTestCase {
    private var testWindow: UIWindow?
    private func closeTestWindow() {
        testWindow?.isHidden=true
        testWindow?.rootViewController=nil
        testWindow=nil
    }
    private func script(_ reader: OfflineLawReader,_ source: String) async throws -> Any {
        try await script(reader.webView,source)
    }
    private func script(_ webView: WKWebView,_ source: String) async throws -> Any {
        try await withCheckedThrowingContinuation { continuation in
            let reply=ReaderScriptReply(continuation)
            let deadline=Task { @MainActor in
                do { try await Task.sleep(nanoseconds:20_000_000_000) } catch { return }
                reply.finish(.failure(NSError(domain:"ReaderQA.JavaScript",code:1,userInfo:[NSLocalizedDescriptionKey:"JavaScript timeout: "+String(source.prefix(160))])))
            }
            webView.callAsyncJavaScript("return await (" + source + ");", arguments: [:], in: nil, in: .page) { result in
                Task { @MainActor in
                    deadline.cancel()
                    reply.finish(result)
                }
            }
        }
    }
    private func openReader() async throws -> OfflineLawReader {
        let reader=OfflineLawReader()
        let scene=try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let window=UIWindow(windowScene:scene)
        let controller=UIViewController()
        window.rootViewController=controller
        window.makeKeyAndVisible()
        controller.loadViewIfNeeded()
        reader.webView.translatesAutoresizingMaskIntoConstraints=false
        controller.view.addSubview(reader.webView)
        NSLayoutConstraint.activate([
            reader.webView.topAnchor.constraint(equalTo:controller.view.topAnchor),
            reader.webView.bottomAnchor.constraint(equalTo:controller.view.bottomAnchor),
            reader.webView.leadingAnchor.constraint(equalTo:controller.view.leadingAnchor),
            reader.webView.trailingAnchor.constraint(equalTo:controller.view.trailingAnchor)
        ])
        controller.view.layoutIfNeeded()
        testWindow=window
        XCTAssertGreaterThan(reader.webView.bounds.width,0,"Navigation assertions require a displayed native web view")
        for _ in 0..<240 {
            if reader.ready { return reader }
            try await Task.sleep(nanoseconds:250_000_000)
        }
        XCTFail("Actual WKWebView did not reach application readiness")
        throw NSError(domain:"ReaderQA",code:1)
    }
    func testReadingLayoutInActualWKWebView() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        let resource=try XCTUnwrap(Bundle(for:ReaderIntegrationTests.self).url(forResource:"reader_layout_probe",withExtension:"js"))
        let probe=try String(contentsOf:resource,encoding:.utf8)
        let options="{sizes:[18,28,48],regulationIds:['used_vehicle_trading_regulations','Calculation_of_annual_interest_rate','Calculation_of_annual_interest_rate_2','Disclosure_of_material_detail_regarding_diamonds_gems_pearls_and_gold_products']}"
        let result=try await script(reader,"JSON.stringify(("+probe+")("+options+"))") as? String
        let data=try XCTUnwrap(result?.data(using:.utf8))
        let report=try XCTUnwrap(JSONSerialization.jsonObject(with:data) as? [String:Any])
        XCTAssertEqual(report["regulations"] as? Int,4)
        XCTAssertEqual((report["issues"] as? [Any])?.count,0,result ?? "No result")
        let attachment=XCTAttachment(data:data,uniformTypeIdentifier:"public.json")
        attachment.name="Actual WKWebView responsive layout";attachment.lifetime = .keepAlways;add(attachment)
        _ = try await script(reader,"(lawMobile.goTo('article_14',false,false),true)")
        try await Task.sleep(nanoseconds:300_000_000)
        XCTAssertLessThanOrEqual(reader.webView.scrollView.contentSize.width,reader.webView.bounds.width+1,"The native scroll view must fit the screen at the default zoom")
        print("NATIVE_READING_LAYOUT: \(result ?? "missing")")
    }
    func testActualOfflineReaderSearchBackupAndLifecycle() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        if ProcessInfo.processInfo.environment["EXPECT_SEER_FRESH"] == "true" {
            var rendered=false
            for _ in 0..<220 {
                let text=try await script(reader,"document.getElementById('pastafari_current_date_text').textContent") as? String ?? ""
                if text.hasPrefix("התאריך הפסטפרי היום:"){rendered=true;break}
                try await Task.sleep(nanoseconds:250_000_000)
            }
            XCTAssertTrue(rendered,"Fresh upstream date must pass the real WKWebView resource and CORS policy")
        }
        let report=try await script(reader,"""
        (()=>{
          const check=(x,m)=>{if(!x)throw Error(m)};
          check(lawMobile.buildSearch().length>500,'full law index');
          check(LawCore.snippet('אָב שָׁלוֹם סוף','שלום').mark==='שָׁלוֹם','Hebrew span');
          localStorage.setItem('outside-backup','keep');
          localStorage.setItem('law-reader-font','24');
          localStorage.removeItem('law-reader-align');
          const backup=lawSettings.exportJSON();
          localStorage.setItem('law-reader-align','right');
          check(lawSettings.prepareImport(backup).ok,'preview');
          check(lawSettings.applyImport(backup).ok,'restore');
          check(localStorage.getItem('law-reader-align')===null,'remove stale');
          check(localStorage.getItem('outside-backup')==='keep','preserve unrelated');
          check(!lawSettings.prepareImport('{"schema":99}').ok,'reject invalid');
          lawMobile.goTo('article_14');
          lawMobile.saveSession();
          return location.hash;
        })()
        """)
        XCTAssertEqual(report as? String,"#article_14")
        let savedPosition = try await script(reader,"(()=>{lawMobile.goTo('article_2');scrollBy(0,100);const p=scrollY;lawMobile.goTo('article_3');return p})()") as? Double
        // pushState runs in the WebContent process; wait until the native
        // history list has received it before asking the UI process to go Back.
        for _ in 0..<50 {
            if reader.webView.backForwardList.currentItem?.url.fragment == "article_3" { break }
            try await Task.sleep(nanoseconds:100_000_000)
        }
        XCTAssertEqual(reader.webView.backForwardList.currentItem?.url.fragment,"article_3")
        let beforeBack = try await script(reader,"JSON.stringify({hash:location.hash,scroll:scrollY,state:history.state,length:history.length})")
        print("NATIVE_BACK_BEFORE: \(beforeBack)")
        reader.webView.goBack()
        // Require a settled position, not a transient matching frame before
        // WebKit finishes restoring its native scrolling snapshot.
        try await Task.sleep(nanoseconds:600_000_000)
        var backPosition: Double?
        for _ in 0..<50 {
            try await Task.sleep(nanoseconds:100_000_000)
            backPosition = try await script(reader,"scrollY") as? Double
            let hash = try await script(reader,"location.hash") as? String
            if hash == "#article_2", abs((backPosition ?? -1000) - (savedPosition ?? -2000)) < 3 { break }
        }
        let afterBack = try await script(reader,"JSON.stringify({hash:location.hash,scroll:scrollY,state:history.state,length:history.length})")
        print("NATIVE_BACK_AFTER: \(afterBack)")
        backPosition = try await script(reader,"scrollY") as? Double
        XCTAssertEqual(backPosition ?? -1000,savedPosition ?? -2000,accuracy:3)
        let backHash = try await script(reader,"location.hash") as? String
        XCTAssertEqual(backHash,"#article_2")
        _ = try await script(reader,"(lawMobile.goTo('article_14'),true)")
        reader.persistReadingState()
        reader.webView.reload()
        for _ in 0..<80 { try await Task.sleep(nanoseconds:250_000_000);if reader.ready { break } }
        let savedFont=try await script(reader,"localStorage.getItem('law-reader-font')") as? String
        let savedHash=try await script(reader,"location.hash") as? String
        XCTAssertEqual(savedFont,"24")
        XCTAssertEqual(savedHash,"#article_14")
        try await Task.sleep(nanoseconds:400_000_000)
        let visibleAfterReload=try await script(reader,"lawMobile.currentArticle()?.id") as? String
        XCTAssertEqual(visibleAfterReload,"article_14","Restoring pixels from another font size must not change the logical section")
        // The real native share path uses the current section's public URL.
        reader.shareCurrentSection()
        for _ in 0..<20 {if reader.sharing != nil{break};try await Task.sleep(nanoseconds:100_000_000)}
        let shared=try XCTUnwrap(reader.sharing?.items.first as? URL)
        XCTAssertEqual(shared.absoluteString,"https://sargon17-green.github.io/consumer-law-reader/reader/#article_14")
        reader.sharing=nil
        _ = try await script(reader,"(NativeLaw.copy('QA clipboard fixture'),true)")
        try await Task.sleep(nanoseconds:200_000_000)
        XCTAssertEqual(UIPasteboard.general.string,"QA clipboard fixture")
        let root=try XCTUnwrap(reader.webView.url?.deletingLastPathComponent())
        let attachment=try XCTUnwrap(FileManager.default.contentsOfDirectory(at:root,includingPropertiesForKeys:nil).first { $0.pathExtension == "doc" })
        let fileJSON=String(data:try JSONSerialization.data(withJSONObject:[attachment.lastPathComponent]),encoding:.utf8)!
        _ = try await script(reader,"(NativeLaw.openAttachment(" + String(fileJSON.dropFirst().dropLast()) + "),true)")
        for _ in 0..<20 {if reader.sharing != nil{break};try await Task.sleep(nanoseconds:100_000_000)}
        let opened=try XCTUnwrap(reader.sharing?.items.first as? URL)
        XCTAssertEqual(try Data(contentsOf:opened),try Data(contentsOf:attachment))
        reader.sharing=nil
        reader.exportSettings()
        for _ in 0..<40 {if reader.sharing != nil{break};try await Task.sleep(nanoseconds:100_000_000)}
        let url=try XCTUnwrap(reader.sharing?.items.first as? URL)
        XCTAssertLessThan(try Data(contentsOf:url).count,1_000_000)
        reader.sharing=nil
        reader.importBackup(result:.success([url]))
        for _ in 0..<40 {if reader.confirmImport{break};try await Task.sleep(nanoseconds:100_000_000)}
        XCTAssertTrue(reader.confirmImport)
        XCTAssertFalse(reader.importPreview.isEmpty)
        reader.cancelPendingImport()
        XCTAssertFalse(reader.confirmImport)
        reader.importBackup(result:.success([url]))
        for _ in 0..<40 {if reader.confirmImport{break};try await Task.sleep(nanoseconds:100_000_000)}
        XCTAssertTrue(reader.confirmImport)
        _ = try await script(reader,"(localStorage.setItem('law-reader-font','20'),true)")
        reader.applyPendingImport()
        for _ in 0..<120 {
            try await Task.sleep(nanoseconds:100_000_000)
            if !reader.working && reader.ready {break}
        }
        let restoredNativeFont=try await script(reader,"localStorage.getItem('law-reader-font')") as? String
        XCTAssertEqual(restoredNativeFont,"24")
        XCTAssertFalse(reader.confirmImport)
        reader.cleanTemporaryExport()
        XCTAssertFalse(FileManager.default.fileExists(atPath:url.path))
        let invalid=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".json")
        try Data([0x7B,0x22,0x78,0x22,0x3A,0x22,0xFF,0x22,0x7D]).write(to:invalid)
        defer { try? FileManager.default.removeItem(at:invalid) }
        reader.importBackup(result:.success([invalid]))
        for _ in 0..<40 {if !reader.working{break};try await Task.sleep(nanoseconds:100_000_000)}
        XCTAssertFalse(reader.confirmImport)
        XCTAssertNotNil(reader.notice)
    }
    func testShareCompletionPreservesNewerPresentationAndReportsFailure() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        let first=SharePayload(items:[try XCTUnwrap(URL(string:"https://sargon17-green.github.io/consumer-law-reader/reader/#article_14"))])
        reader.sharing=first
        reader.finishSharing(first.id,failure:nil)
        XCTAssertNil(reader.sharing,"Cancelling/completing the current share clears its SwiftUI presentation")
        let second=SharePayload(items:[try XCTUnwrap(URL(string:"https://sargon17-green.github.io/consumer-law-reader/reader/#article_2"))])
        reader.sharing=second
        reader.finishSharing(first.id,failure:"Delayed older activity error")
        XCTAssertEqual(reader.sharing?.id,second.id,"A stale completion cannot close a newer activity")
        XCTAssertNil(reader.notice,"An older activity must not present a misleading new error")
        reader.finishSharing(second.id,failure:"QA activity failure")
        XCTAssertNil(reader.sharing)
        XCTAssertTrue(reader.notice?.message.contains("QA activity failure") == true)
    }

    func testRemoteScriptsAndSubframeBridgeAreBlocked() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        let result=try await script(reader,"""
        (async()=>{
          let rejected=false;
          try{await fetch('https://example.com/should-never-load')}catch{rejected=true}
          const frame=document.createElement('iframe');
          frame.srcdoc='<script>parent.__untrustedExecuted=true;window.webkit.messageHandlers.lawReader.postMessage({type:"copy",text:"HOSTILE"})<'+ '/script>';
          document.body.append(frame);
          await new Promise(r=>setTimeout(r,500));frame.remove();
          return {blocked:rejected,frameExecuted:!!window.__untrustedExecuted};
        })()
        """) as? [String:Any]
        XCTAssertEqual(result?["blocked"] as? Bool,true)
        XCTAssertEqual(result?["frameExecuted"] as? Bool,false)
        _ = try await script(reader,"(NativeLaw.copy('TRUSTED_GUARD_QA'),true)")
        try await Task.sleep(nanoseconds:250_000_000)
        XCTAssertEqual(UIPasteboard.general.string,"TRUSTED_GUARD_QA")
        // The initial empty child window can expose message handlers without
        // loading a frame document. Verify an actual child-frame invocation.
        let probe=NativeGuardProbe()
        reader.webView.configuration.userContentController.add(probe,name:"readerQAProbe")
        defer { reader.webView.configuration.userContentController.removeScriptMessageHandler(forName:"readerQAProbe") }
        _ = try await script(reader,"(()=>{const frame=document.createElement('iframe');frame.id='qa-subframe';document.body.append(frame);const w=frame.contentWindow;w.webkit.messageHandlers.readerQAProbe.postMessage('attempted');w.webkit.messageHandlers.lawReader.postMessage({type:'copy',text:'HOSTILE_SUBFRAME'});return true})()")
        for _ in 0..<30 {if probe.attempted{break};try await Task.sleep(nanoseconds:100_000_000)}
        XCTAssertTrue(probe.attempted,"The instrumented subframe must actually attempt a native message")
        try await Task.sleep(nanoseconds:250_000_000)
        XCTAssertEqual(UIPasteboard.general.string,"TRUSTED_GUARD_QA")
        _ = try await script(reader,"(document.getElementById('qa-subframe').remove(),true)")
        // Reusing the controller in another real WKWebView must not confer the
        // original reader's native authority, even for the same bundled URL.
        let other=WKWebView(frame:reader.webView.bounds,configuration:reader.webView.configuration)
        defer {other.stopLoading()}
        let website=try XCTUnwrap(reader.webView.url)
        other.loadFileURL(website,allowingReadAccessTo:website.deletingLastPathComponent())
        var otherReady=false
        for _ in 0..<120 {
            try await Task.sleep(nanoseconds:100_000_000)
            if (try? await script(other,"document.documentElement.dataset.lawReady === 'true'")) as? Bool == true {otherReady=true;break}
        }
        XCTAssertTrue(otherReady)
        _ = try await script(other,"(NativeLaw.copy('HOSTILE_OTHER_WEBVIEW'),true)")
        try await Task.sleep(nanoseconds:250_000_000)
        XCTAssertEqual(UIPasteboard.general.string,"TRUSTED_GUARD_QA")
    }

    func testNativePrintFormatterProducesRenderablePDF() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        let renderer=ReaderPDFRenderer()
        renderer.addPrintFormatter(reader.webView.viewPrintFormatter(),startingAtPageAt:0)
        renderer.prepare(forDrawingPages:NSRange(location:0,length:1))
        XCTAssertGreaterThan(renderer.numberOfPages,0)
        let data=UIGraphicsPDFRenderer(bounds:renderer.paperRect).pdfData { context in
            context.beginPage()
            renderer.drawPage(at:0,in:renderer.paperRect)
        }
        XCTAssertTrue(data.starts(with:[0x25,0x50,0x44,0x46,0x2D]))
        let provider=try XCTUnwrap(CGDataProvider(data:data as CFData))
        let document=try XCTUnwrap(CGPDFDocument(provider))
        XCTAssertEqual(document.numberOfPages,1,"Bounded first-page print-output test")
        let page=try XCTUnwrap(document.page(at:1))
        let width=120,height=170
        var pixels=[UInt8](repeating:255,count:width*height*4)
        let ink=pixels.withUnsafeMutableBytes { raw -> Int in
            guard let context=CGContext(data:raw.baseAddress,width:width,height:height,bitsPerComponent:8,bytesPerRow:width*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else { return 0 }
            context.setFillColor(UIColor.white.cgColor)
            context.fill(CGRect(x:0,y:0,width:CGFloat(width),height:CGFloat(height)))
            context.scaleBy(x:CGFloat(width)/renderer.paperRect.width,y:CGFloat(height)/renderer.paperRect.height)
            context.drawPDFPage(page)
            let bytes=raw.bindMemory(to:UInt8.self)
            return stride(from:0,to:bytes.count,by:4).filter { bytes[$0+3]>200 && (bytes[$0]<220 || bytes[$0+1]<220 || bytes[$0+2]<220) }.count
        }
        XCTAssertGreaterThan(ink,20,"Native print output must contain opaque ink, not transparent or blank pixels")
        let attachment=XCTAttachment(data:data,uniformTypeIdentifier:"com.adobe.pdf")
        attachment.name="Actual UIKit print formatter — first page"
        attachment.lifetime = .keepAlways
        add(attachment)
        print("NATIVE_PDF_OUTPUT: pages=1 bytes=\(data.count) nonblank=true")
    }

    func testBundledReadingWithEveryRemoteRequestBlocked() async throws {
        let reader=try await openReader()
        defer { closeTestWindow() }
        let rule: WKContentRuleList = try await withCheckedThrowingContinuation { continuation in
            WKContentRuleListStore.default().compileContentRuleList(forIdentifier:"ReaderQAOffline",encodedContentRuleList:"[{\"trigger\":{\"url-filter\":\"^https?://\"},\"action\":{\"type\":\"block\"}}]") { rule,error in
                if let rule { continuation.resume(returning:rule) }
                else { continuation.resume(throwing:error ?? NSError(domain:"ReaderQA",code:2)) }
            }
        }
        reader.webView.configuration.userContentController.add(rule)
        reader.retryLoading()
        for _ in 0..<240 {try await Task.sleep(nanoseconds:250_000_000);if reader.ready{break}}
        XCTAssertTrue(reader.ready)
        let offline=try await script(reader,"""
        (async()=>{
          let blocked=false;
          try{await fetch('https://raw.githubusercontent.com/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json')}catch{blocked=true}
          return blocked && lawMobile.buildSearch().length>500 && lawMobile.goTo('article_14');
        })()
        """) as? Bool
        XCTAssertEqual(offline,true,"The actual WKWebView must read/search/navigate without any remote request")
    }
}
