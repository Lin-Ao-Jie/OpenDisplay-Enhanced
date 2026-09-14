from pathlib import Path
# Adds the core Accessibility focus detector and Unicode/key injection helper.
p=Path('Mac/KeyboardBridge.swift')
p.write_text(r'''import AppKit
import ApplicationServices

final class KeyboardBridge {
    private let system = AXUIElementCreateSystemWide()
    private var lastEditable = false
    var sendControl: (([String: Any]) -> Void)?

    func pollFocusedEditor() {
        var value: CFTypeRef?
        guard AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute as CFString, &value) == .success,
              let element = value else { setEditable(false); return }
        let ax = element as! AXUIElement
        setEditable(isEditable(ax))
    }

    func pollAfterRemoteTouchUp() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.06) { [weak self] in self?.pollFocusedEditor() }
    }

    private func isEditable(_ e: AXUIElement) -> Bool {
        var roleRef: CFTypeRef?
        AXUIElementCopyAttributeValue(e, kAXRoleAttribute as CFString, &roleRef)
        let role = roleRef as? String ?? ""
        if [kAXTextFieldRole as String, kAXTextAreaRole as String, kAXComboBoxRole as String].contains(role) { return true }
        var settable: DarwinBoolean = false
        if AXUIElementIsAttributeSettable(e, kAXValueAttribute as CFString, &settable) == .success && settable.boolValue { return true }
        return false
    }

    private func setEditable(_ editable: Bool) {
        guard editable != lastEditable else { return }
        lastEditable = editable
        sendControl?(["type": editable ? "keyboardShow" : "keyboardHide"])
    }

    func handle(_ message: [String: Any]) {
        switch message["type"] as? String {
        case "keyboardText", "keyboardCompose":
            guard let text = message["text"] as? String else { return }
            injectUnicode(text)
        case "keyboardKey":
            if message["key"] as? String == "enter" { injectKey(36) }
            if message["key"] as? String == "backspace" { injectKey(51) }
        default: break
        }
    }

    private func injectUnicode(_ text: String) {
        let source = CGEventSource(stateID: .hidSystemState)
        let down = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: true)
        let up = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: false)
        var chars = Array(text.utf16)
        down?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        up?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        down?.post(tap: .cghidEventTap); up?.post(tap: .cghidEventTap)
    }
    private func injectKey(_ code: CGKeyCode) {
        let source = CGEventSource(stateID: .hidSystemState)
        CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: true)?.post(tap: .cghidEventTap)
        CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: false)?.post(tap: .cghidEventTap)
    }
}
''')
print('KeyboardBridge core created; MacSender socket/touch integration must be applied before build')
