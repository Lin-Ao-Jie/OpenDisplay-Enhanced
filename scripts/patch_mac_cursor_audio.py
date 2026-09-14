from pathlib import Path
p=Path('Mac/MacSender.swift')
s=p.read_text()
needle='final class MacSender: NSObject, SCStreamOutput, SCStreamDelegate {'
assert needle in s
s=s.replace(needle, needle+'\n    private var odCursorMonitor: Any?\n    private var odCursorLastWarp: CFTimeInterval = 0\n', 1)
needle='        self.awaitingWake = awaitingWake\n        super.init()\n    }\n'
assert needle in s
s=s.replace(needle, '''        self.awaitingWake = awaitingWake
        super.init()
        odInstallCursorReclaim()
    }

    deinit {
        if let odCursorMonitor { NSEvent.removeMonitor(odCursorMonitor) }
    }

    private func odInstallCursorReclaim() {
        guard odCursorMonitor == nil else { return }
        odCursorMonitor = NSEvent.addGlobalMonitorForEvents(matching: [.mouseMoved]) { [weak self] _ in
            self?.odReclaimCursorIfNeeded()
        }
    }

    private func odReclaimCursorIfNeeded() {
        guard mode == .extend, let virtual = virtualDisplay else { return }
        let now = CACurrentMediaTime()
        guard now - odCursorLastWarp > 0.15 else { return }
        let point = NSEvent.mouseLocation
        guard let virtualScreen = NSScreen.screens.first(where: { screen in
            guard let n = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else { return false }
            return n.uint32Value == virtual.displayID
        }), virtualScreen.frame.contains(point), let main = NSScreen.main else { return }
        let vf = virtualScreen.frame, mf = main.frame
        let nx = min(max((point.x - vf.minX) / vf.width, 0), 1)
        let ny = min(max((point.y - vf.minY) / vf.height, 0), 1)
        odCursorLastWarp = now
        CGWarpMouseCursorPosition(CGPoint(x: mf.minX + nx * mf.width, y: mf.minY + ny * mf.height))
    }
''',1)
p.write_text(s)
