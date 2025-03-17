# Dual-Mode Project Structure - Implementation Plan

## Overview

This plan outlines steps to enhance The Aichemist Codex to function seamlessly
as both a standalone project and an installable package. The improvements follow
modern Python project structure best practices while maintaining compatibility
with existing code.

## Phase 1: Initial Assessment

1. **Inventory Existing Structure**

   - ✓ Verify `src` layout is already implemented
   - ✓ Check for existing environment detection code
   - ✓ Review current directory management approach
   - ✓ Assess import patterns in key modules

2. **Gap Analysis**
   - ✓ Identify missing package architecture components
   - ✓ Evaluate entry point configurations
   - ✓ Assess documentation needs
   - ✓ Evaluate testing structure

## Phase 2: Core Infrastructure

1. **Environment Detection**

   - [ ] Create `environment.py` utility for detecting mode
   - [ ] Implement `is_development_mode()` function
   - [ ] Implement `get_project_root()` function

2. **Directory Management**

   - [ ] Enhance `DirectoryManager` class (if exists) or create new one
   - [ ] Implement environment variable support
   - [ ] Add directory validation and repair utilities
   - [ ] Create directory structure documentation file

3. **Application Entry Points**
   - [ ] Update CLI module to work in both modes
   - [ ] Create `__main__.py` for direct execution
   - [ ] Setup proper executable scripts in `bin/` directory

## Phase 3: Documentation & Configuration

1. **Development Guide**

   - [ ] Create DEVELOPMENT.md with dual-mode usage instructions
   - [ ] Document environment variables and configuration
   - [ ] Add examples for running in both modes

2. **Project Configuration**
   - [ ] Update pyproject.toml for proper package discovery
   - [ ] Add development tool configurations
   - [ ] Create Makefile for common tasks

## Phase 4: Testing & Validation

1. **Test Organization**

   - [ ] Review and organize test directory structure
   - [ ] Add tests for both execution modes
   - [ ] Ensure tests run in both installed and development modes

2. **Validation**
   - [ ] Verify package installation works
   - [ ] Verify direct execution works
   - [ ] Test environment variable overrides
   - [ ] Validate import patterns work consistently

## Implementation Priority

1. Environment detection utilities (core functionality)
2. Directory manager enhancements (foundation for data access)
3. Entry points for dual-mode execution (user interface)
4. Documentation and configuration updates (developer experience)
5. Testing and validation (quality assurance)
