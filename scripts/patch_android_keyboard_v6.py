# V6 Android runtime keyboard integration
from pathlib import Path
base=Path('app/src/main/java/io/github/josepacelli/opendisplay')
ui=base/'ui/KeyboardBridgeView.kt'
ui.write_text(r'''package io.github.josepacelli.opendisplay.ui
import android.content.Context
import android.text.InputType
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.*
import org.json.JSONObject
class KeyboardBridgeView(context: Context, private val send:(JSONObject)->Unit):View(context){
 init{isFocusable=true;isFocusableInTouchMode=true}
 override fun onCheckIsTextEditor()=true
 override fun onCreateInputConnection(a:EditorInfo):InputConnection{a.inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE;return object:BaseInputConnection(this,false){
  override fun commitText(t:CharSequence?,p:Int):Boolean{if(t!=null)send(JSONObject().put("type","keyboardText").put("text",t.toString()));return true}
  override fun setComposingText(t:CharSequence?,p:Int):Boolean{if(t!=null)send(JSONObject().put("type","keyboardCompose").put("text",t.toString()));return true}
  override fun deleteSurroundingText(b:Int,a:Int):Boolean{repeat(b.coerceAtMost(32)){send(JSONObject().put("type","keyboardKey").put("key","backspace"))};return true}
  override fun sendKeyEvent(e:KeyEvent):Boolean{if(e.action==KeyEvent.ACTION_DOWN){if(e.keyCode==KeyEvent.KEYCODE_ENTER)send(JSONObject().put("type","keyboardKey").put("key","enter"));if(e.keyCode==KeyEvent.KEYCODE_DEL)send(JSONObject().put("type","keyboardKey").put("key","backspace"))};return true}
 }}
 fun showKeyboard(){requestFocus();post{val m=context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager;m.restartInput(this);m.showSoftInput(this,InputMethodManager.SHOW_IMPLICIT)}}
 fun hideKeyboard(){val m=context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager;m.hideSoftInputFromWindow(windowToken,0);clearFocus()}
}
''')
p=base/'MainActivity.kt';s=p.read_text();s=s.replace('import android.view.WindowManager','import android.view.WindowManager\nimport android.widget.FrameLayout\nimport io.github.josepacelli.opendisplay.ui.KeyboardBridgeView');s=s.replace('private var bound = false','private var bound = false\n    private var keyboardBridge: KeyboardBridgeView? = null')
old='''            boundReceiver = receiver
            openPendingAccessory(receiver)''';new='''            boundReceiver = receiver
            openPendingAccessory(receiver)
            if (keyboardBridge == null) keyboardBridge = KeyboardBridgeView(this@MainActivity) { receiver.sendKeyboardControl(it) }.also { v -> v.alpha=0.01f; addContentView(v, FrameLayout.LayoutParams(1,1)) }
            receiver.setKeyboardVisibilityHandler { show -> runOnUiThread { if(show) keyboardBridge?.showKeyboard() else keyboardBridge?.hideKeyboard() } }''';assert old in s;s=s.replace(old,new,1);p.write_text(s)
p=base/'net/PhoneReceiver.kt';s=p.read_text();anchor='''    private fun sendControl(json: JSONObject) {
        scope.launch(Dispatchers.IO) { sendControlBlocking(json) }
    }''';assert anchor in s;s=s.replace(anchor,anchor+'''\n    private var keyboardVisibilityHandler: ((Boolean)->Unit)?=null
    fun setKeyboardVisibilityHandler(h:(Boolean)->Unit){keyboardVisibilityHandler=h}
    fun sendKeyboardControl(json:JSONObject){sendControl(json)}
''',1)
# route raw JSON keyboard commands before normal message dispatch
needle='''        when (type) {''';assert needle in s;s=s.replace(needle,'''        if(type=="keyboardShow"){keyboardVisibilityHandler?.invoke(true);return}
        if(type=="keyboardHide"){keyboardVisibilityHandler?.invoke(false);return}
        when (type) {''',1);p.write_text(s)
print('Android V6 keyboard runtime wired: KeyboardBridgeView addContentView setKeyboardVisibilityHandler showSoftInput keyboardText')
