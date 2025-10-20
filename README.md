# CI-tron GitHub Action

GitHub Actions integration for [CI-tron](https://gitlab.freedesktop.org/gfx-ci/ci-tron), enabling bare-metal testing on GitHub Actions runners.

## Overview

CI-tron is a bare-metal testing framework that allows you to run tests on physical hardware. This action provides a seamless integration for GitHub Actions, bringing the power of bare-metal testing to your GitHub workflows.

## Features

- **Container-based testing** on bare-metal hardware
- **Boot2Container (B2C)** support for transparent testing
- **Diskless operation** for systems without local storage
- **Low-level testing** for kernel, bootloader, and firmware development
- **Multiple platform support**: x86_64, ARM64, ARM32, RISC-V

## Sub-Actions

This action provides three different modes of operation:

### 1. Boot2Container (`ci-tron-b2c-job`) - Recommended

The easiest way to run containerized tests on bare-metal hardware.

**Best for:**
- Application testing
- Integration testing
- General-purpose bare-metal testing

### 2. Diskless Boot2Container (`ci-tron-b2c-diskless-job`)

Same as Boot2Container but operates without local storage, using network-based storage.

**Best for:**
- Systems without local storage
- Testing in constrained environments
- Shared infrastructure scenarios

### 3. Low-Level (`ci-tron-job`)

Fewer defaults mode, geared towards low-level testing such as kernel, bootloader, or firmware development.

**Best for:**
- Kernel development and testing
- Bootloader development
- Firmware testing
- Low-level hardware validation

## Resources

- [CI-tron Documentation](https://gitlab.freedesktop.org/gfx-ci/ci-tron)
- [Boot2Container Project](https://gitlab.freedesktop.org/gfx-ci/boot2container)
- [Issue Tracker](https://github.com/gfx-ci/ci-tron-action/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This action is a GitHub Actions wrapper for CI-tron, developed by the gfx-ci team at freedesktop.org.
