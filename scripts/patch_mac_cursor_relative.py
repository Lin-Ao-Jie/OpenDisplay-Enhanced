from pathlib import Path
p=Path('Mac/MacSender.swift')
s=p.read_text()
# Isolated cursor reclaim: physical local mouse movement while pointer is on the
# virtual OpenDisplay screen maps its normalized position onto the main display.
# No click/down/up events are generated.
needle='final class MacSender:'
assert needle in s
# Add monitor state near class body.
pos=s.index('{',s.index(needle))+1
s=s[:pos]+'''\n    private var cursorReclaimMonitor: Any?\n    private var cursorReclaimLastWarp: CFTimeInterval = 0\n'''+s[pos:]
# Install after init has established sender. Locate deinit if available and add helpers before it.
marker='    deinit {'
assert marker in s
helpers='''    private func installCursorReclaim() {
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
            guard let number = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else { return false }
            return number.uint32Value == virtual.displayID
        }), virtualScreen.frame.contains(point), let main = NSScreen.main else { return }
        let vf = virtualScreen.frame, mf = main.frame
        let nx = ((point.x - vf.minX) / vf.width).clamped(to: 0...1)
        let ny = ((point.y - vf.minY) / vf.height).clamped(to: 0...1)
        let target = CGPoint(x: mf.minX + nx * mf.width, y: mf.minY + ny * mf.height)
        cursorReclaimLastWarp = now
        CGWarpMouseCursorPosition(target)
    }

'''
s=s.replace(marker,helpers+marker,1)
# Start monitor after app is ready using first safe setup point.
for candidate in ['        setupDiscovery()\n','        startBonjour()\n']:
    if candidate in s:
        s=s.replace(candidate,candidate+'        installCursorReclaim()\n',1); break
else:
    raise SystemExit('setup marker not found')
# Clean monitor.
s=s.replace(marker,marker+'\n        if let cursorReclaimMonitor { NSEvent.removeMonitor(cursorReclaimMonitor) }',1)
# helper clamp without touching input code
s += '''\nprivate extension Comparable {\n    func clamped(to limits: ClosedRange<Self>) -> Self { min(max(self, limits.lowerBound), limits.upperBound) }\n}\n'''
p.write_text(s)
