from pathlib import Path
p=Path('Mac/MacSender.swift')
s=p.read_text()
marker='        case "pencil":'
add='''        case "resolution":
            if mode == .extend, let width = obj["width"] as? Int, let height = obj["height"] as? Int, width >= 640, height >= 480, var info = lastHello {
                info.pixelsWide = width * 2
                info.pixelsHigh = height * 2
                lastHello = info
                Task { await self.reconfigure(info) }
            }
'''
assert marker in s
p.write_text(s.replace(marker, add + marker, 1))
