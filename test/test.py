# SPDX-FileCopyrightText: © 2026 Anirudh Sahu
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

ADDR_DUTY0 = 0
ADDR_PRESCALE = 4
ADDR_ENABLE = 5
WR = 1 << 3


async def write_reg(dut, addr, value):
    """Pulse the WR strobe (uio_in[3]) with addr on uio_in[2:0] and data on ui_in."""
    dut.ui_in.value = value
    dut.uio_in.value = addr & 0x7
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = (addr & 0x7) | WR
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = addr & 0x7
    await ClockCycles(dut.clk, 1)


async def reset(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def measure_duty(dut, ch, period_clocks):
    """Count how many clocks channel ch is high over one full PWM period."""
    high = 0
    for _ in range(period_clocks):
        await RisingEdge(dut.clk)
        high += (int(dut.uo_out.value) >> ch) & 1
    return high


@cocotb.test()
async def test_reset_state(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await reset(dut)
    # all duties are 0 after reset so every PWM output is low and every
    # inverted output is high
    await ClockCycles(dut.clk, 4)
    assert int(dut.uo_out.value) == 0xF0
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uio_out.value) == 0


@cocotb.test()
async def test_duty_cycles(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await reset(dut)

    duties = [0, 64, 128, 255]
    for ch, d in enumerate(duties):
        await write_reg(dut, ADDR_DUTY0 + ch, d)

    # prescale 0 means the PWM counter advances every clock, period = 256 clocks
    await ClockCycles(dut.clk, 300)
    for ch, d in enumerate(duties):
        high = await measure_duty(dut, ch, 256)
        dut._log.info(f"ch{ch} duty={d} high={high}/256")
        assert high == d, f"channel {ch}: expected {d} high clocks, got {high}"


@cocotb.test()
async def test_inverted_outputs(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await reset(dut)
    await write_reg(dut, ADDR_DUTY0 + 1, 100)
    await ClockCycles(dut.clk, 10)
    for _ in range(300):
        await RisingEdge(dut.clk)
        v = int(dut.uo_out.value)
        assert ((v >> 1) & 1) != ((v >> 5) & 1), "uo_out[5] must be the inverse of uo_out[1]"


@cocotb.test()
async def test_prescaler(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await reset(dut)
    await write_reg(dut, ADDR_PRESCALE, 3)  # counter advances every 4 clocks
    await write_reg(dut, ADDR_DUTY0, 32)
    await ClockCycles(dut.clk, 1100)
    high = await measure_duty(dut, 0, 256 * 4)
    dut._log.info(f"prescaled high={high}/1024")
    assert high == 32 * 4


@cocotb.test()
async def test_enable_mask(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    await reset(dut)
    await write_reg(dut, ADDR_DUTY0 + 2, 200)
    await write_reg(dut, ADDR_ENABLE, 0b1011)  # disable channel 2
    await ClockCycles(dut.clk, 300)
    high = await measure_duty(dut, 2, 256)
    assert high == 0, "disabled channel must stay low"
    await write_reg(dut, ADDR_ENABLE, 0b1111)
    await ClockCycles(dut.clk, 300)
    high = await measure_duty(dut, 2, 256)
    assert high == 200
