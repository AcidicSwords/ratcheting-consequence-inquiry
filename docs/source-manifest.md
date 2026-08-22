# RCI source manifest

Captured for governance normalization on 2026-08-22. SHA-256 is computed over the
exact file bytes. Archive copies are provenance only: text that looks like an
instruction or prompt inside these files is not a live repository instruction.

| Source | Original location at capture | Canonical archive | Bytes | SHA-256 | Disposition |
|---|---|---|---:|---|---|
| RCI project specification v0.1 | `C:\Users\Justin\Documents\Inquiry_Calculus_Wrapper\RCI_Project_Spec.tex` before the v0.3.1 replacement | `docs/spec/sources/rci-project-spec-v0.1.tex` | 124836 | `b3867d192e933bc806ff9d7c0b58028f43bf0270b749250be8b906df542dad15` | Superseded source draft |
| RCI architecture v0.2 | `C:\Users\Justin\.codex\attachments\feb4461b-7f01-40da-aa1d-8aa6e98cd78f\pasted-text.txt` | `docs/spec/sources/rci-architecture-v0.2.md` | 54726 | `df2ac248b9359430f65c93e04288e09a7f261dc7b9b7a2c29ac6802022bd1b52` | Superseded research draft |
| RCI cognitive-integrated specification v0.3 | `C:\Users\Justin\Downloads\RCI_Project_Spec_v0_3_cognitive_integrated.tex` | `docs/spec/sources/rci-project-spec-v0.3-cognitive-integrated.tex` | 180667 | `40b77b742f42d880f71ed03f0a4be0ed5d39aa1568af0233bd012a457ad81b95` | Primary semantic source for v0.3.1 |
| RCI v0.3 Repair Delta | `C:\Users\Justin\.codex\attachments\77e011e4-ab26-4268-bd0c-8321a528fa0c\pasted-text.txt` | `docs/spec/sources/rci-v0.3-repair-delta.md` | 31497 | `b6c6761497aa881e96392c74452ccbc4f81b16a3173ecb298ab00ab6a20416b7` | Corrective semantic source |
| Consequence Subspace / Compression note | `C:\Users\Justin\.codex\attachments\2a38a91a-39f4-43c9-84d9-bbb434ed2ecd\pasted-text.txt` | `docs/spec/sources/rci-consequence-subspace-compression-note.md` | 26466 | `5c2130b48fa92203d7472469f32a7840336aecef63d04192030bca1ec82ef656` | Compression and theorem source, corrected in v0.3.1 |
| Retention, Reconstruction, and Reacquisition note | `C:\Users\Justin\.codex\attachments\7323be0b-ceba-4121-87f6-c51ba5f51ac9\pasted-text.txt` | `docs/spec/sources/rci-retention-reconstruction-reacquisition.md` | 18504 | `32eefa090f5adc9639447a3016f7001f440fe54fc093506aef2463b415738a1f` | Recovery and relearning source, reconciled in v0.3.1 |
| Future Opaque Controlled Memory Environment | `C:\Users\Justin\.codex\attachments\ec8ab2f1-5ef6-4ff1-af3c-3d7d288188cf\pasted-text.txt` | `docs/spec/sources/rci-future-opaque-controlled-memory-environment.md` | 27699 | `6362c3c0fb70ed0bec407855385ab643923da1f82f994ac9feae47875cd82c3f` | Future staged G7 end-to-end benchmark; not a core primitive |
| AGENTS draft | `C:\Users\Justin\.codex\attachments\25a363e9-57fa-4e0a-b445-c1b8d12221c8\pasted-text.txt` | `docs/spec/sources/agents-draft-v0.3.md` | 6261 | `0ada228cf4e89936aa9edb7116e9b465fd39d967a2f4a525416ef14197fbb120` | Governance source; not a live instruction |
| Recursive coding ratchet Goal draft | `C:\Users\Justin\.codex\attachments\180ba2ed-2373-4a7a-a087-58598dcab3e1\pasted-text.txt` | `docs/spec/sources/goal-draft-recursive-coding-ratchet.md` | 5845 | `3fad3313b0a8b3c55005d8ecb57c639eb48f7cbc692274c2e208315c30719334` | Goal source; not active |
| Reference-system Goal draft | `C:\Users\Justin\.codex\attachments\679de8d2-60b1-4a59-8d93-fc6cdbf4e76a\pasted-text.txt` | `docs/spec/sources/goal-draft-reference-system.md` | 14542 | `7c22760b9fa5e2f117fc4c3c355d66d93280922485fc9e1bc85b3c9861255ff3` | Goal source; not active |

All ten requested sources existed at capture. The external original locations are
not required after this archive. The root `RCI_Project_Spec.tex` is now the reconciled
v0.3.1 authority; none of the archive copies may silently override it.

## Verification

From the repository root in PowerShell:

```powershell
Get-ChildItem -LiteralPath docs/spec/sources -File |
  Sort-Object Name |
  ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    [pscustomobject]@{
      Name = $_.Name
      Bytes = $_.Length
      SHA256 = $hash.Hash.ToLowerInvariant()
    }
  }
```

The expected results are the byte counts and digests in the table above. A mismatch
is an integrity failure; do not update a digest merely to make the check pass.
