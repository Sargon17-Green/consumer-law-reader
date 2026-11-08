import XCTest
import WebKit
@testable import ConsumerLawReader

final class ReaderPolicyTests: XCTestCase {
    func testDateURLsAndHostileInputs() throws {
        for (host,path) in ReaderPolicy.datePaths {
            XCTAssertTrue(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string: "https://" + host + path + "?_t=123"))))
            for bad in ["http://" + host + path, "https://" + host + ".invalid" + path,
                        "https://user@" + host + path, "https://" + host + ":8443" + path,
                        "https://" + host + path + "?ref=evil", "https://" + host + path + "/extra",
                        "https://" + host + path + "?_t=1&_t=2"] {
                XCTAssertFalse(ReaderPolicy.isDateURL(try XCTUnwrap(URL(string: bad))), bad)
            }
        }
        let website=URL(fileURLWithPath:"/app/dist/index.html")
        XCTAssertTrue(ReaderPolicy.isBundledDocument(website,website:website))
        XCTAssertFalse(ReaderPolicy.isBundledDocument(URL(fileURLWithPath:"/app/dist/other.html"),website:website))
        XCTAssertFalse(ReaderPolicy.isBundledDocument(URL(fileURLWithPath:"/app/dist/../secret.html"),website:website))
        XCTAssertFalse(ReaderPolicy.isExternalLink(try XCTUnwrap(URL(string:"javascript:alert(1)"))))
    }
}

@MainActor
final class ReaderIntegrationTests: XCTestCase {
    private func script(_ reader: OfflineLawReader,_ source: String) async throws -> Any {
        try await withCheckedThrowingContinuation { continuation in
            reader.webView.callAsyncJavaScript("return await (" + source + ");", arguments: [:], in: nil, in: .page) { result in
                continuation.resume(with: result)
            }
        }
    }
    private func openReader() async throws -> OfflineLawReader {
        let reader=OfflineLawReader()
        for _ in 0..<240 {
            if reader.ready { return reader }
            try await Task.sleep(nanoseconds:250_000_000)
        }
        XCTFail("Actual WKWebView did not reach application readiness")
        throw NSError(domain:"ReaderQA",code:1)
    }
    func testActualOfflineReaderSearchBackupAndLifecycle() async throws {
        let reader=try await openReader()
        let report=try await script(reader,"""
        (()=>{
          const check=(x,m)=>{if(!x)throw Error(m)};
          check(lawMobile.buildSearch().length>500,'full law index');
          check(LawCore.snippet('אָב שָׁלוֹם סוף','שלום').mark==='שָׁלוֹם','Hebrew span');
          localStorage.setItem('outside-backup','keep');
          localStorage.setItem('law-reader-font','24');
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
        reader.webView.goBack()
        try await Task.sleep(nanoseconds:500_000_000)
        let backPosition = try await script(reader,"scrollY") as? Double
        XCTAssertEqual(backPosition ?? -1000,savedPosition ?? -2000,accuracy:3)
        _ = try await script(reader,"lawMobile.goTo('article_14');true")
        reader.persistReadingState()
        reader.webView.reload()
        for _ in 0..<80 { try await Task.sleep(nanoseconds:250_000_000);if reader.ready { break } }
        let savedFont=try await script(reader,"localStorage.getItem('law-reader-font')") as? String
        let savedHash=try await script(reader,"location.hash") as? String
        XCTAssertEqual(savedFont,"24")
        XCTAssertEqual(savedHash,"#article_14")
        // The real native share path uses the current section's public URL.
        reader.shareCurrentSection()
        for _ in 0..<20 {if reader.sharing != nil{break};try await Task.sleep(nanoseconds:100_000_000)}
        XCTAssertTrue(reader.sharing?.items.first is URL)
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
        reader.cleanTemporaryExport()
        XCTAssertFalse(FileManager.default.fileExists(atPath:url.path))
    }
    func testRemoteScriptsAndSubframeBridgeAreBlocked() async throws {
        let reader=try await openReader()
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
    }
}
