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
    // An independent control: distinguish a broken cold-launch share from
    // a state-transition failure after Print + Files + keyboard interaction.
    // This test complements, never replaces, the full sequential UI test.
    // Independent probes keep system presentation transitions observable.
    // They DO NOT replace the full keyboard/search/print/Files/share test.
    private func verifyIsolatedNativeShare(_ app: XCUIApplication, phase: String) {
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        XCTAssertTrue(share.waitForExistence(timeout:30),"Share must exist: " + phase)
        // A preflight isHittable query can report false for a SwiftUI header
        // that a real coordinate tap successfully operates. Require enabled
        // controls, a physical tap, and the actual system ShareSheet instead.
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            share.exists && share.isEnabled
        },object:nil)],timeout:30),.completed,"Native Share must be enabled: " + phase)
        XCTAssertGreaterThanOrEqual(share.frame.width,44)
        XCTAssertGreaterThanOrEqual(share.frame.height,44)
        share.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        let activities=app.otherElements["ActivityListView"].firstMatch
        let appeared=activities.waitForExistence(timeout:30)
        if !appeared {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(25000)))
            tree.name="Isolated share missing AX " + phase;tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Isolated share missing UI " + phase;shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertTrue(appeared,"Actual ActivityListView must appear: " + phase)
        let closeID=app.buttons.matching(identifier:"header.closeButton").firstMatch
        let closeLabel=app.buttons.matching(NSPredicate(format:"label IN %@",["Close","Cancel","סגירה","סגור","ביטול"])).firstMatch
        let closeReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            activities.exists && ((closeID.exists && closeID.isHittable) ||
                                  (closeLabel.exists && closeLabel.isHittable))
        },object:nil)],timeout:45)
        if closeReady != .completed {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(25000)))
            tree.name="Isolated share Close unavailable AX " + phase;tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Isolated share Close unavailable UI " + phase;shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(closeReady,.completed,"Actual Share Close must be hittable: " + phase)
        let close=(closeID.exists && closeID.isHittable) ? closeID : closeLabel
        print("SHARE_ISOLATION_CLOSE_" + phase + ": " + close.label + ", id=" + close.identifier)
        close.tap()
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            !activities.exists && menu.exists && menu.isEnabled
        },object:nil)],timeout:30),.completed,"Native share must really dismiss: " + phase)
    }

    func testNativeShareAfterPrintWithoutFileImporter() {
        let app=XCUIApplication()
        app.launch()
        defer { app.terminate() }
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            menu.exists && menu.isEnabled
        },object:nil)],timeout:60),.completed,"Header menu must load")
        menu.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        let printAction=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        XCTAssertTrue(printAction.waitForExistence(timeout:15))
        printAction.tap()
        let close=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        XCTAssertTrue(close.waitForExistence(timeout:45),"Real system print UI must appear")
        let before=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        before.name="Isolated actual print UI before closing";before.lifetime = .keepAlways;add(before)
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            close.exists && close.isEnabled && close.isHittable
        },object:nil)],timeout:30),.completed,"System print Close must be hittable")
        close.tap()
        print("SHARE_ISOLATION_PRINT_CLOSE_TAPPED")
        let dismissed=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            !close.exists && menu.exists && menu.isEnabled
        },object:nil)],timeout:30)
        if dismissed != .completed {
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Isolated print failed to dismiss before share";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(dismissed,.completed,"Print must dismiss before subsequent native share")
        verifyIsolatedNativeShare(app,phase:"after-print-only")
    }

    func testNativeShareAfterFileImporterWithoutPrint() {
        let app=XCUIApplication()
        app.launch()
        defer { app.terminate() }
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            menu.exists && menu.isEnabled
        },object:nil)],timeout:60),.completed,"Header menu must load")
        menu.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        let restore=app.buttons.matching(identifier:"שחזור הגדרות מקובץ").firstMatch
        XCTAssertTrue(restore.waitForExistence(timeout:15))
        restore.tap()
        let sidebar=app.navigationBars["DOCSidebarView"].buttons["Cancel"].firstMatch
        let general=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        let ready=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            (sidebar.exists && sidebar.isHittable) || (general.exists && general.isHittable)
        },object:nil)],timeout:60)
        if ready != .completed {
            // A menu item still present after the tap is a different failure
            // from a visible Files picker without Cancel. Record the actual
            // stage instead of assuming that the importer opened.
            Swift.print("FILES_TRANSITION_FAILURE: restoreMenuItemStillExists=\(restore.exists)")
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(25000)))
            tree.name="Isolated importer lacks actionable Cancel AX";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Isolated importer lacks actionable Cancel UI";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(ready,.completed,"Real system Files picker must expose a hittable Cancel")
        let cancel=(sidebar.exists && sidebar.isHittable) ? sidebar : general
        let pickerShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        pickerShot.name="Isolated actual Files picker before Cancel";pickerShot.lifetime = .keepAlways;add(pickerShot)
        cancel.tap()
        print("SHARE_ISOLATION_FILE_CANCEL_TAPPED")
        // Apple Files can retain remote AX proxies even after the picker is
        // dismissed. The decisive acceptance test is a physical tap on Share
        // followed by a usable, dismissible ActivityListView.
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        let readyForNextAction=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            menu.exists && menu.isEnabled && share.exists && share.isEnabled
        },object:nil)],timeout:40)
        if readyForNextAction != .completed {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(25000)))
            tree.name="Isolated Files transition before share AX";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Isolated Files transition before share UI";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(readyForNextAction,.completed,"Reader actions must be enabled after canceling Files")
        verifyIsolatedNativeShare(app,phase:"after-Files-only")
    }

    func testNativeShareDirectlyAfterColdLaunch() {
        let app=XCUIApplication()
        app.launch()
        defer { app.terminate() }
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        XCTAssertTrue(share.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            share.exists && share.isEnabled && menu.exists && menu.isEnabled
        },object:nil)],timeout:60),.completed,"Native share must be enabled on the fully loaded cold-launch reader")
        share.tap()
        let activities=app.otherElements["ActivityListView"].firstMatch
        XCTAssertTrue(activities.waitForExistence(timeout:30),"An actual system share container must appear on cold launch")
        let shareShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        shareShot.name="Native share fresh launch before Close";shareShot.lifetime = .keepAlways;add(shareShot)
        let closeByID=app.buttons.matching(identifier:"header.closeButton").firstMatch
        let closeByLabel=app.buttons.matching(
            NSPredicate(format:"label IN %@",["Close","Cancel","סגירה","סגור","ביטול"])
        ).firstMatch
        let ready=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            activities.exists && ((closeByID.exists && closeByID.isHittable) ||
            (closeByLabel.exists && closeByLabel.isHittable))
        },object:nil)],timeout:45)
        if ready != .completed {
            // A remote ShareSheet container can exist even while its controls
            // never render. Capture this distinction for iOS simulator QA.
            let remote=app.otherElements.matching(identifier:"ShareSheet.RemoteContainerView").firstMatch
            Swift.print("FRESH_SHARE_FAILURE_STAGE: activityExists=\(activities.exists) remoteContainerExists=\(remote.exists)")
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(18000)))
            tree.name="Fresh native share full AX before failed Close";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Fresh native share screen when Close inaccessible";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(ready,.completed,"Cold-launch share must render a hittable native system Close")
        let close=(closeByID.exists && closeByID.isHittable) ? closeByID : closeByLabel
        print("FRESH_SHARE_CONTROL: label=\(close.label) identifier=\(close.identifier) frame=\(close.frame)")
        close.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            !activities.exists && menu.exists && menu.isEnabled
        },object:nil)],timeout:30),.completed,"Actual cold-launch share must close and restore the reader")
    }
    func testSearchNavigationSharingRotationAndRelaunch() {
        // Full keyboard + repeated reading + print + Files + share + rotation
        // + SpringBoard relaunch exceeds the previous 480s allowance on
        // some real simulators. Allow measured UI work to finish; all
        // functional assertions and other test limits remain unchanged.
        executionTimeAllowance=720
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
            // Two actual system AX representations were observed: "Page 1 of N"
            // or (XXXL) a "1" cell accompanied by a "Pages 1-N" range.
            // Both require a real first-page cell with a nonempty frame.
            let fullPage=app.cells.matching(NSPredicate(format:"label BEGINSWITH %@","Page 1 of ")).firstMatch
            let compactPage=app.cells.matching(NSPredicate(format:"label == %@","1")).firstMatch
            let pageRange=app.staticTexts.matching(NSPredicate(format:"label BEGINSWITH %@","Pages 1-")).firstMatch
            let previewReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
                (fullPage.exists && fullPage.frame.width>0 && fullPage.frame.height>0) ||
                (compactPage.exists && compactPage.frame.width>0 && compactPage.frame.height>0 && pageRange.exists)
            },object:nil)],timeout:45)
            if previewReady != .completed {
                let tree=XCTAttachment(string:String(app.debugDescription.prefix(18000)))
                tree.name="Actual system print preview AX when page unavailable";tree.lifetime = .keepAlways;add(tree)
                let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
                shot.name="Actual system print preview when page unavailable";shot.lifetime = .keepAlways;add(shot)
            }
            XCTAssertEqual(previewReady,.completed,"The actual system print preview must contain a real first document page")
        }
        let printCloseReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            guard printCancel.exists && printCancel.isEnabled else { return false }
            let frame=printCancel.frame
            // Do not request a hit point from an invalid or off-screen AX
            // frame: XCTest can throw before reporting a useful assertion.
            return frame.width>0 && frame.height>0 &&
                   frame.intersects(app.frame) && printCancel.isHittable
        },object:nil)],timeout:20)
        if printCloseReady != .completed {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(18000)))
            tree.name="System print Close missing or invalid AX frame";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="System print Close missing or invalid hit point";shot.lifetime = .keepAlways;add(shot)
            // Failure-only diagnostic. A button may become hittable only
            // after the waiter has already timed out; the fresh observation
            // must NOT mask the failed acceptance result. In both cases,
            // probe a real coordinate touch and record actual dismissal.
            let cancelExists=printCancel.exists
            let cancelEnabled=cancelExists && printCancel.isEnabled
            let cancelFrame=cancelExists ? printCancel.frame : CGRect.null
            let appFrame=app.frame
            let center=CGPoint(x:cancelFrame.midX,y:cancelFrame.midY)
            let centerInsideApp=cancelExists && cancelFrame.width>0 &&
                                cancelFrame.height>0 && appFrame.contains(center)
            let cancelHittable=centerInsideApp && printCancel.isHittable
            Swift.print("PRINT_CLOSE_FAILURE: exists=\(cancelExists) enabled=\(cancelEnabled) hittable=\(cancelHittable) frame=\(cancelFrame) appFrame=\(appFrame)")
            if cancelEnabled && centerInsideApp {
                // Probe even when isHittable has changed to true AFTER the
                // waiter failed. Anchor to the app instead of the element so
                // this experiment tests a physical touch rather than AX tap.
                Swift.print("PRINT_CLOSE_LATE_HIT_TEST: hittableAfterTimeout=\(cancelHittable)")
                let touch=app.coordinate(withNormalizedOffset:CGVector(dx:0,dy:0))
                    .withOffset(CGVector(dx:center.x-appFrame.minX,dy:center.y-appFrame.minY))
                Swift.print("PRINT_CLOSE_COORDINATE_PROBE: start=(\(center.x),\(center.y))")
                touch.tap()
                let probeDismissed=XCTWaiter.wait(for:[
                    XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
                        !printCancel.exists && menu.exists && menu.isEnabled
                    },object:nil)
                ],timeout:8) == .completed
                Swift.print("PRINT_CLOSE_COORDINATE_PROBE: actualDismissal=\(probeDismissed)")
                let postShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
                postShot.name="Print Cancel coordinate probe after touch"
                postShot.lifetime = .keepAlways;add(postShot)
                let postAX=XCTAttachment(string:String(app.debugDescription.prefix(18000)))
                postAX.name="Print Cancel coordinate probe post-touch AX"
                postAX.lifetime = .keepAlways;add(postAX)
            } else {
                Swift.print("PRINT_CLOSE_COORDINATE_PROBE: skipped (button disabled/missing or center outside app)")
            }
        }
        // Deliberately fail even if the diagnostic coordinate touch worked.
        // Acceptance requires a hittable system control BEFORE the touch.
        XCTAssertEqual(printCloseReady,.completed,"Actual system Print Close must be enabled, in-frame and hittable")
        let printShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        printShot.name="Actual system print preview before native Close";printShot.lifetime = .keepAlways;add(printShot)
        printCancel.tap()
        let printDismissed=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            !printCancel.exists && menu.exists && menu.isEnabled
        },object:nil)],timeout:30)
        if printDismissed != .completed {
            let afterShot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            afterShot.name="Actual system print UI after failed Close";afterShot.lifetime = .keepAlways;add(afterShot)
        }
        XCTAssertEqual(printDismissed,.completed,"Print Close must dismiss the system UI and restore enabled native controls")
        waitForMenu()
        openNativeMenu()
        let restore=app.buttons.matching(identifier:"שחזור הגדרות מקובץ").firstMatch
        XCTAssertTrue(restore.waitForExistence(timeout:5));restore.tap()
        // iPad's actual Files picker is hosted by DocumentManager under
        // DOCSidebarView, whereas a compact iPhone picker uses the global
        // system Cancel. The generic "firstMatch" can miss the remote button.
        let sidebarCancel=app.navigationBars["DOCSidebarView"].buttons["Cancel"].firstMatch
        let generalCancel=app.buttons.matching(
            NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])
        ).firstMatch
        let cancelReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            (sidebarCancel.exists && sidebarCancel.isHittable) ||
            (generalCancel.exists && generalCancel.isHittable)
        },object:nil)],timeout:60)
        if cancelReady != .completed {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(30000)))
            tree.name="Actual document picker AX when native Cancel unavailable";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Actual document picker before failed cancellation";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(cancelReady,.completed,"Actual Files picker must contain a hittable system Cancel")
        let cancel=(sidebarCancel.exists && sidebarCancel.isHittable) ? sidebarCancel : generalCancel
        cancel.tap()
        // Checking a remote File Picker's stale isHittable proxy before
        // every tap can block even when the reader is plainly available.
        // Actually tap Share and REQUIRE the system share view, its hittable
        // Close button and completed dismissal below. An intercepting picker
        // makes that real interaction fail; no UI coverage is waived.
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        let readyForNextAction=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            menu.exists && menu.isEnabled && share.exists && share.isEnabled
        },object:nil)],timeout:40)
        if readyForNextAction != .completed {
            let afterTree=XCTAttachment(string:String(app.debugDescription.prefix(30000)))
            afterTree.name="Files transition blocked reader action AX";afterTree.lifetime = .keepAlways;add(afterTree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Files transition blocked reader action UI";shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertEqual(readyForNextAction,.completed,"Reader actions must be enabled after canceling Files")
        XCTAssertGreaterThanOrEqual(share.frame.width,44)
        XCTAssertGreaterThanOrEqual(share.frame.height,44)
        share.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        let activities=app.otherElements["ActivityListView"].firstMatch
        // A remote system ShareSheet on iPad26.2 can require longer than the
        // previous eight-second window: the log shows one AX lookup consuming
        // over seven seconds. The independent cold/print/Files share tests
        // all use 30 seconds. Keep one consistent threshold and preserve a
        // screenshot plus AX tree if this genuinely never appears.
        let systemShareAppeared=activities.waitForExistence(timeout:30)
        if !systemShareAppeared {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(30000)))
            tree.name="Full flow system Share missing AX after Print and Files"
            tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Full flow system Share missing screen after Print and Files"
            shot.lifetime = .keepAlways;add(shot)
        }
        XCTAssertTrue(systemShareAppeared,"Actual system share must be presented after Print and Files")
        let shareScreen=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        shareScreen.name="Actual system share before dismissal";shareScreen.lifetime = .keepAlways;add(shareScreen)
        // The ActivityListView can exist before its Close becomes hittable.
        // Wait for that actual control, rather than relying on diagnostic
        // snapshot time or a swipe of the underlying application.
        // The system Close may live in a sibling UIKit presentation rather
        // than within the remote ActivityListView accessibility subtree.
        // Query the foreground application without relaxing the actual
        // isHittable and final sheet-dismissal requirements.
        let closeByID=app.buttons.matching(identifier:"header.closeButton").firstMatch
        let closeByLabel=app.buttons.matching(
            NSPredicate(format:"label IN %@",["Close","Cancel","סגירה","סגור","ביטול"])
        ).firstMatch
        // The remote ShareSheet AX process takes multiple seconds per query
        // in the measured 18.5/26.2 simulator logs. The cold-launch test
        // already allows 45 seconds while requiring identical real Close
        // hit-testing and completed dismissal. Keep both paths consistent.
        let closeReady=XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            activities.exists && ((closeByID.exists && closeByID.isHittable) ||
            (closeByLabel.exists && closeByLabel.isHittable))
        },object:nil)],timeout:45)
        guard closeReady == .completed else {
            let tree=XCTAttachment(string:String(app.debugDescription.prefix(18000)))
            tree.name="Actual foreground system share controls when Close unavailable";tree.lifetime = .keepAlways;add(tree)
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Actual system share UI when Close unavailable";shot.lifetime = .keepAlways;add(shot)
            XCTFail("No hittable Close control while actual system share is present within45 seconds; inspect recorded hierarchy");return
        }
        let closeShare=(closeByID.exists && closeByID.isHittable) ? closeByID : closeByLabel
        Swift.print("NATIVE_SHARE_CLOSE: label=\(closeShare.label) identifier=\(closeShare.identifier) frame=\(closeShare.frame)")
        closeShare.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in !activities.exists },object:nil)],timeout:20),.completed,"Native sharing must be dismissed before rotation and relaunch")
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(search.waitForExistence(timeout:10))
        XCUIDevice.shared.orientation = .portrait
        let shot=XCTAttachment(screenshot:app.screenshot());shot.name="Reader actual simulator UI";shot.lifetime = .keepAlways;add(shot)
        // Leave the app on its Home Screen, then launch through the installed icon.
        XCUIDevice.shared.press(.home);app.terminate()
        // XCTest may report a successful terminate call before SpringBoard
        // has fully retired the process. Do not race a new icon launch with
        // the previous application's shutdown.
        XCTAssertTrue(app.wait(for:.notRunning,timeout:30),
                      "The prior app process must stop before Home Screen relaunch")
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
        let relaunched=app.wait(for:.runningForeground,timeout:30)
        if !relaunched {
            // Keep the real Home Screen icon launch as a strict acceptance
            // requirement. Capture evidence rather than silently falling back
            // to app.activate() or accepting a failed launch.
            let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
            shot.name="Home Screen after native app icon relaunch failure"
            shot.lifetime = .keepAlways
            add(shot)
            let springboardAX=XCTAttachment(string:String(springboard.debugDescription.prefix(18000)))
            springboardAX.name="SpringBoard accessibility after actual icon relaunch failure"
            springboardAX.lifetime = .keepAlways
            add(springboardAX)
            Swift.print("NATIVE_ICON_RELAUNCH_FAILED: appState=\(app.state.rawValue) springboardState=\(springboard.state.rawValue)")
        }
        XCTAssertTrue(relaunched,"Installed Home Screen icon must launch the actual app in foreground")
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        openSearch()
        XCTAssertEqual(input.value as? String,"14")
    }
}
