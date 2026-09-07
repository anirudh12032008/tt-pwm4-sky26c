/*
 * Copyright (c) 2026 Anirudh Sahu
 * SPDX-License-Identifier: Apache-2.0
 *
 * tt_um_anirudh12032008_pwm4
 * Four channel 8 bit PWM generator with a shared 8 bit prescaler,
 * per channel enable mask and complementary (inverted) outputs.
 *
 * Register write interface (all inputs sampled on rising clk):
 *   ui_in[7:0]  : data byte
 *   uio_in[2:0] : register address
 *                 0..3  duty for channel 0..3 (0 = always low, 255 = 255/256 high)
 *                 4     prescaler (PWM counter advances once every (P+1) clocks)
 *                 5     enable mask, bit n enables channel n
 *                 6,7   unused
 *   uio_in[3]   : WR strobe, register is written on the rising edge of this bit
 *
 * Outputs:
 *   uo_out[3:0] : PWM channel 0..3
 *   uo_out[7:4] : inverted PWM channel 0..3 (for complementary drive)
 */

`default_nettype none

module tt_um_anirudh12032008_pwm4 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // ---------------------------------------------------------------
  // Register file
  // ---------------------------------------------------------------
  reg [7:0] duty0, duty1, duty2, duty3;
  reg [7:0] prescale;
  reg [3:0] en_mask;

  wire [2:0] addr = uio_in[2:0];
  wire       wr   = uio_in[3];
  reg        wr_d;
  wire       wr_edge = wr & ~wr_d;

  always @(posedge clk) begin
    if (!rst_n) begin
      wr_d     <= 1'b0;
      duty0    <= 8'd0;
      duty1    <= 8'd0;
      duty2    <= 8'd0;
      duty3    <= 8'd0;
      prescale <= 8'd0;
      en_mask  <= 4'b1111;
    end else begin
      wr_d <= wr;
      if (wr_edge) begin
        case (addr)
          3'd0: duty0    <= ui_in;
          3'd1: duty1    <= ui_in;
          3'd2: duty2    <= ui_in;
          3'd3: duty3    <= ui_in;
          3'd4: prescale <= ui_in;
          3'd5: en_mask  <= ui_in[3:0];
          default: ;
        endcase
      end
    end
  end

  // ---------------------------------------------------------------
  // Prescaler and free running 8 bit PWM counter
  // ---------------------------------------------------------------
  reg [7:0] pre_cnt;
  reg [7:0] pwm_cnt;
  wire      tick = (pre_cnt == prescale);

  always @(posedge clk) begin
    if (!rst_n) begin
      pre_cnt <= 8'd0;
      pwm_cnt <= 8'd0;
    end else begin
      if (tick) begin
        pre_cnt <= 8'd0;
        pwm_cnt <= pwm_cnt + 8'd1;
      end else begin
        pre_cnt <= pre_cnt + 8'd1;
      end
    end
  end

  // ---------------------------------------------------------------
  // Compare stage, registered so outputs are glitch free
  // ---------------------------------------------------------------
  reg [3:0] pwm;
  always @(posedge clk) begin
    if (!rst_n) begin
      pwm <= 4'b0000;
    end else begin
      pwm[0] <= en_mask[0] & (pwm_cnt < duty0);
      pwm[1] <= en_mask[1] & (pwm_cnt < duty1);
      pwm[2] <= en_mask[2] & (pwm_cnt < duty2);
      pwm[3] <= en_mask[3] & (pwm_cnt < duty3);
    end
  end

  assign uo_out  = {~pwm, pwm};
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in[7:4], 1'b0};

endmodule
