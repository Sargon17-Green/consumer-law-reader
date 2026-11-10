import XCTest
import UIKit

final class ReaderWindowingUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=300
    }
    private func record(_ app: XCUIApplication,_ label: String) {
        let tree=XCTAttachment(string:app.debugDescription)
        tree.name=label+" accessibility hierarchy";tree.lifetime = .keepAlways;add(tree)
        let screen=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        screen.name=label+" actual simulator screen";screen.lifetime = .keepAlways;add(screen)
    }
    private func visible(_ app: XCUIApplication,_ label: String) -> XCUIElement? {
        app.descendants(matching:.any).matching(NSPredicate(format:"label == %@",label)).allElementsBoundByIndex.first(where:{$0.isHittable})
    }
    func testIPadWindowResizePreservesSearchAndControls() throws {
        XCTAssertEqual(UIDevice.current.userInterfaceIdiom,.pad,"This diagnostic must run on an actual iPad simulator")
        let settings=XCUIApplication(bundleIdentifier:"com.apple.Preferences")
        settings.launch()
        var multitasking:XCUIElement?
        for _ in 0..<6 {
            multitasking=visible(settings,"Multitasking & Gestures")
            if multitasking != nil {break}
            settings.swipeUp()
        }
        record(settings,"Settings before multitasking selection")
        let entry=try XCTUnwrap(multitasking,"Official Multitasking & Gestures setting was not exposed; inspect hierarchy rather than inventing a private preference")
        entry.tap()
        let windowed=settings.descendants(matching:.any).matching(NSPredicate(format:"label == %@","Windowed Apps")).firstMatch
        XCTAssertTrue(windowed.waitForExistence(timeout:20),settings.debugDescription)
        record(settings,"Windowed Apps choice")
        try XCTUnwrap(visible(settings,"Windowed Apps")).tap()
        settings.terminate()
        let app=XCUIApplication()
        app.launch()
        defer {app.terminate()}
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.exists && menu.isEnabled },object:nil)],timeout:60),.completed)
        let web=app.webViews.firstMatch
        XCTAssertTrue(web.waitForExistence(timeout:30))
        let search=web.buttons.matching(identifier:"חיפוש").firstMatch
        XCTAssertTrue(search.waitForExistence(timeout:30));search.tap()
        let input=web.searchFields.firstMatch
        XCTAssertTrue(input.waitForExistence(timeout:20));input.tap();input.typeText("14")
        let result=web.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14")).firstMatch
        XCTAssertTrue(result.waitForExistence(timeout:20));result.tap()
        let returnToSearch=web.buttons.matching(identifier:"חזרה לתוצאות החיפוש").firstMatch
        XCTAssertTrue(returnToSearch.waitForExistence(timeout:20),app.debugDescription)
        record(app,"Before actual iPad window resize")
        let original=web.frame
        let window=app.windows.firstMatch
        // Apple's documented resize gesture starts at the measured bottom-right
        // corner of the current window; this is a real OS gesture, not a Web resize.
        let start=window.coordinate(withNormalizedOffset:CGVector(dx:0.99,dy:0.99))
        let end=window.coordinate(withNormalizedOffset:CGVector(dx:0.58,dy:0.72))
        start.press(forDuration:0.5,thenDragTo:end)
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
            web.exists && web.frame.width<original.width*0.85 && web.frame.width>250
        },object:nil)],timeout:20),.completed,"The actual OS-managed app window must shrink; changing CSS or a test container does not qualify")
        record(app,"After actual iPad window resize")
        XCTAssertGreaterThanOrEqual(menu.frame.width,44)
        XCTAssertGreaterThanOrEqual(menu.frame.height,44)
        XCTAssertTrue(returnToSearch.isHittable,"Return control remains reachable in the resized native window")
        returnToSearch.tap()
        XCTAssertTrue(input.waitForExistence(timeout:20))
        XCTAssertEqual(input.value as? String,"14")
        XCTAssertTrue(result.waitForExistence(timeout:20))
        XCTAssertTrue(result.isHittable,"Search result remains reachable in the resized native window")
        result.tap()
        XCTAssertTrue(returnToSearch.waitForExistence(timeout:20),app.debugDescription)
        let summary="IPAD_WINDOW_RESIZE: original=\(original) resized=\(web.frame) search preserved; real OS window gesture; simulator only"
        let report=XCTAttachment(string:summary);report.name="iPad window resize result";report.lifetime = .keepAlways;add(report)
        print(summary)
    }
}
