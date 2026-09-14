from pathlib import Path

# Android: add keyboard protocol hooks to PhoneReceiver and a real IME bridge view source.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/PhoneReceiver.kt')
s=p.read_text()
needle='object WireMessage {'
# WireMessage lives elsewhere; patch sender API directly here.
insert='''
    fun sendKeyboardText(text: String) {
        if (text.isEmpty()) return
        sendControl(org.json.JSONObject().put("type", "keyboardText").put("text", text))
    }

    fun sendKeyboardKey(key: String) {
        sendControl(org.json.JSONObject().put("type", "keyboardKey").put("key", key))
    }
'''
anchor='    /** Parses one JSON control payload and dispatches it by its `type` field. */'
assert anchor in s
s=s.replace(anchor,insert+'\n'+anchor,1)
p.write_text(s)

# Add standalone focusable editor that can be hosted by the display Activity.
k=Path('app/src/main/java/io/github/josepacelli/opendisplay/ui/RemoteImeEditText.kt')
k.parent.mkdir(parents=True,exist_ok=True)
k.write_text(r'''package io.github.josepacelli.opendisplay.ui

import android.content.Context
import android.text.InputType
import android.util.AttributeSet
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.view.inputmethod.InputMethodManager
import androidx.appcompat.widget.AppCompatEditText

class RemoteImeEditText @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : AppCompatEditText(context, attrs) {
    var onCommit: ((String) -> Unit)? = null
    init {
        isFocusable = true
        isFocusableInTouchMode = true
        inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        alpha = 0.01f
        setSingleLine(false)
    }
    fun showRemoteKeyboard() {
        requestFocus()
        post { (context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager)
            .showSoftInput(this, InputMethodManager.SHOW_IMPLICIT) }
    }
    override fun onCreateInputConnection(outAttrs: EditorInfo): InputConnection? {
        val base = super.onCreateInputConnection(outAttrs) ?: return null
        return object : android.view.inputmethod.InputConnectionWrapper(base, false) {
            override fun commitText(text: CharSequence?, newCursorPosition: Int): Boolean {
                text?.toString()?.takeIf { it.isNotEmpty() }?.let { onCommit?.invoke(it) }
                return super.commitText(text, newCursorPosition)
            }
            override fun deleteSurroundingText(beforeLength: Int, afterLength: Int): Boolean {
                if (beforeLength > 0) onCommit?.invoke("\b")
                return super.deleteSurroundingText(beforeLength, afterLength)
            }
        }
    }
}
''')

# Mac: add AX focus polling + keyboardShow/Hide and keyboardText handling into MacSender.
p=Path('Mac/MacSender.swift')
s=p.read_text()
class_anchor='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {'
assert class_anchor in s
s=s.replace(class_anchor,class_anchor+'''\n    private var odKeyboardTimer: DispatchSourceTimer?\n    private var odKeyboardShown = false\n''',1)
init_anchor='        self.awaitingWake = awaitingWake\n        super.init()\n    }\n'
assert init_anchor in s
s=s.replace(init_anchor,'''        self.awaitingWake = awaitingWake
        super.init()
        odStartKeyboardFocusMonitor()
    }

    private func odStartKeyboardFocusMonitor() {
        let t = DispatchSource.makeTimerSource(queue: queue)
        t.schedule(deadline: .now() + 0.5, repeating: 0.25)
        t.setEventHandler { [weak self] in self?.odPollKeyboardFocus() }
        t.resume()
        odKeyboardTimer = t
    }

    private func odPollKeyboardFocus() {
        guard mode == .extend, AXIsProcessTrusted() else { return }
        let system = AXUIElementCreateSystemWide()
        var focused: CFTypeRef?
        guard AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute as CFString, &focused) == .success,
              let element = focused else { return }
        var roleValue: CFTypeRef?
        AXUIElementCopyAttributeValue(element as! AXUIElement, kAXRoleAttribute as CFString, &roleValue)
        let role = roleValue as? String ?? ""
        let editable = role == kAXTextFieldRole as String || role == kAXTextAreaRole as String || role == kAXComboBoxRole as String
        if editable != odKeyboardShown {
            odKeyboardShown = editable
            let obj: [String: Any] = ["type": editable ? "keyboardShow" : "keyboardHide"]
            if let data = try? JSONSerialization.data(withJSONObject: obj) { sendFrame(data, type: .json) }
        }
    }

    private func odInjectKeyboardText(_ text: String) {
        guard AXIsProcessTrusted() else { return }
        if text == "\\b" {
            let src = CGEventSource(stateID: .hidSystemState)
            CGEvent(keyboardEventSource: src, virtualKey: 51, keyDown: true)?.post(tap: .cghidEventTap)
            CGEvent(keyboardEventSource: src, virtualKey: 51, keyDown: false)?.post(tap: .cghidEventTap)
            return
        }
        let src = CGEventSource(stateID: .hidSystemState)
        let e = CGEvent(keyboardEventSource: src, virtualKey: 0, keyDown: true)
        var chars = Array(text.utf16)
        e?.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: &chars)
        e?.post(tap: .cghidEventTap)
    }
''',1)
# Inject handling near existing JSON message switch using robust type test anchor.
for anchor in ['case "touch":','case "scroll":']:
    if anchor in s:
        s=s.replace(anchor,'''case "keyboardText":
            if let text = obj["text"] as? String { odInjectKeyboardText(text) }
        '''+anchor,1)
        break
p.write_text(s)
