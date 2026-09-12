from pathlib import Path
p=Path('Mac/MacSender.swift'); s=p.read_text()
# Enable ScreenCaptureKit system audio at a stable Android-friendly format.
needle='        config.showsCursor = !localCursor\n'
assert needle in s
s=s.replace(needle,needle+'''        config.capturesAudio = true
        config.sampleRate = 48000
        config.channelCount = 2
        config.excludesCurrentProcessAudio = true
''',1)
needle='        try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: queue)\n'
assert needle in s
s=s.replace(needle,needle+'        try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: queue)\n',1)
# Route audio separately before the existing screen-only path.
old='''        guard stream === self.stream,
              type == .screen,
              CMSampleBufferIsValid(sampleBuffer),
              let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer)
        else { return }
'''
new='''        guard stream === self.stream, CMSampleBufferIsValid(sampleBuffer) else { return }
        if type == .audio {
            sendAudio(sampleBuffer)
            return
        }
        guard type == .screen, let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
'''
assert old in s; s=s.replace(old,new,1)
# First audio transport: compact framed PCM. Header ODA1 lets old video parsing reject it safely.
marker='    private func isPipelineBackedUp() -> Bool {\n'
method='''    private func sendAudio(_ sample: CMSampleBuffer) {
        guard connectionReady, let block = CMSampleBufferGetDataBuffer(sample) else { return }
        let length = CMBlockBufferGetDataLength(block)
        guard length > 0, length < 1 << 18 else { return }
        var pcm = Data(count: length)
        let status = pcm.withUnsafeMutableBytes { raw in
            CMBlockBufferCopyDataBytes(block, atOffset: 0, dataLength: length, destination: raw.baseAddress!)
        }
        guard status == noErr else { return }
        var payload = Data([0x4f, 0x44, 0x41, 0x31])
        payload.append(pcm)
        sendFramed(payload)
    }

'''
assert marker in s; s=s.replace(marker,method+marker,1)
p.write_text(s)
