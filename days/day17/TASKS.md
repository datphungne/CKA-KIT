# Day 17 — Pod Design, Security Context & StatefulSets [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day17/setup.sh`. **Score:** `bash days/day17/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d17` unless the task explicitly says otherwise.

## Exercise 17.1 — Init container (12 min)

**Your mission:** Create Pod `init-web`: an init container `prepare` (`busybox:1.36`) writes the text `ready from init` to `index.html` in an `emptyDir` volume, and the main container `nginx` (`nginx:1.27`) serves that volume from `/usr/share/nginx/html`.

**Pass when:** Pod Running and nginx serves exactly `ready from init`.

**Check yourself:**

```bash
kubectl -n cka-d17 exec init-web -- cat /usr/share/nginx/html/index.html
```

## Exercise 17.2 — Native sidecar and container logs (12 min)

**Your mission:** Create Pod `log-pair`. Container `app` (`busybox:1.36`) appends `tick <n>` to `/var/log/app/app.log` every 2 seconds. A **native sidecar** `log-tail` (an init container with `restartPolicy: Always`) streams that file to its stdout. Both share an `emptyDir`.

**Pass when:** Pod Running and `kubectl logs log-pair -c log-tail` shows ticks.

**Check yourself:**

```bash
kubectl -n cka-d17 logs log-pair -c log-tail --tail=3
```

## Exercise 17.3 — Security context (12 min)

**Your mission:** Create Pod `secure-pod` (`busybox:1.36`, `sleep 86400`) that runs as user `1000`, group `3000`, `fsGroup` `2000`, with `runAsNonRoot`, no privilege escalation, a read-only root filesystem and **all** Linux capabilities dropped.

**Pass when:** Pod Running as UID 1000 with every listed setting present.

**Check yourself:**

```bash
kubectl -n cka-d17 exec secure-pod -- id
```

## Exercise 17.4 — Pod Security Admission (10 min)

**Your mission:** Label namespace `cka-d17` so Pod Security Admission **enforces** `baseline` and **warns** on `restricted`. Prove it: try to create a privileged Pod `priv-test` and save the rejection message to `answers/day17-psa.txt`.

**Pass when:** Namespace labels set, `priv-test` does not exist, and the file shows the PodSecurity violation.

**Check yourself:**

```bash
kubectl get ns cka-d17 --show-labels
```

## Exercise 17.5 — StatefulSet with headless Service (15 min)

**Your mission:** Create headless Service `db-headless` (port 80, selector `app=db`) and StatefulSet `db` (`nginx:1.27`, 2 replicas, `serviceName: db-headless`) with a `volumeClaimTemplates` entry `data` (100Mi, mounted at `/usr/share/nginx/html`). Resolve `db-0.db-headless.cka-d17.svc.cluster.local` from a Pod and save the output to `answers/day17-dns.txt`.

**Pass when:** 2/2 replicas Ready, claims `data-db-0` and `data-db-1` Bound, Service is headless, per-Pod DNS name recorded.

**Check yourself:**

```bash
kubectl -n cka-d17 get sts,pvc,svc
```

## End of day

Run:

```bash
bash days/day17/verify.sh
```
