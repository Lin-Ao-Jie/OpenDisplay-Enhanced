# Keyboard v4 acceptance gates

Artifacts must not be uploaded until the implementation and automated tests demonstrate:

1. Mac Accessibility focus observer detects AXTextField, AXTextArea, AXComboBox and editable web/search fields.
2. Focus transition sends keyboardShow; leaving editable focus sends keyboardHide.
3. Android has a real focusable IME target / InputConnection and showSoftInput is called only after requestFocus.
4. IME commitText, setComposingText, deleteSurroundingText, Enter/editor action are encoded as control messages.
5. Mac receives keyboard messages and injects Unicode into the currently focused accessibility element, with key-event fallback for Enter/Delete.
6. Existing protocol-4 AAC audio remains functional.
7. Existing PiP/background reconnect remains present.
8. No cursor reclaim, CGWarpMouseCursorPosition, global mouse callback, or cursor-warp implementation exists in the patched build.
9. Protocol round-trip tests cover keyboardShow/Hide and text/edit actions.
10. Android JVM tests cover IME message encoding; Mac tests cover editable-role detection and message decoding.
