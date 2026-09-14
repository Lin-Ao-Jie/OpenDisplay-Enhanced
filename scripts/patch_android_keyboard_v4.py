from pathlib import Path
# This patch adds a real invisible text editor / InputConnection bridge to the Android receiver.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/ui/KeyboardBridgeView.kt')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(r'''package io.github.josepacelli.opendisplay.ui

import android.content.Context
import android.text.InputType
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.BaseInputConnection
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.view.inputmethod.InputMethodManager
import org.json.JSONObject

class KeyboardBridgeView(context: Context, private val send: (JSONObject) -> Unit) : View(context) {
    init { isFocusable = true; isFocusableInTouchMode = true }
    override fun onCheckIsTextEditor() = true
    override fun onCreateInputConnection(outAttrs: EditorInfo): InputConnection {
        outAttrs.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        outAttrs.imeOptions = EditorInfo.IME_ACTION_NONE
        return object : BaseInputConnection(this, false) {
            override fun commitText(text: CharSequence?, newCursorPosition: Int): Boolean {
                if (text != null) send(JSONObject().put("type","keyboardText").put("text",text.toString()))
                return true
            }
            override fun setComposingText(text: CharSequence?, newCursorPosition: Int): Boolean {
                if (text != null) send(JSONObject().put("type","keyboardCompose").put("text",text.toString()))
                return true
            }
            override fun deleteSurroundingText(beforeLength: Int, afterLength: Int): Boolean {
                repeat(beforeLength.coerceAtMost(32)) { send(JSONObject().put("type","keyboardKey").put("key","backspace")) }
                return true
            }
            override fun sendKeyEvent(event: KeyEvent): Boolean {
                if (event.action == KeyEvent.ACTION_DOWN) when(event.keyCode) {
                    KeyEvent.KEYCODE_ENTER -> send(JSONObject().put("type","keyboardKey").put("key","enter"))
                    KeyEvent.KEYCODE_DEL -> send(JSONObject().put("type","keyboardKey").put("key","backspace"))
                }
                return true
            }
            override fun performEditorAction(actionCode: Int): Boolean {
                send(JSONObject().put("type","keyboardKey").put("key","enter")); return true
            }
        }
    }
    fun showKeyboard() {
        requestFocus()
        post {
            val imm = context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.restartInput(this)
            imm.showSoftInput(this, InputMethodManager.SHOW_IMPLICIT)
        }
    }
    fun hideKeyboard() {
        val imm = context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(windowToken, 0); clearFocus()
    }
}
''')
print('KeyboardBridgeView created; activity/receiver integration must be applied before build')
