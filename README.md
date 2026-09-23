# LiveContainer AutoRefresh Dicky

Custom build pipeline for **LiveContainer 3.8.10 + embedded SideStore**.

This project keeps the official LiveContainer 3.8.10 source as the baseline and uses the Auto-Refresh/CoreDevice build work from NRG-Wardog/sidestore-auto-refresh.

## Goal

- LocalDevVPN / CoreDevice / CDTunnel / RSD transport
- Native SideStore auto-refresh
- Background refresh scheduling
- Refresh verification and diagnostics
- Preserve the official LiveContainer 3.8.10 baseline

No pairing files, Apple credentials, certificates, provisioning profiles, or personal signing material are stored here.

## Pinned sources

- LiveContainer 3.8.10: `4dbe0f9a626de801184a42c0be8d2cb105058e3d`
- AutoRefresh builder: v3.0.2, commit `e9c772995cddfcf0b6ae10bd5aa7239e106e817c`

## Build

Open **Actions → Build LiveContainer AutoRefresh Dicky → Run workflow**.

The workflow builds on macOS/Xcode, runs source checks, builds the CoreDevice transport, builds LiveContainer and embedded SideStore, packages the IPA, and uploads it as an artifact.

The resulting IPA is not automatically signed with a personal Apple identity. Install/sign it using your normal Apple-account workflow.

## Important

A successful GitHub Actions build proves source/build/package verification. It does not guarantee that iOS will execute background tasks at an exact time; background execution is controlled by iOS.

## Upstream

- https://github.com/LiveContainer/LiveContainer
- https://github.com/NRG-Wardog/sidestore-auto-refresh
