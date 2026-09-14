from pathlib import Path

# Protocol 4 tagged framing / audio capability.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/protocol/WireProtocol.kt')
s=p.read_text().replace('const val VERSION = 2','const val VERSION = 4')
p.write_text(s)

# Add Android AAC decoder/player. Audio failure is isolated from display/video.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/AudioReceiver.kt')
p.write_text(r'''package io.github.josepacelli.opendisplay.net

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.media.MediaCodec
import android.media.MediaFormat
import java.nio.ByteBuffer

internal class AudioReceiver {
    private var codec: MediaCodec? = null
    private var track: AudioTrack? = null
    private var rate = 0
    private var channels = 0

    fun offer(packet: ByteArray) {
        if (packet.size < 15 || packet[0].toInt() != 0) return // AAC-LC only
        val sr = ((packet[2].toInt() and 255) shl 24) or ((packet[3].toInt() and 255) shl 16) or
            ((packet[4].toInt() and 255) shl 8) or (packet[5].toInt() and 255)
        val ch = packet[14].toInt() and 255
        if (sr <= 0 || ch !in 1..2) return
        if (codec == null || sr != rate || ch != channels) configure(sr, ch)
        val c = codec ?: return
        val input = c.dequeueInputBuffer(0)
        if (input >= 0) {
            val b = c.getInputBuffer(input) ?: return
            b.clear(); b.put(packet, 15, packet.size - 15)
            c.queueInputBuffer(input, 0, packet.size - 15, 0, 0)
        }
        drain(c)
    }

    private fun configure(sr: Int, ch: Int) {
        close()
        try {
            val format = MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_AAC, sr, ch)
            format.setInteger(MediaFormat.KEY_AAC_PROFILE, 2)
            format.setByteBuffer("csd-0", ByteBuffer.wrap(aacCookie(sr, ch) ?: return))
            codec = MediaCodec.createDecoderByType(MediaFormat.MIMETYPE_AUDIO_AAC).also {
                it.configure(format, null, null, 0); it.start()
            }
            val mask = if (ch == 1) AudioFormat.CHANNEL_OUT_MONO else AudioFormat.CHANNEL_OUT_STEREO
            val min = AudioTrack.getMinBufferSize(sr, mask, AudioFormat.ENCODING_PCM_16BIT)
            track = AudioTrack.Builder()
                .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MOVIE).build())
                .setAudioFormat(AudioFormat.Builder().setSampleRate(sr).setChannelMask(mask).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
                .setBufferSizeInBytes(maxOf(min, sr * ch / 5))
                .setTransferMode(AudioTrack.MODE_STREAM).build().also { it.play() }
            rate = sr; channels = ch
        } catch (_: Exception) { close() }
    }

    private fun drain(c: MediaCodec) {
        val info = MediaCodec.BufferInfo()
        while (true) {
            val out = c.dequeueOutputBuffer(info, 0)
            if (out < 0) return
            val b = c.getOutputBuffer(out)
            if (b != null && info.size > 0) {
                b.position(info.offset); b.limit(info.offset + info.size)
                val pcm = ByteArray(info.size); b.get(pcm)
                track?.write(pcm, 0, pcm.size, AudioTrack.WRITE_NON_BLOCKING)
            }
            c.releaseOutputBuffer(out, false)
        }
    }

    fun close() {
        try { codec?.stop() } catch (_: Exception) {}
        try { codec?.release() } catch (_: Exception) {}
        try { track?.stop() } catch (_: Exception) {}
        try { track?.release() } catch (_: Exception) {}
        codec = null; track = null; rate = 0; channels = 0
    }

    private fun aacCookie(sr: Int, ch: Int): ByteArray? {
        val rates = intArrayOf(96000,88200,64000,48000,44100,32000,24000,22050,16000,12000,11025,8000,7350)
        val i = rates.indexOf(sr); if (i < 0 || ch !in 1..7) return null
        val bits = (2 shl 11) or (i shl 7) or (ch shl 3)
        return byteArrayOf((bits ushr 8).toByte(), bits.toByte())
    }
}
''')

# Route negotiated protocol-4 frames.
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/PhoneReceiver.kt')
s=p.read_text()
needle='    private var nextVideoFrameSeq = 0L\n'
assert needle in s
s=s.replace(needle, needle+'    private var taggedFrames = false\n    private val audioReceiver = AudioReceiver()\n',1)
old='''    private fun dispatchFrame(frame: ByteArray) {
        if (AnnexB.isControlJson(frame)) {
            handleControlJson(frame)
            return
        }
        val parsed = AnnexB.parse(frame)
'''
new='''    private fun dispatchFrame(frame: ByteArray) {
        var payload = frame
        if (taggedFrames) {
            if (frame.isEmpty()) return
            payload = frame.copyOfRange(1, frame.size)
            when (frame[0].toInt() and 0xff) {
                1 -> { handleControlJson(payload); return }
                2 -> { audioReceiver.offer(payload); return }
                0 -> Unit
                else -> return
            }
        } else if (AnnexB.isControlJson(frame)) {
            handleControlJson(frame)
            return
        }
        val parsed = AnnexB.parse(payload)
'''
assert old in s
s=s.replace(old,new,1)
needle='''            WireMessage.WELCOME -> {
                val macVersion = obj.optInt("pv", WireProtocol.ASSUMED_WHEN_ABSENT)
'''
assert needle in s
s=s.replace(needle, needle+'                taggedFrames = macVersion >= 4\n',1)
# Reset negotiation/audio per connection.
needle='''                _connected.value = false
                unstableClearJob?.cancel()
'''
s=s.replace(needle,'''                _connected.value = false
                taggedFrames = false
                audioReceiver.close()
                unstableClearJob?.cancel()
''')
p.write_text(s)
