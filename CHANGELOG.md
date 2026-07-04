# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-04

### Added
- **Licensing System**: Secure client-side activation and status endpoints (`/api/license/activate` and `/api/license/status`).
- **Supabase Integration v2**: Database schema migration for licensing tracking, active plans, Stripe customer mapping, and transactional records.
- **Supabase Edge Functions**: Added `validate-license` and `stripe-webhook` serverless handlers.
- **Offline Grace Cache**: Cache system permitting voice commands for up to 72 hours if the central licensing API is unreachable.
- **One-Command Bootstrapper**: Added `scripts/bootstrap.sh` script for rapid single-command installation.
- **Detached Auto-Updater**: Implemented client-triggered self-updating process through `scripts/update.sh` detached daemon launch.
- **System Uninstaller**: Added `scripts/uninstall.sh` to fully revert installation steps, directories, services, and configs.
- **Marketing Landing Page**: Completed beautiful, responsive Stripe-integrated index page (`website/index.html` and `website/gracias.html`) ready for Vercel.
- **Share/Web Share API**: Native sheet recommendation triggers with fallback copying options.
