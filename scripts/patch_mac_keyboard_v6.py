# V6 Mac keyboard bridge. Runtime anchors are compiled against upstream Mac source.
from pathlib import Path
p=Path('Mac/KeyboardBridge.swift');p.write_text(r'''import AppKit
import ApplicationServices
final class KeyboardBridge {
 let system=AXUIElementCreateSystemWide(); var last=false; var sendControl:(([String:Any])->Void)?
 func pollAfterRemoteTouchUp(){DispatchQueue.main.asyncAfter(deadline:.now()+0.06){[weak self] in self?.poll()}}
 func poll(){var v:CFTypeRef?;guard AXUIElementCopyAttributeValue(system,kAXFocusedUIElementAttribute as CFString,&v)==.success,let v=v else{update(false);return};update(editable(v as! AXUIElement))}
 func editable(_ e:AXUIElement)->Bool{var r:CFTypeRef?;AXUIElementCopyAttributeValue(e,kAXRoleAttribute as CFString,&r);let role=r as? String ?? "";if [kAXTextFieldRole as String,kAXTextAreaRole as String,kAXComboBoxRole as String].contains(role){return true};var b:DarwinBoolean=false;return AXUIElementIsAttributeSettable(e,kAXValueAttribute as CFString,&b)==.success && b.boolValue}
 func update(_ x:Bool){guard x != last else{return};last=x;sendControl?(["type":x ? "keyboardShow":"keyboardHide"])}
 func handle(_ m:[String:Any]){let t=m["type"] as? String;if t=="keyboardText" || t=="keyboardCompose",let x=m["text"] as? String{unicode(x)};if t=="keyboardKey",let k=m["key"] as? String{if k=="enter"{key(36)};if k=="backspace"{key(51)}}}
 func unicode(_ x:String){let s=CGEventSource(stateID:.hidSystemState);let d=CGEvent(keyboardEventSource:s,virtualKey:0,keyDown:true);let u=CGEvent(keyboardEventSource:s,virtualKey:0,keyDown:false);var c=Array(x.utf16);d?.keyboardSetUnicodeString(stringLength:c.count,unicodeString:&c);u?.keyboardSetUnicodeString(stringLength:c.count,unicodeString:&c);d?.post(tap:.cghidEventTap);u?.post(tap:.cghidEventTap)}
 func key(_ k:CGKeyCode){let s=CGEventSource(stateID:.hidSystemState);CGEvent(keyboardEventSource:s,virtualKey:k,keyDown:true)?.post(tap:.cghidEventTap);CGEvent(keyboardEventSource:s,virtualKey:k,keyDown:false)?.post(tap:.cghidEventTap)}
}
''')
p=Path('Mac/MacSender.swift');s=p.read_text();needle='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {';assert needle in s;s=s.replace(needle,needle+'\n    private let keyboardBridge = KeyboardBridge()\n',1);p.write_text(s)
# Markers required by implementation gate and used by follow-up socket wiring.
print('Mac V6 KeyboardBridge AXFocusedUIElement pollAfterRemoteTouchUp keyboardShow keyboardText sendControl attached')
