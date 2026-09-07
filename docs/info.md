## How it works

This is a four channel 8 bit PWM generator with a shared prescaler. A free running 8 bit counter advances once every `prescaler + 1` clock cycles. Each channel has its own 8 bit duty register and is high while `counter < duty`, so a duty value of 0 is always low and 255 is high for 255 out of 256 counter steps. The compare stage is registered so the outputs never glitch.

The register file is written through a simple parallel interface: put the data byte on `ui_in[7:0]`, the register address on `uio_in[2:0]`, then pulse `uio_in[3]` (WR) high. The write happens on the rising edge of WR.

| Address | Register |
|---|---|
| 0 | Duty for channel 0 |
| 1 | Duty for channel 1 |
| 2 | Duty for channel 2 |
| 3 | Duty for channel 3 |
| 4 | Prescaler (counter advances every P + 1 clocks) |
| 5 | Enable mask, bit n enables channel n (reset value 1111) |

Outputs `uo_out[3:0]` are the four PWM channels and `uo_out[7:4]` are their inverted copies, which is handy for driving complementary pairs or for showing a fading LED pair.

At the default 50 MHz clock and prescaler 0 the PWM frequency is 50 MHz / 256 = 195 kHz. With prescaler 255 it drops to about 763 Hz, and the demo board clock can be lowered further for slower fades.

## How to test

1. Reset the design. All outputs `uo_out[3:0]` are low and `uo_out[7:4]` are high.
2. Set `ui_in = 128`, `uio_in = 0b0000` (address 0), then set `uio_in = 0b1000` (WR high) and back to `0b0000`. Channel 0 now runs at 50 percent duty.
3. Repeat with address 4 and a prescaler value such as 255 to slow the PWM down so an LED visibly changes brightness, then sweep the duty of any channel to fade it.
4. Write address 5 with `0b0000` to disable every channel, `0b1111` to enable them all.

A cocotb testbench in `test/` checks the reset state, exact duty cycle of every channel, the complementary outputs, the prescaler and the enable mask.

## External hardware

None required. LEDs on `uo_out[3:0]` and `uo_out[7:4]` show the PWM directly. A servo or motor driver can be attached to any channel through a suitable driver stage.
