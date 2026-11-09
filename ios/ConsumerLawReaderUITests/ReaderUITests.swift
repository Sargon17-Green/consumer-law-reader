import XCTest

final class ReaderUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
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
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap()
        let input=app.webViews.firstMatch.searchFields.firstMatch
        XCTAssertTrue(input.waitForExistence(timeout:10))
        input.tap();input.typeText("14")
        let hit=app.webViews.firstMatch.buttons.matching(NSPredicate(format:"label BEGINSWITH %@","סעיף 14")).firstMatch
        XCTAssertTrue(hit.waitForExistence(timeout:15));hit.tap()
        XCTAssertTrue(menu.isEnabled)
        let metrics=XCTMeasureOptions()
        metrics.iterationCount=3
        func waitForMenu() {
            XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in
                menu.exists && menu.isEnabled && menu.isHittable
            },object:nil)],timeout:30),.completed,app.debugDescription)
        }
        measure(metrics:[XCTCPUMetric(application:app),XCTMemoryMetric(application:app),XCTClockMetric()],options:metrics){
            waitForMenu()
            menu.tap()
            let print=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
            XCTAssertTrue(print.waitForExistence(timeout:5));print.tap()
            let printCancel=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
            XCTAssertTrue(printCancel.waitForExistence(timeout:30),app.debugDescription);printCancel.tap()
            waitForMenu()
        }
        waitForMenu()
        menu.tap()
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
        app.terminate();app.launch()
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:60),.completed)
        XCTAssertTrue(search.waitForExistence(timeout:60))
        search.tap();XCTAssertTrue(input.waitForExistence(timeout:10))
        XCTAssertEqual(input.value as? String,"14")
    }
}
