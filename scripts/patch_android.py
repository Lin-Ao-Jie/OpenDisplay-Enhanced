from pathlib import Path
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/PhoneReceiver.kt'); s=p.read_text()
s=s.replace('import android.os.ParcelFileDescriptor','import android.os.ParcelFileDescriptor\nimport android.media.AudioAttributes\nimport android.media.AudioFormat\nimport android.media.AudioManager\nimport android.media.AudioTrack')
needle='    private var nextVideoFrameSeq = 0L\n'
assert needle in s
s=s.replace(needle,needle+'''\n    private val audioTrack: AudioTrack by lazy {
        val min = AudioTrack.getMinBufferSize(48000, AudioFormat.CHANNEL_OUT_STEREO, AudioFormat.ENCODING_PCM_16BIT)
        AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MOVIE).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(maxOf(min, 19200))
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build().also { it.play() }
    }
''',1)
marker='    private fun dispatchFrame(frame: ByteArray) {\n'
assert marker in s
s=s.replace(marker,marker+'''        // Audio frame: ASCII "ODA1" + little-endian signed 16-bit stereo PCM @ 48 kHz.
        if (frame.size > 4 && frame[0] == 0x4f.toByte() && frame[1] == 0x44.toByte() && frame[2] == 0x41.toByte() && frame[3] == 0x31.toByte()) {
            audioTrack.write(frame, 4, frame.size - 4, AudioTrack.WRITE_NON_BLOCKING)
            return
        }
''',1)
p.write_text(s)
