import SwiftUI
import UIKit
import WebKit
import UniformTypeIdentifiers

// The authoritative legal text is packaged by scripts/build_web.py.
// No network connection is required to read the document after installation.
@main
struct ConsumerLawReaderApp: App {
    var body: some Scene {
        WindowGroup {
            ReaderScreen()
        }
    }
}

private struct SharePayload: Identifiable {
    let id = UUID()
    let items: [Any]
}

private struct ReaderNotice: Identifiable {
    let id = UUID()
    let message: String
}

struct ReaderScreen: View {
    @StateObject private var reader = OfflineLawReader()
    @State private var chooseBackup = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 14) {
                Text("חוק הגנת הצרכן")
                    .font(.headline)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Button {
                    reader.shareCurrentSection()
                } label: {
                    Image(systemName: "square.and.arrow.up")
                }
                .accessibilityLabel("שיתוף קישור לסעיף")
                .disabled(!reader.ready)

                Menu {
                    Button("הדפסה או שמירה כ־PDF", systemImage: "printer") {
                        reader.printDocument()
                    }
                    Button("גיבוי ההגדרות לקובץ", systemImage: "square.and.arrow.up.on.square") {
                        reader.exportSettings()
                    }
                    Button("שחזור הגדרות מקובץ", systemImage: "square.and.arrow.down.on.square") {
                        chooseBackup = true
                    }
                    Button("חזרה לתחילת החוק", systemImage: "house") {
                        reader.goHome()
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
                .accessibilityLabel("פעולות iOS")
                .disabled(!reader.ready)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(uiColor: .secondarySystemBackground))

            LawWebView(webView: reader.webView)
                .accessibilityLabel("נוסח חוק הגנת הצרכן")
        }
        .environment(\.layoutDirection, .rightToLeft)
        .sheet(item: $reader.sharing) { share in
            ActivitySheet(items: share.items)
        }
        .fileImporter(
            isPresented: $chooseBackup,
            allowedContentTypes: [.json],
            allowsMultipleSelection: false
        ) { result in
            reader.importBackup(result: result)
        }
        .confirmationDialog(
            "שחזור הגדרות",
            isPresented: $reader.confirmImport,
            titleVisibility: .visible
        ) {
            Button("שחזר את ההגדרות מקובץ הגיבוי") {
                reader.applyPendingImport()
            }
            Button("ביטול", role: .cancel) {
                reader.cancelPendingImport()
            }
        } message: {
            Text("השחזור מחליף רק את ההגדרות המופיעות בגיבוי. הוא אינו משנה את נוסח החוק. מומלץ לגבות את ההגדרות הנוכחיות קודם.")
        }
        .alert(item: $reader.notice) { item in
            Alert(title: Text("חוק הגנת הצרכן"), message: Text(item.message),
                  dismissButton: .default(Text("אישור")))
        }
    }
}

private struct LawWebView: UIViewRepresentable {
    let webView: WKWebView

    func makeUIView(context: Context) -> WKWebView { webView }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

private struct ActivitySheet: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

private final class WeakLawBridge: NSObject, WKScriptMessageHandler {
    weak var reader: OfflineLawReader?

    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        reader?.receiveJSMessage(message.body)
    }
}

@MainActor
final class OfflineLawReader: NSObject, ObservableObject, WKNavigationDelegate, WKUIDelegate {
    @Published var ready = false
    @Published var sharing: SharePayload?
    @Published var notice: ReaderNotice?
    @Published var confirmImport = false

    let webView: WKWebView
    private let scriptHandler = WeakLawBridge()
    private var pendingSettings: [String: String]?
    private let website: URL?
    private static let publicURL = "https://sargon17-green.github.io/consumer-law-reader/"

    override init() {
        let controller = WKUserContentController()
        let source = """
        (function() {
          window.NativeLaw = Object.freeze({
            copy: function(value) {
              window.webkit.messageHandlers.lawReader.postMessage({type:'copy', text:String(value)});
            },
            printDocument: function() {
              window.webkit.messageHandlers.lawReader.postMessage({type:'print'});
            },
            openAttachment: function(value) {
              window.webkit.messageHandlers.lawReader.postMessage({type:'attachment', file:String(value)});
            }
          });
        })();
        """
        controller.addUserScript(WKUserScript(
            source: source,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        let configuration = WKWebViewConfiguration()
        configuration.userContentController = controller
        configuration.websiteDataStore = .default()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        self.webView = WKWebView(frame: .zero, configuration: configuration)
        self.website = Bundle.main.url(
            forResource: "index", withExtension: "html", subdirectory: "dist"
        )
        super.init()

        scriptHandler.reader = self
        controller.add(scriptHandler, name: "lawReader")
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
        webView.isOpaque = false
        webView.backgroundColor = .systemBackground
        webView.scrollView.contentInsetAdjustmentBehavior = .never

        // The legal HTML is self-contained. Block every remote subresource,
        // including third-party scripts; user-activated external links open
        // in Safari, outside this web view.
        let rules = """
        [{"trigger":{"url-filter":"^https?://"},"action":{"type":"block"}}]
        """
        WKContentRuleListStore.default().compileContentRuleList(
            forIdentifier: "NoRemoteLawResourcesV1",
            encodedContentRuleList: rules
        ) { [weak self] list, error in
            Task { @MainActor in
                guard let self else { return }
                guard let list else {
                    self.showError("לא ניתן להפעיל חסימת משאבים חיצוניים: \(error?.localizedDescription ?? "שגיאה לא ידועה").")
                    return
                }
                self.webView.configuration.userContentController.add(list)
                self.openBundledLaw()
            }
        }
    }

    private func showError(_ value: String) {
        notice = ReaderNotice(message: value)
    }

    private func openBundledLaw() {
        guard let website, FileManager.default.fileExists(atPath: website.path) else {
            showError("קובץ החוק חסר בחבילת ההתקנה. יש לבנות מחדש את יישום iOS.")
            return
        }
        webView.loadFileURL(website, allowingReadAccessTo: website.deletingLastPathComponent())
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        ready = true
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!,
                 withError error: Error) {
        showError("טעינת נוסח החוק נכשלה: \(error.localizedDescription)")
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!,
                 withError error: Error) {
        showError("פתיחת קובץ החוק נכשלה: \(error.localizedDescription)")
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else {
            decisionHandler(.cancel)
            return
        }
        if url.isFileURL {
            let root = website?.deletingLastPathComponent().standardizedFileURL.path ?? ""
            let path = url.standardizedFileURL.path
            decisionHandler(!root.isEmpty && (path == root || path.hasPrefix(root + "/")) ? .allow : .cancel)
            return
        }
        if ["https", "http"].contains(url.scheme?.lowercased() ?? ""),
           action.navigationType == .linkActivated {
            UIApplication.shared.open(url)
        }
        decisionHandler(.cancel)
    }

    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url,
           ["http", "https"].contains(url.scheme?.lowercased() ?? ""),
           action.navigationType == .linkActivated {
            UIApplication.shared.open(url)
        }
        return nil
    }

    // Calls originating from the packaged JavaScript are deliberately restricted.
    func receiveJSMessage(_ raw: Any) {
        guard let message = raw as? [String: Any],
              let type = message["type"] as? String else { return }
        switch type {
        case "copy":
            guard let value = message["text"] as? String, value.count <= 1_000_000 else { return }
            UIPasteboard.general.string = value
        case "print":
            printDocument()
        case "attachment":
            guard let path = message["file"] as? String else { return }
            showLocalAttachment(path)
        default:
            break
        }
    }

    private func showLocalAttachment(_ relative: String) {
        guard let root = website?.deletingLastPathComponent(),
              !relative.isEmpty, !relative.hasPrefix("/"),
              !relative.contains("\\"), !relative.contains("?"),
              !relative.contains("#") else { return }
        let url = root.appendingPathComponent(relative).standardizedFileURL
        guard url.path.hasPrefix(root.standardizedFileURL.path + "/"),
              FileManager.default.fileExists(atPath: url.path) else {
            showError("הקובץ המצורף אינו נמצא בחבילת האפליקציה.")
            return
        }
        sharing = SharePayload(items: [url])
    }

    func shareCurrentSection() {
        webView.evaluateJavaScript("window.location.hash") { [weak self] result, _ in
            Task { @MainActor in
                guard let self else { return }
                let hash = (result as? String) ?? ""
                // Never share arbitrary or excessively long injected paths.
                let safeHash = hash.hasPrefix("#") && hash.utf8.count < 2048 ? hash : ""
                guard let url = URL(string: Self.publicURL + safeHash) else { return }
                self.sharing = SharePayload(items: [url])
            }
        }
    }

    func printDocument() {
        guard UIPrintInteractionController.isPrintingAvailable else {
            showError("אפשרות ההדפסה אינה זמינה במכשיר הזה.")
            return
        }
        let controller = UIPrintInteractionController.shared
        let info = UIPrintInfo(dictionary: nil)
        info.outputType = .general
        info.jobName = "חוק הגנת הצרכן"
        controller.printInfo = info
        controller.printFormatter = webView.viewPrintFormatter()
        controller.present(animated: true)
    }

    func goHome() {
        webView.evaluateJavaScript("window.lawMobile?.goTo('law_name')") { _, _ in }
    }

    // Export and import *only* user settings; never export or replace legal text.
    private static let backupFormat = "consumer-law-reader-settings-v1"

    func exportSettings() {
        let js = """
        (function() {
            const values = {};
            for (let i = 0; i < localStorage.length; i++) {
              const key = localStorage.key(i);
              if (key && key.startsWith('law-')) values[key] = localStorage.getItem(key);
            }
            return JSON.stringify({format:'consumer-law-reader-settings-v1', settings:values});
        })()
        """
        webView.evaluateJavaScript(js) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                guard error == nil, let contents = result as? String,
                      let data = contents.data(using: .utf8), data.count <= 1_000_000 else {
                    self.showError("לא ניתן לקרוא את הגדרות המשתמש.")
                    return
                }
                let target = FileManager.default.temporaryDirectory
                    .appendingPathComponent("consumer-law-settings-backup.json")
                do {
                    try data.write(to: target, options: .atomic)
                    self.sharing = SharePayload(items: [target])
                } catch {
                    self.showError("שמירת הגיבוי נכשלה: \(error.localizedDescription)")
                }
            }
        }
    }

    func importBackup(result: Result<[URL], Error>) {
        do {
            guard let url = try result.get().first else { return }
            let access = url.startAccessingSecurityScopedResource()
            defer { if access { url.stopAccessingSecurityScopedResource() } }
            let values = try Data(contentsOf: url)
            guard values.count <= 1_000_000,
                  let raw = try JSONSerialization.jsonObject(with: values) as? [String: Any],
                  raw["format"] as? String == Self.backupFormat,
                  let settings = raw["settings"] as? [String: String],
                  settings.count <= 150,
                  settings.allSatisfy({ $0.key.hasPrefix("law-") &&
                      $0.key.count <= 120 && $0.value.utf8.count <= 500_000 }) else {
                showError("קובץ הגיבוי אינו תואם לפורמט הצפוי, או שהוא גדול מדי.")
                return
            }
            pendingSettings = settings
            confirmImport = true
        } catch {
            showError("קריאת הגיבוי נכשלה: \(error.localizedDescription)")
        }
    }

    func cancelPendingImport() {
        pendingSettings = nil
    }

    func applyPendingImport() {
        guard let pendingSettings,
              let data = try? JSONSerialization.data(withJSONObject: pendingSettings,
                                                     options: [.fragmentsAllowed]),
              let json = String(data: data, encoding: .utf8) else {
            showError("לא ניתן לשחזר את ההגדרות.")
            return
        }
        self.pendingSettings = nil
        let js = """
        (function() {
          const settings = \(json);
          for (const [key, value] of Object.entries(settings)) {
            if (key.startsWith('law-') && typeof value === 'string') {
              localStorage.setItem(key, value);
            }
          }
          return true;
        })()
        """
        webView.evaluateJavaScript(js) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                if error != nil || result as? Bool != true {
                    self.showError("לא ניתן לשחזר את ההגדרות באחסון המקומי.")
                } else {
                    self.webView.reload()
                }
            }
        }
    }
}
