# Day 20 — Extensibility: CRDs, Helm Lifecycle, Kustomize, Cluster Interfaces [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day20/setup.sh`. **Score:** `bash days/day20/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d20` unless the task explicitly says otherwise.

## Exercise 20.1 — CustomResourceDefinition (15 min)

**Your mission:** Create CRD `backups.cka.io`: group `cka.io`, version `v1` (served and storage), **Namespaced**, kind `Backup`, plural `backups`, short name `bk`. Its OpenAPI schema requires `spec.schedule` (string) and allows `spec.retention` (integer, minimum 1).

**Pass when:** The CRD is Established with that scope, kind and schema.

**Check yourself:**

```bash
kubectl get crd backups.cka.io; kubectl explain backup.spec
```

## Exercise 20.2 — Custom resources and schema validation (8 min)

**Your mission:** Create Backup `nightly` with schedule `0 2 * * *` and retention `7`. Then try to create Backup `broken` with retention `0` and save the API server's rejection to `answers/day20-invalid.txt`.

**Pass when:** `nightly` exists with the right spec; `broken` was rejected by the schema.

**Check yourself:**

```bash
kubectl -n cka-d20 get bk
```

## Exercise 20.3 — Helm upgrade and rollback (15 min)

**Your mission:** Install `charts/mini-web` as release `rollback-web`. Upgrade it with image tag `does-not-exist` and watch the rollout fail. Roll the release back to revision 1.

**Pass when:** History shows install, failed-image upgrade and a rollback to 1; Deployment `mini-web` is Ready on `nginx:1.27`.

**Check yourself:**

```bash
helm -n cka-d20 history rollback-web
```

## Exercise 20.4 — Write your own Kustomize overlay (15 min)

**Your mission:** Under `answers/day20-kustomize/`, build a base from `materials/kustomize/base` and an overlay `overlays/prod` that sets namespace `cka-d20`, name prefix `prod-`, label `env=prod` on everything, and generates ConfigMap `web-config` with `MODE=prod`. Apply the overlay.

**Pass when:** Deployment `prod-overlay-web` Ready with label `env=prod`; a generated `prod-web-config-<hash>` ConfigMap holds `MODE=prod`.

**Check yourself:**

```bash
kubectl kustomize answers/day20-kustomize/overlays/prod
```

## Exercise 20.5 — Identify CRI, CNI and storage plumbing (8 min)

**Your mission:** Find the container runtime (with version) the nodes use, the CNI plugin that provides Pod networking, and the provisioner behind the default StorageClass. Write all three into `answers/day20-interfaces.txt`.

**Pass when:** The file names the runtime, the CNI and the provisioner correctly.

**Check yourself:**

```bash
kubectl get nodes -o wide; kubectl get storageclass
```

## End of day

Run:

```bash
bash days/day20/verify.sh
```
