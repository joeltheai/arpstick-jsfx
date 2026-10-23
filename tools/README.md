# Validation tooling

The plugin is written in EEL2, the language REAPER's JSFX uses. These tools
compile and functionally test `ArpStick.jsfx` with the real EEL2 engine
(Cockos WDL's `loose_eel` interpreter), so issues are caught before loading
the plugin into REAPER.

## Building the checker

1. Clone Cockos WDL:

       git clone --depth 1 https://github.com/justinfrankel/WDL

2. Apply the harness patch (adds JSFX builtin stubs with exact argument-count
   checks, plus a scriptable MIDI event queue for functional tests):

       cd WDL/WDL/eel2
       git apply <path-to-repo>/tools/loose_eel.patch

3. Build the headless interpreter (graphics disabled):

       make NO_GFX=1 loose_eel

## Running

    # compile-check the whole plugin
    python3 tools/validate.py WDL/WDL/eel2/loose_eel

    # compile-check + run the end-to-end MIDI regression suite
    python3 tools/validate.py WDL/WDL/eel2/loose_eel \
        --driver tools/regression.eel

The first invocation compiles the plugin with REAPER-faithful section
ordering and exact argument-count checks for every JSFX builtin used. The
second additionally drives the plugin with simulated MIDI input and a fake
transport, printing every MIDI message the plugin emits (note-ons/offs with
pitches and velocities) so the expected output can be diffed by eye.

## How faithful is the emulation?

- REAPER compiles the `@sections` before top-level "main" code, so helper
  functions defined outside a section are invisible to them. That's why all
  plugin functions live inside `@init`, and why the preprocessor inlines
  `@init` first and wraps the remaining sections as functions after it.
- Every JSFX builtin the plugin calls is registered with REAPER's exact
  parameter count, so signature errors surface at compile time.
- The MIDI stubs implement a queue: `push_midi(offs, st, d1, d2)` feeds the
  plugin and `dump_midi()` prints everything it sent out.

## Caveats

- `gfx_*` stubs are no-ops: the GUI is compile-checked, not pixel-tested.
- `file_*` stubs are no-ops: `@serialize` is compile-checked, not
  round-trip-tested.
- `time_precise()` returns 0 unless driven, which only affects timer-based
  learn mode in the regression tests.
