# Quad PWM with prescaler — Tiny Tapeout (Sky130)

Four channel 8 bit PWM generator with a shared prescaler, per channel enable mask and complementary outputs. Built for the Tiny Tapeout Sky130 shuttle (TTSKY26c).

- RTL: `src/project.v` (top module `tt_um_anirudh12032008_pwm4`)
- Tests: `test/` (cocotb + Icarus, run `cd test && make`)
- Datasheet: `docs/info.md`

## What it does

A free running 8 bit counter advances once every `prescaler + 1` clock cycles. Each of the four channels has its own 8 bit duty register and is high while `counter < duty`. The compare stage is registered so the outputs never glitch.

Registers are written over a small parallel interface: data on `ui_in[7:0]`, address on `uio_in[2:0]`, then pulse `uio_in[3]` (WR).

| Address | Register |
|---|---|
| 0–3 | Duty for channels 0–3 |
| 4 | Prescaler |
| 5 | Enable mask |

`uo_out[3:0]` are the four PWM channels and `uo_out[7:4]` their inverted copies, for complementary drive or a fading LED pair.

At 50 MHz with prescaler 0 the PWM frequency is 195 kHz; with prescaler 255 it drops to about 763 Hz.

## Testing

`cd test && make` runs the cocotb testbench: reset state, exact duty cycle on every channel, complementary outputs, prescaler and enable mask (5 tests).

Workflows in `.github/workflows` build the GDS with `TinyTapeout/tt-gds-action@ttsky26c` and run RTL and gate level tests. After pushing, enable GitHub Actions and set Pages source to "GitHub Actions".
