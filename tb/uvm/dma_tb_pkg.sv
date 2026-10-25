// UVM verification package for the ADAS DMA subsystem
`timescale 1ns/1ps
package dma_tb_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import dma_pkg::*;

  `include "dma_tb_items.svh"
  `include "dma_tb_agents.svh"
  `include "dma_tb_env.svh"
  `include "dma_tb_seqs.svh"
  `include "dma_tb_tests.svh"
endpackage
