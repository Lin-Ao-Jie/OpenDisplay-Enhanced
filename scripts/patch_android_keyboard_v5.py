from pathlib import Path
# Runtime keyboard patch: create IME editor and wire it into MainActivity.
ui=Path('app/src/main/java/io/github/josepacelli/opendisplay/ui/KeyboardBridgeView.kt')
ui.parent.mkdir(parents=True, exist_ok=True)
ui.write_text('''package io.github.josepacelli.opendisplay.ui
import android.content.Context
import android.text.InputType
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.*
import org.json.JSONObject
class KeyboardBridgeView(context: Context, val send: (JSONObject)->Unit): View(context) {
 init { isFocusable=true; isFocusableInTouchMode=true }
 override fun onCheckIsTextEditor()=true
 override fun onCreateInputConnection(a: EditorInfo): InputConnection { a.inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE; return object: BaseInputConnection(this,false) {
  override fun commitText(t:CharSequence?,p:Int):Boolean { if(t!=null) send(JSONObject().put("type","keyboardText").put("text",t.toString())); return true }
  override fun setComposingText(t:CharSequence?,p:Int):Boolean { if(t!=null) send(JSONObject().put("type","keyboardCompose").put("text",t.toString())); return true }
  override fun deleteSurroundingText(b:Int,a:Int):Boolean { repeat(b.coerceAtMost(32)){send(JSONObject().put("type","keyboardKey").put("key","backspace"))}; return true }
  override fun sendKeyEvent(e:KeyEvent):Boolean { if(e.action==KeyEvent.ACTION_DOWN) { if(e.keyCode==KeyEvent.KEYCODE_ENTER) send(JSONObject().put("type","keyboardKey").put("key","enter")); if(e.keyCode==KeyEvent.KEYCODE_DEL) send(JSONObject().put("type","keyboardKey").put("key","backspace")) }; return true }
 } }
 fun showKeyboard(){ requestFocus(); post { val i=context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager; i.restartInput(this); i.showSoftInput(this,InputMethodManager.SHOW_IMPLICIT) } }
 fun hideKeyboard(){ val i=context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager; i.hideSoftInputFromWindow(windowToken,0); clearFocus() }
}
''')
# MainActivity integration anchors. PhoneReceiver needs public keyboard flow/send API from audio patch follow-up.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/MainActivity.kt'); s=p.read_text()
s=s.replace('import android.view.WindowManager','import android.view.WindowManager\nimport android.view.ViewGroup\nimport android.widget.FrameLayout\nimport io.github.josepacelli.opendisplay.ui.KeyboardBridgeView')
s=s.replace('private var bound = false','private var bound = false\n    private var keyboardBridge: KeyboardBridgeView? = null')
needle='''            boundReceiver = receiver
            openPendingAccessory(receiver)'''
repl='''            boundReceiver = receiver
            openPendingAccessory(receiver)
            if (keyboardBridge == null) {
                keyboardBridge = KeyboardBridgeView(this@MainActivity) { receiver.sendKeyboardControl(it) }.also { v ->
                    v.alpha = 0.01f
                    addContentView(v, FrameLayout.LayoutParams(1, 1))
                }
            }
            receiver.setKeyboardVisibilityHandler { show -> runOnUiThread { if (show) keyboardBridge?.showKeyboard() else keyboardBridge?.hideKeyboard() } }'''
assert needle in s; s=s.replace(needle,repl,1); p.write_text(s)
# Wire receiver APIs/control messages.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/PhoneReceiver.kt'); s=p.read_text()
anchor='''    private fun sendControl(json: JSONObject) {
        scope.launch(Dispatchers.IO) { sendControlBlocking(json) }
    }'''
assert anchor in s
s=s.replace(anchor,anchor+'''\n\n    private var keyboardVisibilityHandler: ((Boolean) -> Unit)? = null
    fun setKeyboardVisibilityHandler(handler: (Boolean) -> Unit) { keyboardVisibilityHandler = handler }
    fun sendKeyboardControl(json: JSONObject) { sendControl(json) }
''',1)
# insert control cases before PONG
needle='''            WireMessage.PONG -> handlePong(obj)'''
assert needle in s
s=s.replace(needle,'''            "keyboardShow" -> keyboardVisibilityHandler?.invoke(true)
            "keyboardHide" -> keyboardVisibilityHandler?.invoke(false)
            WireMessage.PONG -> handlePong(obj)''',1)
p.write_text(s)
print('Android keyboard v5 runtime wired')
