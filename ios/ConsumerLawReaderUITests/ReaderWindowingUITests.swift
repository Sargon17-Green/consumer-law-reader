import XCTest
import UIKit

final class ReaderWindowingUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=360
    }
    private func record(_ app: XCUIApplication,_ label: String,native:Bool=true) {
        let details:String
        if native {
            let menu=app.buttons.matching(identifier:"native-menu").firstMatch
            let share=app.buttons.matching(identifier:"native-share").firstMatch
            let web=app.webViews.firstMatch
            details="window=\(app.windows.firstMatch.frame)\nweb=\(web.exists ? String(describing:web.frame):"missing")\nmenu=\(menu.exists ? menu.debugDescription:"missing")\nshare=\(share.exists ? share.debugDescription:"missing")"
        } else {
            details=String(app.debugDescription.prefix(24000))
        }
        let tree=XCTAttachment(string:details)
        tree.name=label+" actual native accessibility controls and geometry";tree.lifetime = .keepAlways;add(tree)
        let screen=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        screen.name=label+" actual simulator screen";screen.lifetime = .keepAlways;add(screen)
    }
    private func visible(_ app: XCUIApplication,_ label: String) -> XCUIElement? {
        app.descendants(matching:.any).matching(NSPredicate(format:"label == %@",label)).allElementsBoundByIndex.first(where:{$0.isHittable})
    }
    func testIPadWindowResizePreservesSearchAndControls() throws {
        guard UIDevice.current.userInterfaceIdiom == .pad else {throw XCTSkip("OS-managed iPad window resize requires the iPad CI job; iPhone functional tests run separately") }
        guard #available(iOS 26.0, *) else {throw XCTSkip("Windowed Apps is an iPadOS26 feature; core UI and layout tests still run on earlier systems")}
        let settings=XCUIApplication(bundleIdentifier:"com.apple.Preferences")
        settings.launch()
        var multitasking:XCUIElement?
        for _ in 0..<6 {
            multitasking=visible(settings,"Multitasking & Gestures")
            if multitasking != nil {break}
            settings.swipeUp()
        }
        record(settings,"Settings before multitasking selection",native:false)
        let entry=try XCTUnwrap(multitasking,"Official Multitasking & Gestures setting was not exposed; inspect hierarchy rather than inventing a private preference")
        entry.tap()
        let windowed=settings.descendants(matching:.any).matching(NSPredicate(format:"label == %@","Windowed Apps")).firstMatch
        XCTAssertTrue(windowed.waitForExistence(timeout:20),settings.debugDescription)
        record(settings,"Windowed Apps choice",native:false)
        let choice=settings.buttons.matching(identifier:"com.apple.settings.multitaskingAndGestures.windowedApps").firstMatch
        XCTAssertTrue(choice.exists)
        if !choice.isSelected {choice.tap()}
        XCTAssertTrue(choice.isSelected,"The actual system windowing mode must be selected")
        settings.terminate()
        let app=XCUIApplication()
        app.launch()
        defer {app.terminate()}
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.exists && menu.isEnabled },object:nil)],timeout:60),.completed)
        let web=app.webViews.firstMatch
        XCTAssertTrue(web.waitForExistence(timeout:30))
        let title=app.staticTexts.matching(identifier:"חוק הגנת הצרכן, התשמ״א–1981").firstMatch
        if title.isHittable {title.tap()}
        let search=web.buttons.matching(identifier:"חיפוש").firstMatch
        let input=web.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout:30));search.tap()
        if !input.waitForExistence(timeout:8) {
            // A first touch can activate the window or meet a WebContent
            // reload. Record the actual state and allow one bounded retry,
            // as the existing full functional UI test already does.
            record(app,"Initial search interaction before bounded retry")
            print("INITIAL_SEARCH_RETRY: menuEnabled=\(menu.isEnabled) nativeLoading=\(app.otherElements.matching(identifier:"native-loading").firstMatch.exists)")
            XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.exists && menu.isEnabled },object:nil)],timeout:60),.completed)
            XCTAssertTrue(search.waitForExistence(timeout:20));search.tap()
        }
        record(app,"Search interaction outcome")
        XCTAssertTrue(input.waitForExistence(timeout:20),"Search must open after at most one recorded retry");input.tap()
        // The preceding full-suite relaunch test can leave the same query.
        // Preserve it; deleting at an unknown restored caret may produce1414.
        if (input.value as? String) != "14" {
            if let existing=input.value as? String,!existing.isEmpty,existing != input.placeholderValue {
                XCTFail("Unexpected prior search fixture: " + existing);return
            }
            input.typeText("14")
        }
        XCTAssertEqual(input.value as? String,"14")
        let result=web.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14 ·")).firstMatch
        XCTAssertTrue(result.waitForExistence(timeout:20));result.tap()
        let returnToSearch=web.buttons.matching(identifier:"חזרה לתוצאות החיפוש").firstMatch
        XCTAssertTrue(returnToSearch.waitForExistence(timeout:20),app.debugDescription)
        record(app,"Before actual iPad window resize")
        let original=web.frame
        let window=app.windows.firstMatch
        // The first touch gesture did not resize. Its actual screenshot exposes
        // the handle in the bottom-right 28pt square. Test a public pointer drag
        // over that observed handle, with system hierarchy and dimensions recorded.
        let springboard=XCUIApplication(bundleIdentifier:"com.apple.springboard")
        record(springboard,"System resize controls before pointer drag",native:false)
        let handles=springboard.otherElements.matching(identifier:"resize-grabber").allElementsBoundByIndex
        let handle=try XCTUnwrap(handles.first(where:{$0.label.contains("חוק הגנת הצרכן") && ($0.value as? String)=="Bottom Right"}),"Use the actual observed system resize handle")
        let start=handle.coordinate(withNormalizedOffset:CGVector(dx:0,dy:0)).withOffset(CGVector(dx:6,dy:6))
        let end=window.coordinate(withNormalizedOffset:CGVector(dx:0.58,dy:0.72))
        print("IPAD_WINDOW_POINTER: from=\(start.screenPoint) to=\(end.screenPoint) originalWeb=\(original)")
        start.hover()
        start.click(forDuration:0.2,thenDragTo:end)
        record(app,"Immediately after pointer resize gesture")
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            web.exists && web.frame.width<original.width*0.85 && web.frame.width>250
        },object:nil)],timeout:20),.completed,"The actual OS-managed app window must shrink; changing CSS or a test container does not qualify")
        record(app,"After actual iPad window resize")
        XCTAssertGreaterThanOrEqual(menu.frame.width,44)
        XCTAssertGreaterThanOrEqual(menu.frame.height,44)
        // A44pt AX frame does not prove reachability: system window controls
        // may overlap a custom header. Perform real native actions after resize.
        let innerMenu=menu.buttons.firstMatch
        (innerMenu.exists ? innerMenu:menu).tap()
        let printAction=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        record(app,"After actual resized native menu tap")
        record(springboard,"System controls after native menu tap",native:false)
        XCTAssertTrue(printAction.waitForExistence(timeout:10),"Native menu must open after the real pointer/touch tap, despite system window controls")
        web.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.22)).tap()
        let share=app.buttons.matching(identifier:"native-share").firstMatch
        XCTAssertTrue(share.isHittable)
        share.tap()
        XCTAssertTrue(app.otherElements["ActivityListView"].waitForExistence(timeout:10) || app.buttons.matching(identifier:"Copy").firstMatch.exists,"Native share must open from the resized header")
        record(app,"Actual resized native share presentation")
        app.swipeDown()
        XCTAssertTrue(returnToSearch.isHittable,"Return control remains reachable in the resized native window")
        returnToSearch.tap()
        XCTAssertTrue(input.waitForExistence(timeout:20))
        XCTAssertEqual(input.value as? String,"14")
        XCTAssertTrue(result.waitForExistence(timeout:20))
        record(app,"Restored search in the resized native window")
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in result.isHittable },object:nil)],timeout:10),.completed,"The selected search result stays visible after layout changes, before any automatic tap scrolling")
        result.tap()
        XCTAssertTrue(returnToSearch.waitForExistence(timeout:20),app.debugDescription)
        let summary="IPAD_WINDOW_RESIZE: original=\(original) resized=\(web.frame) search preserved; real OS window gesture; simulator only"
        let report=XCTAttachment(string:summary);report.name="iPad window resize result";report.lifetime = .keepAlways;add(report)
        print(summary)
    }
}
