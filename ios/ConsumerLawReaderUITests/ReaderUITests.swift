import XCTest

final class ReaderUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=360
    }
    func testNativeHeaderAccessibilityAudit() throws {
        guard #available(iOS 17.0,*) else { throw XCTSkip("Apple's automated accessibility audit requires iOS 17; the iOS 16 functional UI test still runs.") }
        let app=XCUIApplication()
        app.launch()
        defer { app.terminate() }
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        let web=app.webViews.firstMatch
        XCTAssertTrue(web.waitForExistence(timeout:60))
        XCTAssertFalse(web.label.isEmpty)
        let webTop=web.frame.minY
        XCTAssertGreaterThan(webTop,menu.frame.maxY)
        var findings=[[String:String]](),nativeFailures=[String]()
        try app.performAccessibilityAudit(for:[.contrast,.hitRegion,.sufficientElementDescription]) { issue in
            let element=issue.element
            let frame=element?.frame ?? .zero
            let native=element != nil && frame.width>0 && frame.height>0 && frame.maxY<=webTop+0.5
            let knownWeb=element != nil && frame.width>0 && frame.height>0 && frame.minY>=webTop-0.5
            let scope=native ? "native header":knownWeb ? "web content":"unclassified"
            findings.append(["scope":scope,"description":issue.compactDescription,"identifier":element?.identifier ?? "","frame":String(describing:frame)])
            if !knownWeb { nativeFailures.append(scope+": "+issue.compactDescription) }
            return true // Record every issue; fail below for the declared native scope.
        }
        let data=try JSONSerialization.data(withJSONObject:["scope":"Visible native header only; Web has separate axe scans","types":["contrast","hitRegion","sufficientElementDescription"],"findings":findings],options:[.prettyPrinted,.sortedKeys])
        let attachment=XCTAttachment(data:data,uniformTypeIdentifier:"public.json")
        attachment.name="Apple native header accessibility audit"
        attachment.lifetime = .keepAlways
        add(attachment)
        XCTAssertTrue(nativeFailures.isEmpty,nativeFailures.joined(separator:"; "))
        print("NATIVE_ACCESSIBILITY_AUDIT: nativeFailures=\(nativeFailures.count) totalRecorded=\(findings.count)")
    }
    func testSearchNavigationSharingRotationAndRelaunch() {
        let app=XCUIApplication()
        app.launch()
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        for control in [menu,app.buttons.matching(identifier:"native-share").firstMatch] {
            XCTAssertGreaterThanOrEqual(control.frame.width,44)
            XCTAssertGreaterThanOrEqual(control.frame.height,44)
        }
        let search=app.webViews.firstMatch.buttons.matching(identifier:"חיפוש").firstMatch
        let input=app.webViews.firstMatch.searchFields.firstMatch
        func openSearch() {
            XCTAssertTrue(search.waitForExistence(timeout:60))
            search.tap()
            if !input.waitForExistence(timeout:20) {
                XCTAssertTrue(search.waitForExistence(timeout:20),app.debugDescription)
                search.tap()
            }
            XCTAssertTrue(input.waitForExistence(timeout:30),app.debugDescription)
        }
        openSearch()
        input.tap();input.typeText("14")
        let hit=app.webViews.firstMatch.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14")).firstMatch
        XCTAssertTrue(hit.waitForExistence(timeout:15));hit.tap()
        XCTAssertTrue(menu.isEnabled)
        let metrics=XCTMeasureOptions()
        metrics.iterationCount=3
        // Repeated reading gestures measure actual document interaction;
        // system print-popover transitions remain a separate functional test.
        measure(metrics:[XCTCPUMetric(application:app),XCTMemoryMetric(application:app),XCTClockMetric()],options:metrics){
            app.swipeUp()
            app.swipeDown()
        }
        func waitForMenu() {
            XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
                menu.exists && menu.isEnabled
            },object:nil)],timeout:30),.completed,app.debugDescription)
        }
        func openNativeMenu() {
            waitForMenu()
            let inner=menu.buttons.firstMatch
            (inner.exists ? inner:menu).tap()
        }
        openNativeMenu()
        let print=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        XCTAssertTrue(print.waitForExistence(timeout:10));print.tap()
        let printCancel=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        XCTAssertTrue(printCancel.waitForExistence(timeout:45),app.debugDescription);printCancel.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            !printCancel.exists
        },object:nil)],timeout:30),.completed,app.debugDescription)
        waitForMenu()
        openNativeMenu()
        let restore=app.buttons.matching(identifier:"שחזור הגדרות מקובץ").firstMatch
        XCTAssertTrue(restore.waitForExistence(timeout:5));restore.tap()
        let cancel=app.buttons.matching(NSPredicate(format: "label IN %@", ["Cancel", "Close", "ביטול"])).firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout:60),app.debugDescription);cancel.tap()
        XCTAssertTrue(menu.waitForExistence(timeout:10))
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        XCTAssertTrue(share.isEnabled);share.tap()
        XCTAssertTrue(app.otherElements["ActivityListView"].waitForExistence(timeout:8) || app.buttons.matching(identifier:"Copy").firstMatch.exists || app.buttons.matching(identifier:"העתק").firstMatch.exists)
        app.swipeDown()
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(search.waitForExistence(timeout:10))
        XCUIDevice.shared.orientation = .portrait
        let shot=XCTAttachment(screenshot:app.screenshot());shot.name="Reader actual simulator UI";shot.lifetime = .keepAlways;add(shot)
        // Leave the app on its Home Screen, then launch through the installed icon.
        XCUIDevice.shared.press(.home);app.terminate()
        let springboard=XCUIApplication(bundleIdentifier:"com.apple.springboard")
        let icons=springboard.icons.matching(NSPredicate(format:"label BEGINSWITH %@","חוק הגנת הצרכן"))
        var launcher:XCUIElement?
        for attempt in 0..<4 {
            launcher=icons.allElementsBoundByIndex.first(where:{$0.isHittable})
            if launcher != nil {break}
            if attempt<3 {springboard.swipeLeft()}
        }
        XCTAssertNotNil(launcher,"Installed native app must be reachable from its persistent Home Screen icon: "+springboard.debugDescription)
        launcher?.tap()
        XCTAssertTrue(app.wait(for:.runningForeground,timeout:30))
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        openSearch()
        XCTAssertEqual(input.value as? String,"14")
    }
}
