MUSIC
═════

solar-eclipse.mp3 is IN PLACE and working.

Extracted from the solar.mp4 you supplied:
  58.9 s · stereo · 44.1 kHz · 128 kbps · 924 KB

HOW IT BEHAVES
  - Plays on every slide, fixed, never restarts on a slide change.
  - Loops seamlessly (verified: wraps from 56.9s back to 1.8s
    without pausing).
  - Volume 0.22, faded in over ~0.9 s so it never jumps.
  - ♫ button top-right mutes/unmutes, with a fade either way.
  - Resumes if the phone is locked and unlocked.

  It starts on her FIRST TAP, not on page load. Every mobile browser
  blocks audio before a user gesture — that is an OS rule, not a bug.
  The landing slide says "turn your volume up" so the first tap on
  NEXT arms it.

TO CHANGE IT
  Volume:  edit `const VOL = 0.22;` in index.html.
  Track:   replace this file, keep the name. A longer rip means fewer
           loops — the clip supplied is 59 s, so it repeats about once
           a minute. If you want it less noticeable, drop in the full
           song under the same filename and nothing else changes.
