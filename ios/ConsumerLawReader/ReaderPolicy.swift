import Foundation

/// Network exceptions are data-only, exact paths. No external script or frame is allowed.
enum ReaderPolicy {
    static let datePaths = [
        "raw.githubusercontent.com": "/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json",
        "api.github.com": "/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json",
        "sargon17-green.github.io": "/pastafari-calendar/api/seer-now.json"
    ]

    static func isDateURL(_ url: URL) -> Bool {
        guard url.scheme == "https", url.port == nil, url.user == nil, url.password == nil,
              url.fragment == nil, let host = url.host,
              let parts = URLComponents(url: url, resolvingAgainstBaseURL: false),
              datePaths[host] == parts.percentEncodedPath else { return false }
        guard let query=parts.percentEncodedQuery else { return true }
        guard query.utf8.count<=64 else { return false }
        var seen=Set<String>()
        // Validate the canonical wire spelling, as in the native Android policy
        // and the WKWebView resource rules; percent-encoded aliases are not exceptions.
        for item in query.components(separatedBy:"&") {
            if item.hasPrefix("_t=") {
                guard seen.insert("_t").inserted,
                      item.range(of:"^_t=[0-9]{1,16}$",options:.regularExpression) != nil else { return false }
            } else if item == "ref=main", host == "api.github.com" {
                guard seen.insert("ref").inserted else { return false }
            } else { return false }
        }
        return true
    }

    static func isBundledDocument(_ url: URL, website: URL) -> Bool {
        url.isFileURL && url.host.map({ $0.isEmpty || $0 == "localhost" }) != false &&
        url.query == nil && url.standardizedFileURL.resolvingSymlinksInPath().path == website.standardizedFileURL.resolvingSymlinksInPath().path
    }

    static func isExternalLink(_ url: URL) -> Bool {
        guard let scheme = url.scheme?.lowercased(), ["http", "https", "mailto"].contains(scheme),
              url.user == nil, url.password == nil, url.absoluteString.utf8.count <= 8192 else { return false }
        return scheme == "mailto" || !(url.host?.isEmpty ?? true)
    }

    static var contentRules: String {
        var rules: [[String: Any]] = [["trigger": ["url-filter": "^https?://"], "action": ["type": "block"]]]
        for (host, path) in datePaths.sorted(by: { $0.key < $1.key }) {
            let base = "https://" + host + path
            let escaped = base.replacingOccurrences(of: ".", with: "\\.")
            // WebKit's content-blocker regex subset does not support counted repeats.
            let digits = "[0-9]" + String(repeating: "[0-9]?", count: 15)
            let queries = host == "api.github.com"
                ? ["$", "[?]ref=main(&_t=" + digits + ")?$", "[?]_t=" + digits + "(&ref=main)?$"]
                : ["([?]_t=" + digits + ")?$"]
            // Alternation is also outside WebKit's supported regex subset: use separate rules.
            for query in queries {
                rules.append(["trigger": ["url-filter": "^" + escaped + query, "url-filter-is-case-sensitive": true, "resource-type": ["raw"]], "action": ["type": "ignore-previous-rules"]])
            }
        }
        let data = try! JSONSerialization.data(withJSONObject: rules, options: [.sortedKeys])
        return String(data: data, encoding: .utf8)!
    }
}
