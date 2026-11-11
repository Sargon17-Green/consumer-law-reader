import XCTest

final class ReaderUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=480
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
        input.tap()
        let keyboard=app.keyboards.firstMatch
        XCTAssertTrue(keyboard.waitForExistence(timeout:8),"This native UI scenario requires the actual software keyboard")
        XCTAssertGreaterThan(keyboard.frame.height,100,"A hardware-keyboard suggestion bar is not a software keyboard test")
        XCTAssertGreaterThan(input.frame.height,0)
        XCTAssertLessThanOrEqual(input.frame.maxY,keyboard.frame.minY+1,"Native software keyboard must not cover the actual search field")
        Swift.print("NATIVE_KEYBOARD_BOUNDS: input=\(input.frame) keyboard=\(keyboard.frame) web=\(app.webViews.firstMatch.frame)")
        let keyboardShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        keyboardShot.name="Actual native software keyboard and reachable search";keyboardShot.lifetime = .keepAlways;add(keyboardShot)
        input.typeText("14")
        let hit=app.webViews.firstMatch.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14 ·")).firstMatch
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
            menu.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        }
        openNativeMenu()
        let print=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        XCTAssertTrue(print.waitForExistence(timeout:10));print.tap()
        let printCancel=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        XCTAssertTrue(printCancel.waitForExistence(timeout:45),app.debugDescription)
        if #available(iOS 26.0,*) {
            // Require an actual document preview in the redesigned print UI;
            // the presence of a Close control alone does not verify rendering.
            let firstPage=app.cells.matching(NSPredicate(format:"label BEGINSWITH %@","Page 1 of ")).firstMatch
            XCTAssertTrue(firstPage.waitForExistence(timeout:45),"The actual system print preview must contain the first document page")
            XCTAssertGreaterThan(firstPage.frame.width,0)
            XCTAssertGreaterThan(firstPage.frame.height,0)
        }
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            printCancel.exists && printCancel.isEnabled && printCancel.isHittable
        },object:nil)],timeout:20),.completed,"The actual system Close must be ready")
        let printShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        printShot.name="Actual system print preview before native Close";printShot.lifetime = .keepAlways;add(printShot)
        printCancel.tap()
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
        let activities=app.otherElements["ActivityListView"].firstMatch
        XCTAssertTrue(activities.waitForExistence(timeout:8),"Actual system share must be presented")
        let shareScreen=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        shareScreen.name="Actual system share before dismissal";shareScreen.lifetime = .keepAlways;add(shareScreen)
        // The ActivityListView can exist before its Close becomes hittable.
        // Wait for that actual control, rather than relying on diagnostic
        // snapshot time or a swipe of the underlying application.
        // Enumerating every AX button repeatedly can invalidate remote elements
        // during UIActivityViewController transitions on older iPadOS. Query
        // stable targeted first matches instead; still require an actually
        // hittable system Close button and the real sheet's dismissal.
        let closeByID=activities.buttons.matching(identifier:"header.closeButton").firstMatch
        let closeByLabel=activities.buttons.matching(
            NSPredicate(format:"label IN %@",["Close","Cancel","סגירה","סגור","ביטול"])
        ).firstMatch
        let closeReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            (closeByID.exists && closeByID.isHittable) ||
            (closeByLabel.exists && closeByLabel.isHittable)
        },object:nil)],timeout:15)
        guard closeReady == .completed else {
            let tree=XCTAttachment(string:String(activities.debugDescription.prefix(18000)))
            tree.name="Actual system share controls when Close unavailable";tree.lifetime = .keepAlways;add(tree)
            XCTFail("No hittable Close control in the actual system share within15 seconds; inspect recorded hierarchy");return
        }
        let closeShare=closeByID.isHittable ? closeByID : closeByLabel
        Swift.print("NATIVE_SHARE_CLOSE: label=\(closeShare.label) identifier=\(closeShare.identifier) frame=\(closeShare.frame)")
        closeShare.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in !activities.exists },object:nil)],timeout:20),.completed,"Native sharing must be dismissed before rotation and relaunch")
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
