# A10PED Neuromorphic AI Tile

**Repurposing the BittWare A10PED as a production-grade neuromorphic compute platform**

## Overview

This project transforms the BittWare A10PED dual-FPGA PCIe card into a reusable "AI tile" for spiking neural networks (SNNs), topological field networks, and neuromorphic architectures. The design emphasizes:

- **Clean host-FPGA ABI**: Simple register-based command protocol
- **Portable architecture**: Core logic vendor-agnostic, easily retargeted
- **Hybrid toolchain**: Quartus backend, open tools + AI assistance for everything else
- **Production-ready**: From research prototype to reliable accelerator

## Hardware

**BittWare A10PED Specifications:**
- 2x Intel Arria 10 GX1150 FPGAs (1.15M logic elements each)
- 16GB DDR4 total (8GB per FPGA on SO-DIMMs)
- PCIe Gen3 x8 to each FPGA
- Optional HMC and QSFP28 high-speed I/O
- Onboard USB-Blaster II for JTAG

**Acquisition:**
- Target cost: $120-2,000 (secondary market)
- See: [Arria 10 Salvage Guide](../../docs/ARRIA10_SALVAGE_GUIDE.md)

## Architecture

Each Arria 10 FPGA is treated as an independent **AI Tile** with:

```
┌─────────────────────────────────────────────────────────┐
│                    AI Tile (per FPGA)                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ PCIe HIP │→ │ ai_csr   │→ │ snn_core │             │
│  │ (Gen3x8) │  │ (regs)   │  │ (compute)│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       ↓              ↓              ↓                   │
│  ┌─────────────────────────────────────────┐           │
│  │     DDR4 EMIF Controller (8GB)          │           │
│  └─────────────────────────────────────────┘           │
│       ↓                                                 │
│  ┌─────────────────────────────────────────┐           │
│  │     On-Chip RAM (scratchpads, buffers)  │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

**Host-FPGA Command Protocol:**
1. Host writes command parameters (SRC, DST, LEN, CFG) to BAR0 registers
2. Host sets CTRL.START bit
3. FPGA executes (SNN inference, memory copy, etc.)
4. FPGA clears BUSY, sets DONE, raises interrupt (optional)
5. Host reads STATUS and results

**ABI Specification:** See `abi/ai_tile_registers.yaml`

## Project Structure

```
a10ped_neuromorphic/
├── README.md                      # This file
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # Detailed design
│   ├── BRINGUP.md                 # Bring-up procedure
│   └── RESEARCH_PLAN.md           # Milestones and roadmap
├── abi/                           # ABI specification (single source of truth)
│   ├── ai_tile_registers.yaml    # Register map
│   └── gen_code.py                # Code generator (RTL, C, docs)
├── hw/                            # Hardware (FPGA side)
│   ├── quartus/                   # Quartus projects
│   │   ├── bringup/               # Milestone 1: JTAG-to-Avalon
│   │   ├── ai_tile_v0/            # Milestone 2: PCIe + CSR
│   │   └── ai_tile_v1/            # Milestone 3: SNN core
│   ├── rtl/                       # Hand-written RTL
│   │   ├── ai_csr.v               # Control/status registers (generated)
│   │   ├── snn_core.v             # SNN compute kernel
│   │   └── utils/                 # Common modules (FIFOs, etc.)
│   └── sim/                       # Simulation/testbenches
│       ├── ai_csr_tb.sv           # CSR testbench
│       └── snn_core_tb.sv         # SNN testbench
├── sw/                            # Software (host side)
│   ├── libaictile/                # Host driver library (C)
│   │   ├── src/                   # C implementation
│   │   ├── include/               # Headers (ai_tile.h, generated)
│   │   └── tests/                 # Unit tests
│   ├── python/                    # Python bindings
│   │   ├── aictile.py             # ctypes wrapper
│   │   └── examples/              # Usage examples
│   └── tools/                     # Diagnostic tools
│       ├── ai_tile_info.py        # Device enumeration
│       ├── ai_tile_test.py        # Register read/write test
│       └── snn_benchmark.py       # Performance benchmark
├── models/                        # SNN models and datasets
│   ├── lif_mnist.py               # LIF neuron MNIST classifier
│   └── datasets/                  # Test data
└── scripts/                       # Build and setup scripts
    ├── setup_quartus.sh           # Install Quartus environment
    ├── build_all.sh               # Build hardware + software
    └── flash_fpga.sh              # Program bitstream via JTAG
```

## Development Phases

### **Phase 1: Foundation (Week 1)** ✅ **← YOU ARE HERE**

**Milestone 1.1: Project Setup**
- [x] Create directory structure
- [x] Define ABI specification (YAML)
- [ ] Generate code from ABI (RTL, C headers, docs)

**Milestone 1.2: JTAG Bring-Up**
- [ ] Quartus project: minimal JTAG-to-Avalon design
- [ ] On-chip RAM (4KB test buffer)
- [ ] Python script to read/write via JTAG
- [ ] **Success Criteria**: Read/write on-chip RAM via System Console

### **Phase 2: AI Tile v0 Shell (Weeks 2-4)**

**Milestone 2.1: Hardware Shell**
- [ ] Quartus Platform Designer system:
  - PCIe Hard IP (Gen3 x8)
  - DDR4 EMIF controller (8GB)
  - ai_csr register block
  - snn_core stub (memcopy)
- [ ] Build and test in simulation

**Milestone 2.2: Host Driver**
- [ ] C library using `uio_pci_generic`
- [ ] Python bindings (ctypes)
- [ ] Test: enumerate device, read registers

**Milestone 2.3: End-to-End Test**
- [ ] Host→FPGA memory copy command
- [ ] **Success Criteria**: Copy 1MB data through FPGA, verify integrity

### **Phase 3: SNN Core v1 (Weeks 5-8)**

**Milestone 3.1: LIF Neuron Kernel**
- [ ] Replace memcopy stub with LIF neuron array
- [ ] Support configurable parameters (threshold, leak, etc.)
- [ ] Read spike inputs from DDR, write outputs back

**Milestone 3.2: Validation**
- [ ] Testbench with known SNN model
- [ ] Compare FPGA output vs CPU reference
- [ ] **Success Criteria**: 99.9% match with CPU, <1ms latency

**Milestone 3.3: Benchmarking**
- [ ] Measure throughput (neurons/sec)
- [ ] Measure power (via PCIe, if available)
- [ ] Compare vs GPU implementation

### **Phase 4: Dual-Tile System (Weeks 9-12)**

**Milestone 4.1: Multi-Device Support**
- [ ] Host library manages both FPGAs independently
- [ ] Scheduler distributes work across tiles

**Milestone 4.2: System Integration**
- [ ] GPU co-processing experiments
- [ ] PCIe peer-to-peer DMA (if supported)

## Quick Start

### Prerequisites

**Hardware:**
- BittWare A10PED board
- Host PC with PCIe slot and Ubuntu 22.04
- USB cable for onboard USB-Blaster II

**Software:**
- Intel Quartus Prime Pro 23.4 (free evaluation)
- Python 3.8+
- OpenCL runtime (for OPAE, optional)

### Installation

```bash
# 1. Clone repository
cd /path/to/mcp
cd projects/a10ped_neuromorphic

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup Quartus environment
./scripts/setup_quartus.sh

# 4. Generate code from ABI spec
cd abi
python gen_code.py
# This creates:
#   - hw/rtl/ai_csr.v (auto-generated RTL)
#   - sw/libaictile/include/ai_tile_regs.h (C header)
#   - docs/REGISTER_MAP.md (documentation)
```

### JTAG Bring-Up (Milestone 1.2)

```bash
# 1. Build Quartus project
cd hw/quartus/bringup
quartus_sh -t build.tcl

# 2. Program FPGA via JTAG
quartus_pgm -m jtag -o "p;output_files/bringup.sof"

# 3. Test via System Console
cd ../../../sw/tools
python test_jtag_ram.py
# Expected: Successfully read/write 4KB on-chip RAM
```

### PCIe Bring-Up (Milestone 2.3)

```bash
# 1. Build AI tile v0
cd hw/quartus/ai_tile_v0
make build

# 2. Flash FPGA
make flash

# 3. Reboot host (for PCIe enumeration)

# 4. Verify PCIe detection
lspci | grep Altera
# Should show: 01:00.0 Processing accelerators: Intel Corporation Device XXXX

# 5. Load uio driver
sudo modprobe uio_pci_generic
echo "8086 XXXX" | sudo tee /sys/bus/pci/drivers/uio_pci_generic/new_id

# 6. Test host library
cd sw/python
python examples/test_memcopy.py
# Expected: 1MB memcopy through FPGA in <10ms
```

## ABI Specification

The AI tile exposes a simple register-based interface at **BAR0**:

| Offset | Name | Width | Access | Description |
|--------|------|-------|--------|-------------|
| 0x00 | CTRL | 32 | RW | Control register (START, RESET, IRQ_EN) |
| 0x04 | STATUS | 32 | RO | Status register (BUSY, DONE, ERROR) |
| 0x08 | CMD_SRC_LO | 32 | RW | Source address (DDR) [31:0] |
| 0x0C | CMD_SRC_HI | 32 | RW | Source address (DDR) [63:32] |
| 0x10 | CMD_DST_LO | 32 | RW | Destination address (DDR) [31:0] |
| 0x14 | CMD_DST_HI | 32 | RW | Destination address (DDR) [63:32] |
| 0x18 | CMD_LEN | 32 | RW | Length (bytes) |
| 0x1C | CMD_CFG | 32 | RW | Configuration (mode, params) |
| 0x20 | VERSION | 32 | RO | Hardware version |
| 0x24 | CAPABILITIES | 32 | RO | Feature flags |

**See:** `abi/ai_tile_registers.yaml` for complete specification

**See:** `docs/REGISTER_MAP.md` (auto-generated) for detailed bit fields

## Command Protocol Example

```python
import aictile

# 1. Open device
tile = aictile.AITile(device_id=0)

# 2. Setup command
tile.write_reg('CMD_SRC', 0x0000_0000)  # Source at DDR offset 0
tile.write_reg('CMD_DST', 0x0010_0000)  # Dest at offset 1MB
tile.write_reg('CMD_LEN', 1024 * 1024)  # 1MB
tile.write_reg('CMD_CFG', 0x00)         # Mode: memcopy

# 3. Execute
tile.write_reg('CTRL', 0x01)  # Set START bit

# 4. Wait for completion
while tile.read_reg('STATUS') & 0x01:  # BUSY bit
    time.sleep(0.001)

# 5. Check result
status = tile.read_reg('STATUS')
if status & 0x02:  # DONE bit
    print("Success!")
else:
    print(f"Error: {status}")
```

## Contributing

This is a research project. Contributions welcome in:

- **RTL optimization** (SNN kernels, memory controllers)
- **Host driver improvements** (OPAE integration, async I/O)
- **SNN models** (new architectures, datasets)
- **Documentation** (guides, tutorials, papers)

**See:** `docs/CONTRIBUTING.md`

## Citations

If you use this work in research, please cite:

```
@misc{a10ped_neuromorphic,
  title={A10PED Neuromorphic AI Tile: A $120 Platform for Production Neuromorphic Computing},
  author={[Your Name]},
  year={2024},
  howpublished={\url{https://github.com/[your-repo]/a10ped_neuromorphic}}
}
```

## References

- **BittWare A10PED Product Page**: https://www.bittware.com/fpga/a10ped/
- **Intel Arria 10 Handbook**: https://www.intel.com/content/www/us/en/docs/programmable/683561/
- **OPAE Documentation**: https://opae.github.io/
- **FPGA Salvage Project**: [../../README.md](../../README.md)

## License

- **Hardware (RTL)**: BSD-3-Clause
- **Software (drivers, libraries)**: MIT
- **Documentation**: CC-BY-4.0

---

**Status**: Phase 1 - Foundation (Active Development)

**Contact**: Open an issue on GitHub or ask in FPGA Salvage Discord (#a10ped-neuromorphic)
