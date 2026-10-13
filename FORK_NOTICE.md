# Fork attribution and permission status

This repository is an independent GitHub fork of
[BeyondTomrrow/2K5Remade](https://github.com/BeyondTomrrow/2K5Remade), maintained
under [cosmokay1](https://github.com/cosmokay1). The native Windows port, runtime,
generated game-code work, tools, and original documentation come from upstream
and its contributors. Upstream history and existing third-party notices are
preserved. No upstream endorsement, official game affiliation, or new ownership
of upstream work is claimed.

## Our additions

The `codex/franchise-negotiation` branch adds the original Python franchise AI
prototype (`franchise/`), its tests/examples, Google configuration and remote
control, save-diff/audit utilities, original native pipe transport/checks
(`native/franchise_bridge/`), and associated documentation. Developed for
cosmokay1 with Codex assistance. These additions have not been connected to
Remade's franchise functions. See [prototype documentation](docs/FRANCHISE-AI.md)
and [money audit](docs/franchise-money-audit.md).

Base reviewed for the original integration audit:
`579c72b58153c37ceb9cf20502f9ac81a3de6f4e`. Repository ancestry, rather than an
independent source snapshot or rewritten history, identifies upstream provenance.
The fork development branch starts from current upstream commit
`b9131cd2b78973dc06cddd327f0d70943ba8565c`; the audit retains its original
revision labels rather than presenting an earlier inspection as a new one.

## Research and third-party credit

- BAD-AL's [nfl2k5tool_dart](https://github.com/BAD-AL/nfl2k5tool_dart), revision
  `e3afeece61896380a95e506ab43ae1abda0ae8a5`, informed the save-layout investigation.
  Its source checkout and executable are not added by this branch. The binary
  comparison utility does not incorporate its parser or assert contract offsets.
  Preserve [upstream converter credit](docs/third-party/nfl2k5tool-NOTICE.txt).
- Preserve upstream [third-party notices](docs/third-party/) and bundled license
  files, including the 2K Football Mod Tools, extract-xiso, Kenney, and mod-package
  notices. This document does not replace their terms or claim rights to their
  branding, media, or other assets.
- Google Gen AI is an optional externally installed SDK; we do not vendor it.
  Modern contract research links to NFL/NFLPA sources; no CBA PDF is bundled.

## Permission status — checked October 13, 2026

No top-level license granting general reuse/redistribution was found in Remade;
GitHub's repository API reports `license: null`. GitHub allows its public
repository fork mechanism, but that does not establish permission to distribute
modified game builds or relicense inherited code. See
[GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

BAD-AL's converter also lacks explicit redistribution terms in the inspected
source. Upstream already records this in [SAVE-LIBRARY.md](docs/SAVE-LIBRARY.md).
Attribution alone does not supply missing permission. No blanket license has
been added to this fork and no new installer or binary release is published by
this work. Permission scope must be resolved with the relevant rights holders
before distributing such artifacts.

The fork continues upstream's requirement that users provide their own legally
obtained game. This work adds no retail executable, ISO, save, or game assets.
It does not represent a legal clearance of inherited generated code or media.

## Before a release

Obtain an explicit upstream license/permission covering the intended modified
source and binary distribution. Separately resolve any converter and asset
permissions needed for that release. Preserve applicable notices in the shipped
artifact, identify our modifications/version, and retain evidence of the grants.
Choose a license for our original additions separately; do not apply it to
inherited components without authority. Maintain the independent-fork wording.

No permission request has been sent to any maintainer. A draft is available in
[upstream-permission-request.md](docs/upstream-permission-request.md).
