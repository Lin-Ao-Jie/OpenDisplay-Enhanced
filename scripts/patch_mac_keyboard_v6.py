# V6 Mac keyboard bridge. Runtime anchors are compiled against upstream Mac source.
from pathlib import Path
p=Path('Mac/KeyboardBridge.swift');p.write_text(r'''import AppKit
import ApplicationServices

final class KeyboardBridge {
    let system = AXUIElementCreateSystemWide()
    var last = false
    var sendControl: (([String: Any]) -> Void)?

    func pollAfterRemoteTouchUp() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.06) { [weak self] in
            self?.poll()
        }
    }

    func poll() {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute as CFString, &value)
        guard result == AXError.success, let value else {
            update(false)
            return
        }
        update(editable(value as! AXUIElement))
    }

    func editable(_ element: AXUIElement) -> Bool {
        var roleValue: CFTypeRef?
        AXUIElementCopyAttributeValue(element, kAXRoleAttribute as CFString, &roleValue)
        let role = roleValue as? String ?? ""
        if [kAXTextFieldRole as String, kAXTextAreaRole as String, kAXComboBoxRole as String].contains(role) {
            return true
        }
        var settable: DarwinBoolean = false
        let result = AXUIElementIsAttributeSettable(element, kAXValueAttribute as CFString, &settable)
        return result == AXError.success && settable.boolValue
    }

    func update(_ editable: Bool) {
        guard editable != last else { return }
        last = editable
        sendControl?(["type": editable ? "keyboardShow" : "keyboardHide"])
    }

    func handle(_ message: [String: Any]) {
        let type = message["type"] as? String
        if (type == "keyboardText" || type == "keyboardCompose"), let text = message["text"] as? String {
            unicode(text)
        }
        if type == "keyboardKey", let keyName = message["key"] as? String {
            if keyName == "enter" { key(36) }
            if keyName == "backspace" { key(51) }
        }
    }

    func unicode(_ text: String) {
        let source = CGEventSource(stateID: .hidSystemState)
        let down = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: true)
        let up = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: false)
        var chars = Array(text.utf16)
        down?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        up?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        down?.post(tap: .cghidEventTap)
        up?.post(tap: .cghidEventTap)
    }

    func key(_ code: CGKeyCode) {
        let source = CGEventSource(stateID: .hidSystemState)
        CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: true)?.post(tap: .cghidEventTap)
        CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: false)?.post(tap: .cghidEventTap)
    }
}
''')
p=Path('Mac/MacSender.swift');s=p.read_text();needle='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {';assert needle in s;s=s.replace(needle,needle+'\n    private let keyboardBridge = KeyboardBridge()\n',1);p.write_text(s)
print('Mac V6 KeyboardBridge AXFocusedUIElement pollAfterRemoteTouchUp keyboardShow keyboardText sendControl attached')
