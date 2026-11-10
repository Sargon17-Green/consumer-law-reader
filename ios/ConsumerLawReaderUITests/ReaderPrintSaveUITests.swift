import XCTest

final class ReaderPrintSaveUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=300
    }
    private func openPrint(_ app: XCUIApplication) {
        app.launchEnvironment["LAW_PRINT_QA"]="1"
        app.launch()
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.exists && menu.isEnabled },object:nil)],timeout:60),.completed)
        let center=menu.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5))
        center.tap()
        let action=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        XCTAssertTrue(action.waitForExistence(timeout:10));action.tap()
    }
    private func record(_ name:String,_ element:XCUIElement) {
        Swift.print("SYSTEM_PRINT_"+name+": label=\(element.label) frame=\(element.frame) enabled=\(element.isEnabled) hittable=\(element.isHittable)")
        let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        shot.name="Actual system print "+name;shot.lifetime = .keepAlways;add(shot)
    }
    func testActualPrintCloseAfterHittable() {
        let app=XCUIApplication()
        defer {app.terminate()}
        openPrint(app)
        let close=app.buttons.matching(NSPredicate(format:"label IN %@",["Close","Cancel","ביטול"])).firstMatch
        XCTAssertTrue(close.waitForExistence(timeout:45))
        record("CLOSE_EXISTS",close)
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in close.exists && close.isEnabled && close.isHittable },object:nil)],timeout:20),.completed)
        record("CLOSE_READY",close)
        close.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in !close.exists },object:nil)],timeout:30),.completed)
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.isEnabled },object:nil)],timeout:15),.completed)
        Swift.print("SYSTEM_PRINT_CLOSE: actual single native Close and restored enabled reader")
    }
    func testInspectActualSystemPrintPreview() {
        let app=XCUIApplication()
        defer {app.terminate()}
        openPrint(app)
        let systemShare=app.buttons.matching(identifier:"Share").firstMatch
        XCTAssertTrue(systemShare.waitForExistence(timeout:60),"The actual system print preview has a Share control")
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in systemShare.exists && systemShare.isEnabled && systemShare.isHittable },object:nil)],timeout:30),.completed)
        record("SHARE_READY",systemShare)
        systemShare.tap()
        let activities=app.otherElements["ActivityListView"].firstMatch
        XCTAssertTrue(activities.waitForExistence(timeout:45),"Actual print PDF system activities")
        let save=activities.cells.matching(NSPredicate(format:"label IN %@",["Save to Files","שמירה בקבצים"])).firstMatch
        if !save.waitForExistence(timeout:8) {
            activities.swipeUp()
        }
        XCTAssertTrue(save.waitForExistence(timeout:15),"System print PDF must offer Save to Files: "+String(activities.debugDescription.prefix(14000)))
        record("SAVE_TO_FILES",save)
        save.tap()
        let browser=app.navigationBars.firstMatch
        XCTAssertTrue(browser.waitForExistence(timeout:30))
        let snap=XCTAttachment(string:String(app.debugDescription.prefix(22000)))
        snap.name="Actual system Files save browser controls";snap.lifetime = .keepAlways;add(snap)
        Swift.print("SYSTEM_FILES_BROWSER: "+String(app.debugDescription.prefix(22000)))
    }
}
