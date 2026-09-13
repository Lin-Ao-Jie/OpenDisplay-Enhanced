from pathlib import Path
p=Path('Mac/MacSender.swift')
s=p.read_text()
needle='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {'
assert needle in s
s=s.replace(needle,needle+'''\n    private var cursorReclaimMonitor: Any?\n    private var cursorReclaimLastWarp: CFTimeInterval = 0\n''',1)
# Install from the actual v1.19 initializer. Global mouseMoved reports physical
# local pointer motion; the warp itself generates no mouse click/down/up.
needle='''        self.awaitingWake = awaitingWake
        super.init()
    }
'''
assert needle in s
s=s.replace(needle,'''        self.awaitingWake = awaitingWake
        super.init()
        installCursorReclaim()
    }

    deinit {
        if let cursorReclaimMonitor { NSEvent.removeMonitor(cursorReclaimMonitor) }
    }

    private func installCursorReclaim() {
        guard cursorReclaimMonitor == nil else { return }
        cursorReclaimMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.mouseMoved]) { [weak self] _ in
            self?.reclaimCursorIfNeeded()
        }
    }

    private func reclaimCursorIfNeeded() {
        guard mode == .extend, let virtual = virtualDisplay else { return }
        let now = CACurrentMediaTime()
        guard now - cursorReclaimLastWarp > 0.15 else { return }
        let point = NSEvent.mouseLocation
        guard let virtualScreen = NSScreen.screens.first(where: { screen in
            guard let n = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else { return false }
            return n.uint32Value == virtual.displayID
        }), virtualScreen.frame.contains(point), let main = NSScreen.main else { return }
        let vf = virtualScreen.frame
        let mf = main.frame
        let nx = min(max((point.x - vf.minX) / vf.width, 0), 1)
        let ny = min(max((point.y - vf.minY) / vf.height, 0), 1)
        cursorReclaimLastWarp = now
        CGWarpMouseCursorPosition(CGPoint(x: mf.minX + nx * mf.width,
                                          y: mf.minY + ny * mf.height))
    }
''',1)
p.write_text(s)
