vasttrafik-cli
==============

python API for Göteborg Västtrafik public API

The project provides a python module to access the Västtrafik public API and 
two command line tools: trip and stops. I think the names are self explaining.

Västtrafik is the public transport company in the county of Västra Götaland,
Sweden.

![ScreenShot](https://raw.github.com/ltworf/vasttrafik-cli/master/screenshot.png)


Suggestions
===========
Suggestions for improvements are welcome only if they come together
with a patch.

Emoji in the terminal
=====================

My terminal was not able to display emoji, and would not show
the vehicle icon.

There is a workaround for that here:

https://forums.debian.net/viewtopic.php?t=149181

```bash
mkdir -p ~/.config/fontconfig/conf.d

echo '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>

  <match target="font">
    <test name="family" compare="eq">
      <string>Noto Serif</string>
    </test>
    <edit name="family" mode="assign_replace">
      <string>Noto Serif Display</string>
    </edit>
    <edit name="family" mode="append_last">
      <string>serif</string>
    </edit>
  </match>
  <match target="pattern">
    <test qual="any" name="family">
      <string>serif</string>
    </test>
    <edit name="family" mode="prepend_first">
      <string>Noto Color Emoji</string>
    </edit>
    <edit name="family" mode="prepend_first">
      <string>Noto Serif Display</string>
    </edit>
  </match>

  <match target="font">
    <test name="family" compare="eq">
      <string>Noto Sans</string>
    </test>
    <edit name="family" mode="assign_replace">
      <string>Noto Sans Display</string>
    </edit>
    <edit name="family" mode="append_last">
      <string>sans-serif</string>
    </edit>
  </match>
  <match target="pattern">
    <test qual="any" name="family">
      <string>sans-serif</string>
    </test>
    <edit name="family" mode="prepend_first">
      <string>Noto Color Emoji</string>
    </edit>
    <edit name="family" mode="prepend_first">
      <string>Noto Sans Display</string>
    </edit>
  </match>

  <match target="font">
    <test name="family" compare="eq">
      <string>Noto Sans Mono</string>
    </test>
    <edit name="family" mode="assign_replace">
      <string>Noto Sans Mono</string>
    </edit>
    <edit name="family" mode="append_last">
      <string>monospace</string>
    </edit>
  </match>
  <match target="pattern">
    <test qual="any" name="family">
      <string>monospace</string>
    </test>
    <edit name="family" mode="prepend_first">
      <string>Noto Color Emoji</string>
    </edit>
    <edit name="family" mode="prepend_first">
      <string>Noto Sans Mono</string>
    </edit>
  </match>

  <alias binding="strong">
    <family>emoji</family>
    <default>
      <family>Noto Color Emoji</family>
    </default>
  </alias>
</fontconfig>' > ~/.config/fontconfig/conf.d/56-nono.conf
```

Restart your terminal and if the emoji font is installed you
should be able to see the emojis in the terminal.
