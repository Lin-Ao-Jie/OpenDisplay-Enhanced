from pathlib import Path
# Create bridge; integration uses MacSender's existing control channel in follow-on compile fixes.
p=Path('Mac/KeyboardBridge.swift')
p.write_text('''import AppKit
import ApplicationServices
final class KeyboardBridge {
 let system=AXUIElementCreateSystemWide(); var last=false; var sendControl: (([String:Any])->Void)?
 func pollAfterRemoteTouchUp(){ DispatchQueue.main.asyncAfter(deadline:.now()+0.06){[weak self] in self?.poll()} }
 func poll(){ var v:CFTypeRef?; guard AXUIElementCopyAttributeValue(system,kAXFocusedUIElementAttribute as CFString,&v)==.success, let v=v else { update(false); return }; let e=v as! AXUIElement; update(editable(e)) }
 func editable(_ e:AXUIElement)->Bool { var r:CFTypeRef?; AXUIElementCopyAttributeValue(e,kAXRoleAttribute as CFString,&r); let role=r as? String ?? ""; if [kAXTextFieldRole as String,kAXTextAreaRole as String,kAXComboBoxRole as String].contains(role){return true}; var b:DarwinBoolean=false; return AXUIElementIsAttributeSettable(e,kAXValueAttribute as CFString,&b)==.success && b.boolValue }
 func update(_ x:Bool){ guard x != last else{return}; last=x; sendControl?(["type":x ? "keyboardShow":"keyboardHide"]) }
 func handle(_ m:[String:Any]) { let t=m["type"] as? String; if t=="keyboardText" || t=="keyboardCompose" { if let x=m["text"] as? String { unicode(x) } }; if t=="keyboardKey", let k=m["key"] as? String { if k=="enter"{key(36)}; if k=="backspace"{key(51)} } }
 func unicode(_ s:String){ let src=CGEventSource(stateID:.hidSystemState); let d=CGEvent(keyboardEventSource:src,virtualKey:0,keyDown:true); let u=CGEvent(keyboardEventSource:src,virtualKey:0,keyDown:false); var c=Array(s.utf16); d?.keyboardSetUnicodeString(stringLength:c.count,unicodeString:&c); u?.keyboardSetUnicodeString(stringLength:c.count,unicodeString:&c); d?.post(tap:.cghidEventTap); u?.post(tap:.cghidEventTap) }
 func key(_ k:CGKeyCode){ let s=CGEventSource(stateID:.hidSystemState); CGEvent(keyboardEventSource:s,virtualKey:k,keyDown:true)?.post(tap:.cghidEventTap); CGEvent(keyboardEventSource:s,virtualKey:k,keyDown:false)?.post(tap:.cghidEventTap) }
}
''')
# Ensure generated project includes new Swift source. XcodeGen glob normally includes Mac/**/*.swift.
# Add bridge ownership to MacSender; further socket anchors are verified by compile workflow.
p=Path('Mac/MacSender.swift'); s=p.read_text(); needle='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {'; assert needle in s
s=s.replace(needle,needle+'\n    private let keyboardBridge = KeyboardBridge()\n',1)
p.write_text(s)
print('Mac keyboard v5 bridge attached to MacSender; compile workflow will expose exact socket/touch anchors still required')
