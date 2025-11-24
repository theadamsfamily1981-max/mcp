# FPGA Salvage Tool

Repurpose cryptocurrency mining FPGAs and ATCA telecom boards for AI research.

## 🤖 One-Click AI Automation (EASIEST!)

**NEW:** Fully automated salvage - just take a photo!

```bash
# 1. Take photo of your board (top-down view)
# 2. Run auto salvage:
python3 ai/auto_salvage.py board_photo.jpg

# That's it! AI will:
# ✓ Detect hardware (computer vision)
# ✓ Generate JTAG config (automatic)
# ✓ Erase mining firmware (jailbreak)
# ✓ Run diagnostics (validation)
# ✓ Generate report (next steps)
```

**Features**:
- 🧠 **AI board detection** - Identify FPGA from photo (OCR + CV)
- 🔧 **Auto configuration** - Zero manual setup
- 🩺 **AI diagnostics** - Troubleshoot errors with GPT-4/Claude
- ⚡ **One command** - Complete workflow in 5-10 minutes

**See:** [ai/README.md](ai/README.md) for full AI automation docs

## 🌐 Easy Web GUI (Also Great!)

```bash
# One-command setup and launch:
cd gui/
sudo ./setup_gui.sh

# Then open your browser to: http://localhost:5000
```

**Features**:
- 📱 Modern web interface (works on phone/tablet too!)
- 🧙 Step-by-step wizard
- 📊 Real-time progress updates
- ⚡ Voltage tuning with sliders
- 🔍 Auto hardware detection
- 📜 Live log viewer

## 💻 Command Line (Advanced)

```bash
# Test JTAG connection (safe, no modifications)
sudo ./fpga_salvage.py --vendor stratix10 --skip-erase

# Full salvage (erases mining firmware)
sudo ./fpga_salvage.py --vendor stratix10

# Voltage tuning (after salvage)
sudo ./scripts/pmic_flasher.py --bus 0 --read
sudo ./scripts/pmic_flasher.py --bus 0 --preset safe
```

## Supported Devices

### Cryptocurrency Mining FPGAs
- **Intel Stratix 10** (10SX/10GX): `--vendor stratix10`
- **Intel Arria 10** (GX/SX): `--vendor arria10` 🆕
- **Xilinx Virtex UltraScale+** (VU9P/VU13P): `--vendor virtex`
- **Xilinx Kintex UltraScale+** (KU5P/KU15P): `--vendor kintex`

### Mining Hashboards 🔥
- **4x Agilex Hashboards** (Linzhi Phoenix, Chinese miners): `--vendor hashboard-agilex`
  - 4 chips in JTAG chain: **5.6M logic cells total!**
  - 128GB DDR4, perfect for massive SNN models
  - Cost: $200-400 used (vs $60,000 new equivalent!)
- **PCIe Mining Cards** (VU33P/VU35P/VU37P): `--vendor pcie-mining-card`
  - Single high-end chip, 1.2-2M cells
  - PCIe Gen3/4 interface, 64GB DDR4
  - Cost: $500-1,200 (vs $6,000 new)

### Enterprise PCIe Accelerators 🆕
- **BittWare A10PED** (Dual Arria 10 GX1150): `--vendor bittware-a10ped`
  - 2x FPGAs, 32GB DDR4, PCIe Gen3 x8
  - Perfect for AI inference with OpenCL/OpenVINO
  - Cost: $800-2,000 used (vs $4,000-8,000 new)
  - **See:** [Arria 10 Salvage Guide](../../docs/ARRIA10_SALVAGE_GUIDE.md) 📖

### ATCA Telecom Boards
- **ATCA Virtex-7** (Emerson, Radisys, Mercury): `--vendor atca-virtex7`
- **ATCA Virtex-6** (Kontron, older boards): `--vendor atca-virtex6`
- **ATCA Stratix IV/V** (NAT Semi, Mercury): `--vendor atca-stratix4`
- **ATCA Arria 10** (Advantech, Trenton): `--vendor atca-arria10`

### 🔥 EXTREME TIER (Advanced Users Only) 🔥
- **Superscalar K10 / COL Engine P2** (1700W mining beasts)
  - Likely VU37P, Stratix 10 GX2800, or Agilex AGF027
  - **Extreme difficulty**: Security lockouts, 1700W power, intensive reverse engineering
  - Cost: $2,000-5,000 used (vs $35,000-60,000 new FPGA)
  - **⚠️ HIGH RISK**: Requires advanced skills, industrial power, potential hardware destruction
  - **See:** [K10/P2 Extreme Guide](../../docs/K10_P2_EXTREME_SALVAGE_GUIDE.md) ⚡

**What is a Hashboard?** The compute module from a cryptocurrency miner - typically 2-4 high-end FPGAs on one board. Mining crash = incredible deals!

**What is ATCA?** Advanced Telecommunications Computing Architecture - enterprise telecom boards with powerful FPGAs. Decommissioned boards sell for $200-$2,000 vs $10,000-$50,000 new!

**What is Extreme Tier?** Ultra-high-end mining FPGAs (1700W+) requiring reverse engineering, industrial power, and advanced expertise. Only for experienced FPGA engineers willing to accept high financial and safety risks.

## Directory Structure

```
fpga_salvage/
├── fpga_salvage.py          # Main salvage tool
├── ai/                      # 🤖 AI-powered automation (NEW!)
│   ├── auto_salvage.py      # One-click salvage workflow
│   ├── board_detector.py    # Computer vision board detection
│   ├── diagnostic_assistant.py  # LLM-powered troubleshooting
│   ├── requirements.txt     # AI dependencies
│   └── README.md            # AI automation docs
├── configs/                 # OpenOCD JTAG configurations
│   ├── stratix10.cfg
│   ├── arria10_bittware_a10ped.cfg  ← NEW (Arria 10 dual-FPGA)
│   ├── virtex_ultrascale.cfg
│   ├── kintex_ultrascale.cfg
│   ├── hashboard_agilex.cfg         (4x Agilex hashboards)
│   ├── pcie_mining_card.cfg         (VU33P/VU35P/VU37P)
│   ├── superscalar_k10_extreme.cfg  ← NEW (K10/P2 extreme tier)
│   ├── atca_xilinx.cfg
│   └── atca_altera.cfg
├── gui/                     # Web interface
│   ├── fpga_salvage_gui.py  # Flask server
│   ├── templates/           # HTML templates
│   └── setup_gui.sh         # One-command GUI setup
├── hardware/                # PCB designs and adapters
│   ├── jtag_breakout/       # JTAG adapter schematics
│   ├── hashboard_power/     # Power adapters
│   └── README.md            # Hardware design docs
├── bitstreams/              # Diagnostic bitstreams (generate yourself)
│   └── README.md            # Bitstream generation guide
└── scripts/                 # Helper utilities
    └── pmic_flasher.py      # Voltage/frequency tuning
```

## Requirements

### Hardware
- FPGA mining board (Stratix 10, Virtex UltraScale+, or Kintex UltraScale+)
- USB JTAG adapter:
  - Intel: USB-Blaster II
  - Xilinx: Platform Cable USB II, FT2232H, or Digilent HS2
- 12V power supply (200-400W depending on board)

### Software

**Basic (command line only):**
```bash
# Install dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install openocd i2c-tools python3
```

**AI Automation (recommended):**
```bash
# Install AI dependencies
pip install -r ai/requirements.txt

# Optional: Set up AI API key for best diagnostics
export ANTHROPIC_API_KEY='your-key-here'  # Claude (recommended)
# OR
export OPENAI_API_KEY='your-key-here'     # GPT-4 (alternative)
# Get keys from: https://console.anthropic.com/
```

**Bitstream generation (optional):**
```bash
# Intel Quartus Prime Pro (for Stratix 10)
# Xilinx Vivado (for UltraScale+)
```

## Usage

### 1. Test Connection (Safe Mode)

```bash
# This only detects the FPGA, does not modify anything
sudo ./fpga_salvage.py --vendor stratix10 --skip-erase
```

### 2. Full Salvage Procedure

```bash
# WARNING: This erases the proprietary mining firmware!
sudo ./fpga_salvage.py --vendor stratix10

# You will be prompted:
# ⚠️  Erase proprietary bootloader? (yes/no): yes
```

### 3. Voltage Tuning (Optional)

```bash
# Read current PMIC settings
sudo ./scripts/pmic_flasher.py --bus 0 --read

# Set to efficient preset (0.80V for lower power AI inference)
sudo ./scripts/pmic_flasher.py --bus 0 --preset efficient

# Or set custom voltage
sudo ./scripts/pmic_flasher.py --bus 0 --voltage 0.85
```

## Safety Guidelines

### ⚠️  Voltage Limits
- **Safe range**: 0.80V - 0.89V (VCCINT)
- **Nominal**: 0.85V
- **DO NOT** exceed 0.95V (can damage FPGA)
- **DO NOT** go below 0.75V (may cause instability)

### ⚠️  Thermal Management
- **Idle**: <65°C (good)
- **Load**: <85°C (acceptable)
- **Max**: <100°C (dangerous, reduce voltage or improve cooling)

### ⚠️  Legal
- ✅ Only use on hardware you own
- ✅ Educational/research purposes
- ❌ Do not extract proprietary bitstreams
- ❌ Do not access hardware you don't own

## Troubleshooting

### Issue: "JTAG connection failed"
```bash
# Check board power
# Verify JTAG adapter: lsusb | grep -i ftdi

# Try slower JTAG speed
# Edit configs/stratix10.cfg: adapter speed 1000
```

### Issue: "No bitstream found"
```bash
# Generate diagnostic bitstream (see bitstreams/README.md)
# OR skip bitstream and use JTAG-only mode
sudo ./fpga_salvage.py --vendor stratix10 --skip-erase
```

### Issue: "PMIC not detected"
```bash
# List I2C buses
i2cdetect -l

# Scan for devices
sudo i2cdetect -y 0  # Try bus 0, 1, 2, etc.

# Look for addresses like 0x60, 0x70 (PMICs)
```

## Examples

### Example 1: Salvage Stratix 10 from Ethereum Miner
```bash
# 1. Connect JTAG (USB-Blaster to 10-pin header)
# 2. Power on board (12V, check LED indicator)

# 3. Test connection
sudo ./fpga_salvage.py --vendor stratix10 --skip-erase

# 4. Erase mining firmware
sudo ./fpga_salvage.py --vendor stratix10
# Answer "yes" to erase prompt

# 5. Tune voltage for AI workloads
sudo ./scripts/pmic_flasher.py --bus 0 --preset safe

# 6. Verify
sudo ./scripts/pmic_flasher.py --bus 0 --read
```

### Example 2: Salvage Xilinx VCU1525 (VU9P)
```bash
# 1. Connect JTAG (FT2232H to 14-pin header)
# 2. Power on via PCIe or 12V barrel jack

# 3. Salvage
sudo ./fpga_salvage.py --vendor virtex

# 4. Check PMIC (if available)
sudo ./scripts/pmic_flasher.py --bus 1 --read
```

## Integration with SNN Kernel

After salvaging, integrate with the main SNN kernel system:

```bash
# 1. Build kernel module
cd /path/to/mcp
make

# 2. Load module
sudo modprobe snn_kernel_core

# 3. Verify FPGA detection
lspci | grep -i fpga
# Should show: 01:00.0 Processing accelerators: Intel/Xilinx Device...

# 4. Program AI bitstream (see docs/ARCHITECTURE.md)
aocl program acl0 my_snn_kernel.aocx  # Intel OpenCL
# OR
xbutil program -d 0 -u my_snn_kernel.xclbin  # Xilinx Vitis
```

## Contributing

Found a bug? Have a mining board we don't support?

1. Open an issue: [GitHub Issues](https://github.com/your-repo/mcp/issues)
2. Submit a PR with:
   - New OpenOCD config
   - PMIC driver
   - Diagnostic bitstream

## Screenshots

### Web GUI
![FPGA Salvage Web GUI](../../docs/images/fpga_salvage_gui.png)
*(Modern, easy-to-use interface - no command line required!)*

## Resources

### Salvage Guides
- **Mining FPGA Guide**: [docs/FPGA_SALVAGE_GUIDE.md](../../docs/FPGA_SALVAGE_GUIDE.md)
- **Hashboard Guide**: [docs/HASHBOARD_SALVAGE_GUIDE.md](../../docs/HASHBOARD_SALVAGE_GUIDE.md)
- **Arria 10 Guide**: [docs/ARRIA10_SALVAGE_GUIDE.md](../../docs/ARRIA10_SALVAGE_GUIDE.md) 🆕
  - BittWare A10PED dual-FPGA cards
  - OpenCL + OpenVINO deployment
  - Open source project integration
- **ATCA Board Guide**: [docs/ATCA_SALVAGE_GUIDE.md](../../docs/ATCA_SALVAGE_GUIDE.md)
- **K10/P2 Extreme Guide**: [docs/K10_P2_EXTREME_SALVAGE_GUIDE.md](../../docs/K10_P2_EXTREME_SALVAGE_GUIDE.md) ⚡
  - **⚠️ Advanced only** - 1700W, reverse engineering required
  - Security exploitation, industrial power, high risk

### Hardware & AI
- **Hardware Adapters**: [hardware/](hardware/)
  - JTAG breakout boards
  - Power adapters for hashboards
  - Multi-chip JTAG splitters
  - PCB designs + schematics
- **AI Workload Examples**: [examples/fpga_ai_workloads/](../../examples/fpga_ai_workloads/)
  - SNN accelerators, CNN engines, GNN, transformers
  - Full source code + build scripts
  - Performance benchmarks vs GPU

### Technical Docs
- **API Documentation**: [docs/API_GUIDE.md](../../docs/API_GUIDE.md)
- **Architecture**: [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
- **Business Roadmap**: [docs/NEXT_LEVEL_ROADMAP.md](../../docs/NEXT_LEVEL_ROADMAP.md)

## License

GPL-3.0 (compatible with Linux kernel modules)

---

**Disclaimer**: This tool is for educational and research purposes on hardware you legally own. Always follow local laws and respect intellectual property.
