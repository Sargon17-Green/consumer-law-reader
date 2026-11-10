import XCTest

final class ReaderPrintSaveUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure=false
        executionTimeAllowance=300
    }
    func testInspectActualSystemPrintPreview() {
        let app=XCUIApplication()
        app.launch()
        defer {app.terminate()}
        let menu=app.buttons.matching(identifier:"native-menu").firstMatch
        XCTAssertTrue(menu.waitForExistence(timeout:60))
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in menu.exists && menu.isEnabled },object:nil)],timeout:60),.completed)
        let inner=menu.buttons.firstMatch
        (inner.exists ? inner:menu).tap()
        let printAction=app.buttons.matching(identifier:"הדפסה או שמירה כ־PDF").firstMatch
        XCTAssertTrue(printAction.waitForExistence(timeout:10))
        printAction.tap()
        let cancel=app.buttons.matching(NSPredicate(format:"label IN %@",["Cancel","Close","ביטול"])).firstMatch
        XCTAssertTrue(cancel.waitForExistence(timeout:45))
        let shot=XCTAttachment(screenshot:XCUIScreen.main.screenshot())
        shot.name="Actual system print preview before PDF-save inspection";shot.lifetime = .keepAlways;add(shot)
        func record(_ name:String,_ elements:[XCUIElement]) {
            let values=elements.prefix(20).map { ["label":String($0.label.prefix(180)),"identifier":$0.identifier,"frame":String(describing:$0.frame)] }
            let raw=try! JSONSerialization.data(withJSONObject:values,options:[.sortedKeys])
            Swift.print("SYSTEM_PRINT_CONTROLS_"+name+": "+String(data:raw,encoding:.utf8)!)
        }
        record("BUTTONS",app.buttons.allElementsBoundByIndex)
        record("IMAGES",app.images.allElementsBoundByIndex)
        record("SCROLLVIEWS",app.scrollViews.allElementsBoundByIndex)
        record("PAGE_LABELS",app.descendants(matching:.any).matching(NSPredicate(format:"label CONTAINS[c] %@","page")).allElementsBoundByIndex)
        cancel.tap()
        XCTAssertEqual(XCTWaiter.wait(for:[XCTNSPredicateExpectation(predicate:NSPredicate { _,_ in !cancel.exists },object:nil)],timeout:30),.completed)
        Swift.print("SYSTEM_PRINT_INSPECTION: actual UI recorded; PDF system Files-save is not claimed by this observation test")
    }
}
