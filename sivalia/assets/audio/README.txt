MUSIC — one file, then it just works
════════════════════════════════════

The site is already wired for a fixed, looping, quiet (22% volume)
background track that keeps playing across every slide and survives
the phone locking/unlocking.

It is NOT included, because I can't download copyrighted music.

TO ADD IT:
  Put the track in THIS folder, named exactly:

      solar-eclipse.mp3           (or solar-eclipse.m4a)

  That's it. No code changes. Refresh the page.

The track intended: "Solar Eclipse" — Drake & Don Toliver.
Rip it from your own copy / a purchase you own.

WHILE THE FILE IS MISSING:
  Nothing breaks. The ♫ button in the top-right shows "♪?" and the
  page runs silently.

NOTES
  - Browsers block autoplay with sound, so the track starts on her
    FIRST TAP anywhere on the page. That's unavoidable on mobile —
    it's a browser rule, not a bug.
  - Volume is 0.22 and fades in over ~0.9s. To change it, edit
    `const VOL = 0.22;` in index.html.
  - Keep the file under ~6 MB so it loads fast on mobile data.
    128 kbps mp3 is plenty for background music.
