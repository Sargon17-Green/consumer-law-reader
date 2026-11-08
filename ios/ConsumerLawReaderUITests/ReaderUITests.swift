import XCTest

final class ReaderUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
    }
    func testSearchNavigationSharingRotationAndRelaunch() {
        let app=XCUIApplication()
        app.launch()
        let menu=app.buttons["native-menu"]
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        for control in [menu,app.buttons["native-share"]] {
            XCTAssertGreaterThanOrEqual(control.frame.width,44)
            XCTAssertGreaterThanOrEqual(control.frame.height,44)
        }
        let search=app.webViews.buttons["חיפוש"]
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap()
        let input=app.webViews.searchFields.firstMatch
        XCTAssertTrue(input.waitForExistence(timeout:10))
        input.tap();input.typeText("14")
        let hit=app.webViews.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14")).firstMatch
        XCTAssertTrue(hit.waitForExistence(timeout:15));hit.tap()
        XCTAssertTrue(menu.isEnabled);menu.tap()
        let print=app.buttons["הדפסה או שמירה כ־PDF"]
        XCTAssertTrue(print.waitForExistence(timeout:5));print.tap()
        let printCancel=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        XCTAssertTrue(printCancel.waitForExistence(timeout:30),app.debugDescription);printCancel.tap()
        XCTAssertTrue(menu.waitForExistence(timeout:10));menu.tap()
        let restore=app.buttons["שחזור הגדרות מקובץ"]
        XCTAssertTrue(restore.waitForExistence(timeout:5));restore.tap()
        let cancel=app.buttons.matching(NSPredicate(format: "label IN %@", ["Cancel", "Close", "ביטול"])).firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout:60),app.debugDescription);cancel.tap()
        XCTAssertTrue(menu.waitForExistence(timeout:10))
        let share=app.buttons["native-share"]
        XCTAssertTrue(share.isEnabled);share.tap()
        XCTAssertTrue(app.otherElements["ActivityListView"].waitForExistence(timeout:8) || app.buttons["Copy"].exists || app.buttons["העתק"].exists)
        app.swipeDown()
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(search.waitForExistence(timeout:10))
        XCUIDevice.shared.orientation = .portrait
        let shot=XCTAttachment(screenshot:app.screenshot());shot.name="Reader actual simulator UI";shot.lifetime = .keepAlways;add(shot)
        app.terminate();app.launch()
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap();XCTAssertTrue(input.waitForExistence(timeout:10))
        XCTAssertEqual(input.value as? String,"14")
    }
}
