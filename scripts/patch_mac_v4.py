from pathlib import Path
p=Path('Mac/MacSender.swift')
s=p.read_text()
marker='        case "pencil":'
add='''        case "resolution":
            if mode == .extend, let width = obj["width"] as? Int, let height = obj["height"] as? Int, width >= 640, height >= 480, let old = lastHello {
                let info = PhoneInfo(pixelsWide: width * 2, pixelsHigh: height * 2,
                                     scale: old.scale, device: old.device, id: old.id,
                                     pv: old.pv, cursorPort: old.cursorPort, addrs: old.addrs,
                                     maxEncodeWide: old.maxEncodeWide, maxEncodeHigh: old.maxEncodeHigh)
                lastHello = info
                Task { await self.reconfigure(info) }
            }
'''
assert marker in s
p.write_text(s.replace(marker, add + marker, 1))
