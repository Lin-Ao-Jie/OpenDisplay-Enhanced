from pathlib import Path
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/net/PhoneReceiver.kt'); s=p.read_text()
s=s.replace('private const val KEY_ZOOM_ENABLED = "zoomEnabled"','private const val KEY_ZOOM_ENABLED = "zoomEnabled"\n        private const val KEY_RESOLUTION_WIDTH = "resolutionWidth"\n        private const val KEY_RESOLUTION_HEIGHT = "resolutionHeight"')
needle='    private val _zoomEnabled = MutableStateFlow(loadZoomEnabled())\n    val zoomEnabled: StateFlow<Boolean> = _zoomEnabled.asStateFlow()\n'
assert needle in s
s=s.replace(needle,needle+'\n    data class Resolution(val width: Int, val height: Int) { val isAuto: Boolean get() = width <= 0 || height <= 0 }\n    private val _resolution = MutableStateFlow(loadResolution())\n    val resolution: StateFlow<Resolution> = _resolution.asStateFlow()\n',1)
marker='    /** Best-effort local IPv4 address for manually typing into the Mac app\'s'
method='''    fun setResolution(width: Int, height: Int) {
        val value = if (width > 0 && height > 0) Resolution(width, height) else Resolution(0, 0)
        if (value == _resolution.value) return
        _resolution.value = value
        appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).edit()
            .putInt(KEY_RESOLUTION_WIDTH, value.width).putInt(KEY_RESOLUTION_HEIGHT, value.height).apply()
        if (link != null) sendHello()
    }

'''
assert marker in s; s=s.replace(marker,method+marker,1)
s=s.replace('.put("pixelsWide", devicePixelsWide)\n            .put("pixelsHigh", devicePixelsHigh)', '.put("pixelsWide", if (_resolution.value.isAuto) devicePixelsWide else _resolution.value.width)\n            .put("pixelsHigh", if (_resolution.value.isAuto) devicePixelsHigh else _resolution.value.height)',1)
end='    /** @return the current wall-clock time in milliseconds, as a [Double] (wire messages use floats). */'
load='''    private fun loadResolution(): Resolution {
        val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return Resolution(prefs.getInt(KEY_RESOLUTION_WIDTH, 0), prefs.getInt(KEY_RESOLUTION_HEIGHT, 0))
    }

'''
assert end in s; s=s.replace(end,load+end,1); p.write_text(s)
p=Path('app/src/main/java/io/github/josepacelli/opendisplay/ui/SettingsDialog.kt'); s=p.read_text()
s=s.replace('val zoomEnabled by receiver.zoomEnabled.collectAsState()','val zoomEnabled by receiver.zoomEnabled.collectAsState()\n    val resolution by receiver.resolution.collectAsState()',1)
s=s.replace('VideoSection(zoomEnabled, receiver::setZoomEnabled, modifier = Modifier.fillMaxWidth())','VideoSection(zoomEnabled, receiver::setZoomEnabled, modifier = Modifier.fillMaxWidth())\n                    ResolutionSection(resolution, receiver::setResolution, modifier = Modifier.fillMaxWidth())',1)
s=s.replace('VideoSection(zoomEnabled, receiver::setZoomEnabled)','VideoSection(zoomEnabled, receiver::setZoomEnabled)\n                    ResolutionSection(resolution, receiver::setResolution)',1)
marker='/** @param draftName'
section='''@Composable
private fun ResolutionSection(selected: PhoneReceiver.Resolution, onSelect: (Int, Int) -> Unit, modifier: Modifier = Modifier) {
    val options = listOf(PhoneReceiver.Resolution(0,0) to "Auto / Native", PhoneReceiver.Resolution(1280,800) to "1280 × 800", PhoneReceiver.Resolution(1600,1000) to "1600 × 1000", PhoneReceiver.Resolution(1920,1200) to "1920 × 1200", PhoneReceiver.Resolution(2560,1600) to "2560 × 1600")
    SettingsSection(stringResource(R.string.settings_section_resolution), modifier) {
        Text(stringResource(R.string.settings_resolution_hint), style = MaterialTheme.typography.bodySmall)
        options.forEach { (v,label) -> FilterChip(selected = selected == v, onClick = { onSelect(v.width,v.height) }, label = { Text(label) }, modifier = Modifier.padding(top = 6.dp)) }
    }
}

'''
assert marker in s; s=s.replace(marker,section+marker,1); p.write_text(s)
p=Path('app/src/main/res/values/strings.xml'); s=p.read_text().replace('</resources>','    <string name="settings_section_resolution">Resolution</string>\n    <string name="settings_resolution_hint">Changes the actual macOS virtual-display resolution.</string>\n</resources>'); p.write_text(s)
