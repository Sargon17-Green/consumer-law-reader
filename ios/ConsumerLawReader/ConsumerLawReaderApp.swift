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

struct SharePayload: Identifiable {
    let id = UUID()
    let items: [Any]
}

struct ReaderNotice: Identifiable {
    let id = UUID()
    let message: String
}

struct ReaderScreen: View {
    @StateObject private var reader = OfflineLawReader()
    @State private var chooseBackup = false
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 14) {
                Text("חוק הגנת הצרכן, התשמ״א–1981")
                    .font(.subheadline.weight(.semibold))
                    .fixedSize(horizontal: false, vertical: true)
                    .minimumScaleFactor(0.8)
                    .frame(maxWidth: .infinity, alignment: .leading)

                Button {
                    reader.shareCurrentSection()
                } label: {
                    Image(systemName: "square.and.arrow.up")
                        .frame(minWidth: 44, minHeight: 44)
                        .contentShape(Rectangle())
                }
                .accessibilityIdentifier("native-share")
                .accessibilityLabel("שיתוף קישור לסעיף")
                .disabled(!reader.ready || reader.working)

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
                        .frame(minWidth: 44, minHeight: 44)
                        .contentShape(Rectangle())
                }
                .accessibilityIdentifier("native-menu")
                .accessibilityLabel("פעולות iOS")
                .disabled(!reader.ready || reader.working)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(uiColor: .secondarySystemBackground))

            if !reader.ready {
                HStack {
                    if !reader.loadFailed { ProgressView("טעינת נוסח החוק המקומי") }
                    Button { reader.retryLoading() } label: {
                        Text("טעינה מחדש").frame(minWidth: 44, minHeight: 44).contentShape(Rectangle())
                    }
                        .accessibilityIdentifier("native-retry")
                        .disabled(!reader.loadFailed)
                }
                .accessibilityIdentifier("native-loading")
            }
            LawWebView(webView: reader.webView)
                .accessibilityLabel("נוסח חוק הגנת הצרכן")
        }
        .environment(\.layoutDirection, .rightToLeft)
        .onChange(of: dynamicTypeSize) { _ in reader.applyDynamicType() }
        .onChange(of: reader.requestFileImport) { requested in
            if requested { chooseBackup = true; reader.requestFileImport = false }
        }
        .onChange(of: scenePhase) { phase in
            if phase != .active { reader.persistReadingState() }
        }
        .sheet(item: $reader.sharing, onDismiss: { reader.cleanTemporaryExport() }) { share in
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
            Text(reader.importPreview)
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
        Task { @MainActor [weak reader] in
            guard let reader, reader.isTrustedMessage(message) else { return }
            reader.receiveJSMessage(message.body)
        }
    }
}

@MainActor
final class OfflineLawReader: NSObject, ObservableObject, WKNavigationDelegate, WKUIDelegate {
    @Published var ready = false
    @Published var loadFailed = false
    @Published var sharing: SharePayload?
    @Published var notice: ReaderNotice?
    @Published var confirmImport = false
    @Published var importPreview = ""
    @Published var working = false
    @Published var requestFileImport = false

    let webView: WKWebView
    private let scriptHandler = WeakLawBridge()
    private var pendingSettings: String?
    private var temporaryExport: URL?
    private var resourcePolicyReady = false
    private let website: URL?
    private static let publicURL = "https://sargon17-green.github.io/consumer-law-reader/reader/"

    override init() {
        let controller = WKUserContentController()
        let source = """
        (function() {
          window.NativeLaw = Object.freeze({
            copyLimit: function() { return 1000000; },
            copy: function(value) {
              window.webkit.messageHandlers.lawReader.postMessage({type:'copy', text:String(value)});
            },
            printDocument: function() {
              window.webkit.messageHandlers.lawReader.postMessage({type:'print'});
            },
            share: function(value) {
              window.webkit.messageHandlers.lawReader.postMessage({type:'share', url:String(value)});
            },
            exportSettings: function() {
              window.webkit.messageHandlers.lawReader.postMessage({type:'export'});
            },
            importSettings: function() {
              window.webkit.messageHandlers.lawReader.postMessage({type:'import'});
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
        configureResourcePolicy()
    }

    private func configureResourcePolicy() {
        let rules = ReaderPolicy.contentRules
        WKContentRuleListStore.default().compileContentRuleList(
            forIdentifier: "NoRemoteLawResourcesV2",
            encodedContentRuleList: rules
        ) { [weak self] list, error in
            Task { @MainActor in
                guard let self else { return }
                guard let list else {
                    self.loadFailed = true
                    self.showError("לא ניתן להפעיל חסימת משאבים חיצוניים: \(error?.localizedDescription ?? "שגיאה לא ידועה").")
                    return
                }
                self.webView.configuration.userContentController.add(list)
                self.resourcePolicyReady = true
                self.openBundledLaw()
            }
        }
    }

    private func showError(_ value: String) {
        notice = ReaderNotice(message: value)
    }

    func retryLoading() {
        ready = false; loadFailed = false
        if resourcePolicyReady { openBundledLaw() } else { configureResourcePolicy() }
    }

    private func openBundledLaw() {
        guard let website, FileManager.default.fileExists(atPath: website.path) else {
            loadFailed = true
            showError("קובץ החוק חסר בחבילת ההתקנה. יש לבנות מחדש את יישום iOS.")
            return
        }
        webView.loadFileURL(website, allowingReadAccessTo: website.deletingLastPathComponent())
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        ready = false
        loadFailed = false
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        webView.evaluateJavaScript("document.documentElement.dataset.lawReady === 'true'") { [weak self] value, error in
            Task { @MainActor in
                guard let self else { return }
                self.ready = error == nil && value as? Bool == true
                if self.ready { self.applyDynamicType() }
                if !self.ready { self.loadFailed = true; self.showError("ממשק הקריאה לא אותחל. אפשר לסגור ולפתוח שוב את האפליקציה.") }
            }
        }
    }

    func applyDynamicType() {
        guard ready else { return }
        let scale = UIFont.preferredFont(forTextStyle: .body).pointSize / 17.0
        webView.evaluateJavaScript("window.lawMobile?.setSystemFontScale(" + String(Double(scale)) + ")") { _, _ in }
    }

    func persistReadingState() {
        guard ready else { return }
        webView.evaluateJavaScript("window.lawMobile?.saveSession()") { _, _ in }
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        ready = false
        openBundledLaw()
    }

    func isTrustedMessage(_ message: WKScriptMessage) -> Bool {
        guard message.name == "lawReader", message.webView === webView,
              message.frameInfo.isMainFrame, let url = message.frameInfo.request.url,
              let website else { return false }
        return ReaderPolicy.isBundledDocument(url, website: website)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!,
                 withError error: Error) {
        ready = false; loadFailed = true
        showError("טעינת נוסח החוק נכשלה: \(error.localizedDescription)")
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!,
                 withError error: Error) {
        ready = false; loadFailed = true
        showError("פתיחת קובץ החוק נכשלה: \(error.localizedDescription)")
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else {
            decisionHandler(.cancel)
            return
        }
        if url.isFileURL {
            if let website, ReaderPolicy.isBundledDocument(url, website: website), action.targetFrame?.isMainFrame == true {
                decisionHandler(.allow)
            } else {
                if action.navigationType == .linkActivated, url.pathExtension.lowercased() == "doc" {
                    showLocalAttachment(url.lastPathComponent)
                }
                decisionHandler(.cancel)
            }
            return
        }
        if ReaderPolicy.isExternalLink(url), action.navigationType == .linkActivated,
           action.sourceFrame.isMainFrame {
            UIApplication.shared.open(url)
        }
        decisionHandler(.cancel)
    }

    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url,
           ReaderPolicy.isExternalLink(url), action.sourceFrame.isMainFrame,
           action.navigationType == .linkActivated {
            UIApplication.shared.open(url)
        }
        return nil
    }

    // Calls originating from the packaged JavaScript are deliberately restricted.
    func receiveJSMessage(_ raw: Any) {
        guard let message = raw as? [String: Any],
              let type = message["type"] as? String else { return }
        guard ready, !working else {
            if type == "copy" { webView.evaluateJavaScript("window.lawMobile?.copyResult?.(false)") { _,_ in } }
            return
        }
        switch type {
        case "share":
            guard let value = message["url"] as? String, value.utf8.count < 2048,
                  value.hasPrefix(Self.publicURL + "#"), let url = URL(string: value) else { return }
            sharing = SharePayload(items: [url])
        case "export":
            exportSettings()
        case "import":
            requestFileImport = true
        case "copy":
            guard let value = message["text"] as? String, value.utf16.count <= 1_000_000 else {
                webView.evaluateJavaScript("window.lawMobile?.copyResult?.(false)") { _,_ in }
                return
            }
            UIPasteboard.general.string = value
            webView.evaluateJavaScript("window.lawMobile?.copyResult?.(true)") { _,_ in }
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
              !relative.isEmpty, relative.utf8.count <= 500, relative.hasSuffix(".doc"),
              !relative.contains("/"), !relative.hasPrefix("/"),
              !relative.contains("\\"), !relative.contains("?"),
              !relative.contains("#") else { return }
        let url = root.appendingPathComponent(relative).standardizedFileURL.resolvingSymlinksInPath()
        guard url.path.hasPrefix(root.standardizedFileURL.path + "/"),
              FileManager.default.fileExists(atPath: url.path) else {
            showError("הקובץ המצורף אינו נמצא בחבילת האפליקציה.")
            return
        }
        sharing = SharePayload(items: [url])
    }

    func shareCurrentSection() {
        guard ready, !working else { return }
        let script = """
        (() => {
            const visible = window.lawMobile?.currentArticle()?.id;
            if (visible) return visible;
            try {
                const target = decodeURIComponent(location.hash.slice(1));
                if (target && document.getElementById(target)) return target;
            } catch (_) {}
            return 'law_name';
        })()
        """
        webView.evaluateJavaScript(script) { [weak self] result, error in
            Task { @MainActor in
                guard let self, error == nil, let target = result as? String,
                      !target.isEmpty, target.utf8.count <= 2048,
                      var parts = URLComponents(string: Self.publicURL) else { return }
                parts.fragment = target
                guard let url = parts.url else { return }
                self.sharing = SharePayload(items: [url])
            }
        }
    }

    func printDocument() {
        guard UIPrintInteractionController.isPrintingAvailable else {
            showError("אפשרות ההדפסה אינה זמינה במכשיר הזה.")
            return
        }
        guard ready, !working else { return }
        let controller = UIPrintInteractionController.shared
        let info = UIPrintInfo(dictionary: nil)
        info.outputType = .general
        info.jobName = "חוק הגנת הצרכן"
        controller.printInfo = info
        controller.printFormatter = webView.viewPrintFormatter()
        if UIDevice.current.userInterfaceIdiom == .pad {
            controller.present(from: CGRect(x: webView.bounds.midX, y: webView.bounds.minY, width: 1, height: 1), in: webView, animated: true, completionHandler: nil)
        } else {
            controller.present(animated: true, completionHandler: nil)
        }
    }

    func goHome() {
        webView.evaluateJavaScript("window.lawMobile?.goTo('law_name')") { _, _ in }
    }

    // All formats and all preference values are validated by the same code on both platforms.
    private func jsonArgument(_ value: String) -> String? {
        guard let data = try? JSONSerialization.data(withJSONObject: [value]),
              let array = String(data: data, encoding: .utf8) else { return nil }
        return String(array.dropFirst().dropLast())
    }

    func cleanTemporaryExport() {
        if let temporaryExport { try? FileManager.default.removeItem(at: temporaryExport) }
        temporaryExport = nil
    }

    func exportSettings() {
        guard ready, !working else { return }
        working = true
        webView.evaluateJavaScript("window.lawSettings.exportJSON()") { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                defer { self.working = false }
                guard error == nil, let contents = result as? String,
                      let data = contents.data(using: .utf8), data.count <= 1_000_000 else {
                    self.showError("לא ניתן לקרוא את הגדרות המשתמש.")
                    return
                }
                self.cleanTemporaryExport()
                let target = FileManager.default.temporaryDirectory
                    .appendingPathComponent("consumer-law-settings-" + UUID().uuidString + ".json")
                do {
                    try data.write(to: target, options: [.atomic, .completeFileProtection])
                    self.temporaryExport = target
                    self.sharing = SharePayload(items: [target])
                } catch { self.showError("שמירת הגיבוי נכשלה: \(error.localizedDescription)") }
            }
        }
    }

    func importBackup(result: Result<[URL], Error>) {
        guard ready, !working else { return }
        pendingSettings = nil
        confirmImport = false
        let url: URL
        do {
            guard let selected = try result.get().first else { return }
            url = selected
        } catch {
            if (error as NSError).code != NSUserCancelledError { showError("בחירת קובץ הגיבוי נכשלה.") }
            return
        }
        working = true
        Task {
            do {
                let raw = try await Task.detached(priority: .userInitiated) {
                    let access = url.startAccessingSecurityScopedResource()
                    defer { if access { url.stopAccessingSecurityScopedResource() } }
                    let handle = try FileHandle(forReadingFrom: url)
                    defer { try? handle.close() }
                    var data=Data()
                    while let chunk=try handle.read(upToCount:min(65_536,1_000_001-data.count)),!chunk.isEmpty {
                        data.append(chunk)
                        if data.count>1_000_000 {break}
                    }
                    guard data.count <= 1_000_000, let text = String(data: data, encoding: .utf8) else {
                        throw NSError(domain: "ReaderBackup", code: 1, userInfo: [NSLocalizedDescriptionKey: "קובץ הגיבוי גדול מדי או אינו UTF-8 תקין."])
                    }
                    return text
                }.value
                guard ready, let argument = jsonArgument(raw) else { working = false; return }
                webView.evaluateJavaScript("window.lawSettings.prepareImport(" + argument + ")") { [weak self] result, error in
                    Task { @MainActor in
                        guard let self else { return }
                        defer { self.working = false }
                        guard error == nil, let preview = result as? [String: Any], preview["ok"] as? Bool == true else {
                            self.showError((result as? [String: Any])?["error"] as? String ?? "קובץ הגיבוי אינו תקין.")
                            return
                        }
                        self.pendingSettings = raw
                        self.importPreview = preview["preview"] as? String ?? "ההגדרות הנוכחיות יוחלפו."
                        self.confirmImport = true
                    }
                }
            } catch { working = false; showError("קריאת הגיבוי נכשלה: \(error.localizedDescription)") }
        }
    }

    func cancelPendingImport() { pendingSettings = nil; confirmImport = false; importPreview = "" }

    func applyPendingImport() {
        guard ready, !working, let pendingSettings, let argument = jsonArgument(pendingSettings) else { return }
        self.pendingSettings = nil
        confirmImport = false
        importPreview = ""
        working = true
        webView.evaluateJavaScript("window.lawSettings.applyImport(" + argument + ")") { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                defer { self.working = false }
                guard error == nil, let status = result as? [String: Any], status["ok"] as? Bool == true else {
                    self.showError((result as? [String: Any])?["error"] as? String ?? "השחזור נכשל; ההגדרות הקודמות נשמרו.")
                    return
                }
                self.ready = false
                self.webView.reload()
            }
        }
    }
}
