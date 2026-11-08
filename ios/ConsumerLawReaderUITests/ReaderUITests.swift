import XCTest

final class ReaderUITests: XCTestCase {
    func testSearchNavigationSharingRotationAndRelaunch() {
        let app=XCUIApplication()
        app.launch()
        let search=app.webViews.buttons["חיפוש"]
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap()
        let input=app.webViews.searchFields.firstMatch
        XCTAssertTrue(input.waitForExistence(timeout:10))
        input.tap();input.typeText("14")
        let hit=app.webViews.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14")).firstMatch
        XCTAssertTrue(hit.waitForExistence(timeout:15));hit.tap()
        let menu=app.buttons["native-menu"]
        XCTAssertTrue(menu.isEnabled);menu.tap()
        let restore=app.buttons["שחזור הגדרות מקובץ"]
        XCTAssertTrue(restore.waitForExistence(timeout:5));restore.tap()
        let cancel=app.buttons["Cancel"]
        XCTAssertTrue(cancel.waitForExistence(timeout:10));cancel.tap()
        let share=app.buttons["native-share"]
        XCTAssertTrue(share.isEnabled);share.tap()
        XCTAssertTrue(app.otherElements["ActivityListView"].waitForExistence(timeout:8) || app.buttons["Copy"].exists || app.buttons["העתק"].exists)
        app.swipeDown()
        XCUIDevice.shared.orientation = .landscapeLeft
        XCTAssertTrue(search.waitForExistence(timeout:10))
        XCUIDevice.shared.orientation = .portrait
        let shot=XCTAttachment(screenshot:app.screenshot());shot.name="Reader actual simulator UI";shot.lifetime = .keepAlways;add(shot)
        app.terminate();app.launch()
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap();XCTAssertTrue(input.waitForExistence(timeout:10))
        XCTAssertEqual(input.value as? String,"14")
    }
}
