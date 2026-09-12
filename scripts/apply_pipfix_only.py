from pathlib import Path
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/MainActivity.kt')
s=p.read_text()
needle='''    /** Accessory received before the service finished binding; opened once bound. */'''
s=s.replace(needle,'''    /** Suppress panel-size hello messages while Android is transitioning into/out of PiP.\n     * PiP window metrics are tiny and must never be advertised as the physical receiver panel. */\n    private var suppressPanelSizeReports = false\n\n'''+needle,1)
old='''        Log.info("configuration changed — re-reporting panel size")\n        boundReceiver?.let { reportPanelSize(it) }'''
new='''        if (suppressPanelSizeReports || isInPictureInPictureMode) {\n            Log.info("configuration changed during PiP transition — keeping existing panel size")\n            return\n        }\n        Log.info("configuration changed — re-reporting panel size")\n        boundReceiver?.let { reportPanelSize(it) }'''
assert old in s
s=s.replace(old,new,1)
marker='''    /** Auto-enters picture-in-picture when the user leaves to another app or the'''
block='''    /** PiP changes the Activity window bounds to the small floating window. Those bounds are\n     * not a display rotation/resolution change and must not be sent to the Mac as a new hello.\n     * On return to full screen, wait for the window to settle, then re-announce the real panel\n     * size and request a fresh keyframe so the newly-created Surface resumes immediately. */\n    override fun onPictureInPictureModeChanged(\n        isInPictureInPictureMode: Boolean,\n        newConfig: Configuration,\n    ) {\n        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig)\n        if (isInPictureInPictureMode) {\n            suppressPanelSizeReports = true\n            Log.info("entered PiP — preserving full-screen panel geometry")\n        } else {\n            Log.info("left PiP — waiting for full-screen window metrics")\n            window.decorView.postDelayed({\n                suppressPanelSizeReports = false\n                boundReceiver?.let { receiver ->\n                    reportPanelSize(receiver)\n                    receiver.requestKeyframe()\n                }\n            }, 250L)\n        }\n    }\n\n'''
assert marker in s
s=s.replace(marker,block+marker,1)
old='''        enterPictureInPictureMode(pictureInPictureParams())'''
new='''        // Freeze the last full-screen geometry before Android shrinks this Activity into PiP.\n        suppressPanelSizeReports = true\n        if (!enterPictureInPictureMode(pictureInPictureParams())) {\n            suppressPanelSizeReports = false\n        }'''
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
