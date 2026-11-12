#!/usr/bin/env python3
"""Read-only practical CKA lab verifier. No external Python dependencies.

The grader checks observable Kubernetes state; some administration work requires
manual proof and is explicitly labelled MANUAL, never silently marked passed.
"""
from __future__ import annotations
import json
import pathlib
import re
import subprocess
import sys
import os
import atexit
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_CONTEXT = "kind-cka-14d"
if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 14:
    sys.exit("Usage: python3 bin/grade.py <1..14>")
DAY = int(sys.argv[1]); NS = f"cka-d{DAY:02d}"


def cmd(*args: str, timeout: int = 12) -> tuple[bool, str]:
    try:
        run = subprocess.run(list(args), text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return run.returncode == 0, run.stdout.strip()


sys.path.insert(0, str(ROOT / 'lib'))
from safety import snapshot
try:
    config = snapshot(DAY)
except Exception as exc:
    sys.exit(f'REFUSED: {exc}')
os.environ['KUBECONFIG'] = config
atexit.register(lambda: pathlib.Path(config).unlink(missing_ok=True))


def obj(kind: str, name: str, ns: str | None = NS) -> dict[str, Any]:
    args = ["kubectl"] + (["-n", ns] if ns else []) + ["get", kind, name, "-o", "json"]
    good, out = cmd(*args)
    if not good:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def path(data: dict, *parts: str | int, default: Any = None) -> Any:
    cur: Any = data
    for part in parts:
        try:
            cur = cur[part]
        except (IndexError, TypeError, KeyError):
            return default
    return cur


def image(kind: str, name: str) -> str:
    r = obj(kind, name)
    p = ("spec", "template", "spec", "containers", 0, "image") if kind in ("deploy", "ds") else ("spec", "containers", 0, "image")
    return path(r, *p, default="")


def ready(kind: str, name: str, count: int = 1) -> bool:
    r = obj(kind, name)
    if not r:
        return False
    if kind == "pod":
        return path(r, "status", "phase") == "Running" and all(x.get("ready") for x in path(r, "status", "containerStatuses", default=[])) and len(path(r, "status", "containerStatuses", default=[])) > 0
    return path(r, "spec", "replicas", default=1) == count and path(r, "status", "readyReplicas", default=0) == count and path(r, "status", "updatedReplicas", default=0) == count


def all_nodes_ready() -> bool:
    good, raw = cmd("kubectl", "get", "nodes", "-o", "json")
    if not good:
        return False
    nodes = json.loads(raw).get("items", [])
    return len(nodes) >= 3 and all(not n["spec"].get("unschedulable", False) and any(c["type"] == "Ready" and c["status"] == "True" for c in n["status"]["conditions"]) for n in nodes)


def svc(name: str, selector: dict[str, str], service_port: int, target: int | None = None, node_port: int | None = None) -> bool:
    s = obj("svc", name); ports = path(s, "spec", "ports", default=[])
    return (bool(s) and all(path(s, "spec", "selector", k) == v for k, v in selector.items()) and any(p.get("port") == service_port and (target is None or p.get("targetPort") == target) and (node_port is None or p.get("nodePort") == node_port) for p in ports))


def endpoints(name: str) -> bool:
    good, raw = cmd("kubectl", "-n", NS, "get", "endpointslice", "-l", f"kubernetes.io/service-name={name}", "-o", "json")
    if not good:
        return False
    return any(ep.get("conditions", {}).get("ready", True) for item in json.loads(raw).get("items", []) for ep in item.get("endpoints", []))


def volume(name: str, size: str | None = None) -> bool:
    p = obj("pvc", name)
    return bool(p) and path(p, "status", "phase") == "Bound" and (size is None or path(p, "spec", "resources", "requests", "storage") == size)


def has_mount(pod_name: str, claim: str, at: str) -> bool:
    p = obj("pod", pod_name)
    volumes = {v.get("name") for v in path(p, "spec", "volumes", default=[]) if v.get("persistentVolumeClaim", {}).get("claimName") == claim}
    return ready("pod", pod_name) and any(m.get("name") in volumes and m.get("mountPath") == at for c in path(p, "spec", "containers", default=[]) for m in c.get("volumeMounts", []))


def proof(pod: str, filename: str, expected: str) -> bool:
    good, output = cmd("kubectl", "-n", NS, "exec", pod, "--", "cat", filename)
    return good and output == expected


def can(sa: str, verb: str, resource: str, namespace: str | None = NS) -> bool:
    args = ["kubectl", "auth", "can-i", verb, resource, "--as", f"system:serviceaccount:{NS}:{sa}"]
    if namespace:
        args += ["-n", namespace]
    good, out = cmd(*args)
    return good and out == "yes"


def policies(name: str, selected_label: dict[str, str], from_label: dict[str, str]) -> bool:
    p = obj("networkpolicy", name)
    ingresses = path(p, "spec", "ingress", default=[])
    rules = [r for ingress in ingresses for r in ingress.get("from", [])]
    ports = [p for ingress in ingresses for p in ingress.get("ports", [])]
    return bool(p) and all(path(p, "spec", "podSelector", "matchLabels", k) == v for k,v in selected_label.items()) and all(any(rule.get("podSelector", {}).get("matchLabels", {}).get(k) == v for rule in rules) for k,v in from_label.items()) and any(x.get("port") == 80 and x.get("protocol", "TCP") == "TCP" for x in ports)


def traffic(client: str, service: str, expect_success: bool = True) -> bool:
    if not ready("pod", client):
        return False
    # If no Service exists, target a backend Pod IP directly.
    target = service
    if not obj("svc", service):
        good, raw = cmd("kubectl", "-n", NS, "get", "pods", "-l", f"app={service}", "-o", "json")
        if not good:
            return False
        pods = json.loads(raw).get("items", [])
        if not pods:
            return False
        target = pods[0].get("status", {}).get("podIP", "")
        if not target:
            return False
    good, _ = cmd("kubectl", "-n", NS, "exec", client, "--", "wget", "-T", "3", "-q", "-O", "/dev/null", f"http://{target}:80", timeout=8)
    return good if expect_success else not good


def env_source(kind: str, name: str, key: str, source_type: str, source_name: str) -> bool:
    r = obj(kind, name)
    p = ("spec", "template", "spec", "containers") if kind == "deploy" else ("spec", "containers")
    envs = [e for c in path(r, *p, default=[]) for e in c.get("env", [])]
    field = "configMapKeyRef" if source_type == "configmap" else "secretKeyRef"
    return any(e.get("name") == key and e.get("valueFrom", {}).get(field, {}).get("name") == source_name for e in envs)


def probe(name: str, probe_type: str, port: int) -> bool:
    d = obj("deploy", name)
    return any(path(c, probe_type, "httpGet", "port") == port for c in path(d, "spec", "template", "spec", "containers", default=[]))


def file_contains(filename: str, *parts: str) -> bool:
    target = ROOT / "answers" / filename
    return target.is_file() and all(p in target.read_text(errors="replace") for p in parts)


def role_ok(sa: str, allowed: str, forbidden: str, resource: str) -> bool:
    return bool(obj("sa", sa)) and can(sa, allowed, resource) and not can(sa, forbidden, resource)


SAFE_USER_KEYS = {"client-certificate-data", "client-key-data", "token", "username", "password"}
SAFE_CLUSTER_KEYS = {"server", "certificate-authority-data", "tls-server-name", "insecure-skip-tls-verify"}


def learner_kubeconfig_works(filename: str) -> bool:
    """Run `kubectl cluster-info` against a learner-written kubeconfig without trusting it.

    The grader runs in the console container (which holds the Docker socket). A kubeconfig can
    make kubectl execute programs (users[].user.exec / auth-provider) or read arbitrary files
    (*-file / tokenFile keys), so only inline credentials are accepted, and kubectl reads a
    re-serialised copy so the file cannot be swapped between validation and use.
    """
    import tempfile
    import yaml
    try:
        data = yaml.safe_load((ROOT / "answers" / filename).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return False
    if not isinstance(data, dict):
        return False
    users = [u.get("user") or {} for u in data.get("users") or [] if isinstance(u, dict)]
    clusters = [c.get("cluster") or {} for c in data.get("clusters") or [] if isinstance(c, dict)]
    if not all(isinstance(u, dict) and set(u) <= SAFE_USER_KEYS for u in users):
        print("  [INFO] kubeconfig rejected: only inline credentials (no exec/auth-provider/file paths) are graded")
        return False
    if not all(isinstance(c, dict) and set(c) <= SAFE_CLUSTER_KEYS for c in clusters):
        print("  [INFO] kubeconfig rejected: unsupported cluster fields (e.g. proxy-url, certificate-authority path)")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as copy:
        yaml.safe_dump(data, copy)
    try:
        return cmd("kubectl", "--kubeconfig", copy.name, "cluster-info")[0]
    finally:
        pathlib.Path(copy.name).unlink(missing_ok=True)


def rescheduled(deploy: str, label: str, min_age_gap: int = 30) -> bool:
    """True when at least one Pod was recreated well after the Deployment (e.g. evicted by a drain).

    A cordon/drain/uncordon round-trip leaves nodes and replica counts exactly as seeded,
    so the end state alone cannot prove the work was done.
    """
    from datetime import datetime
    created = path(obj("deploy", deploy), "metadata", "creationTimestamp")
    good, raw = cmd("kubectl", "-n", NS, "get", "pods", "-l", f"app={label}", "-o", "json")
    if not created or not good:
        return False
    parse = lambda ts: datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    start = parse(created)
    return any((parse(p["metadata"]["creationTimestamp"]) - start).total_seconds() >= min_age_gap
               for p in json.loads(raw).get("items", []))


def no_taint(key: str) -> bool:
    good, out = cmd("kubectl", "get", "nodes", "-o", "json")
    return good and not any(t.get("key") == key for n in json.loads(out).get("items", []) for t in n.get("spec", {}).get("taints", []))


TASKS: dict[int, list[tuple[str, Any]]] = {
  1: [
    ("Pod web-pod spec and Ready", lambda: ready("pod", "web-pod") and image("pod", "web-pod") == "nginx:1.27" and path(obj("pod", "web-pod"), "metadata", "labels", "app") == "web"),
    ("Deployment frontend 3/3", lambda: ready("deploy", "frontend", 3) and image("deploy", "frontend") == "nginx:1.27"),
    ("Redis Pod and generated YAML", lambda: ready("pod", "cache-pod") and file_contains("day01-cache.yaml", "cache-pod", "redis:7")),
    ("Filtered frontend file", lambda: (ROOT / "answers/day01-frontend.txt").is_file() and sorted((ROOT / "answers/day01-frontend.txt").read_text().split()) == ["sample-front-a", "sample-front-b"]),
    ("All current Pod names exported", lambda: (ROOT / "answers/day01-pods.txt").is_file() and (lambda a: a == sorted(a) and a == sorted(item["metadata"]["name"] for item in json.loads(cmd("kubectl", "-n", NS, "get", "pods", "-o", "json")[1]).get("items", [])))((ROOT / "answers/day01-pods.txt").read_text().split())),
  ],
  2: [
    ("Store rolled back to 1.26; 4/4", lambda: ready("deploy", "store", 4) and image("deploy", "store") == "nginx:1.26" and path(obj("deploy", "store"), "metadata", "annotations", "deployment.kubernetes.io/revision") not in (None,"1")),
    ("ConfigMap/Secret injected into Pod", lambda: path(obj("cm", "app-config"), "data", "MODE") == "production" and bool(obj("secret", "app-secret")) and ready("pod", "config-test") and env_source("pod", "config-test", "MODE", "configmap", "app-config") and env_source("pod", "config-test", "TOKEN", "secret", "app-secret")),
    ("Required node affinity", lambda: ready("pod", "ssd-pod") and bool(path(obj("pod", "ssd-pod"), "spec", "affinity", "nodeAffinity", "requiredDuringSchedulingIgnoredDuringExecution"))),
    ("Toleration target and taint cleanup", lambda: ready("pod", "tolerant-pod") and any(t.get("key") == "dedicated" and t.get("value") == "exam" and t.get("effect") == "NoSchedule" for t in path(obj("pod", "tolerant-pod"), "spec", "tolerations", default=[])) and no_taint("dedicated")),
    ("Healthy deployment probes/limits", lambda: ready("deploy", "healthy-web", 2) and probe("healthy-web", "readinessProbe", 80) and probe("healthy-web", "livenessProbe", 80) and path(obj("deploy", "healthy-web"), "spec", "template", "spec", "containers", 0, "resources", "requests", "cpu") == "100m" and path(obj("deploy", "healthy-web"), "spec", "template", "spec", "containers", 0, "resources", "limits", "memory") == "128Mi"),
  ],
  3: [
    ("ClusterIP service with ready endpoints", lambda: svc("api-svc", {"app":"api"},8080,80) and endpoints("api-svc")),
    ("NodePort 30080", lambda: svc("frontend-nodeport",{"app":"frontend"},80,80,30080) and endpoints("frontend-nodeport")),
    ("DNS resolves from client, evidence saved", lambda: svc("database",{"app":"database"},80,80) and file_contains("day03-dns.txt", "database")),
    ("NetworkPolicy enforced: trusted yes, outsider no", lambda: policies("database-ingress",{"app":"database"},{"role":"frontend"}) and traffic("trusted","database") and traffic("outsider","database",False)),
    ("OPTIONAL Ingress+Gateway: manual functional test", None),
  ],
  4: [
    ("PV+PVC bound to static local volume", lambda: volume("data-claim", "500Mi") and path(obj("pvc","data-claim"),"spec","volumeName") == "cka-d04-local-pv"),
    ("Persistence after Pod recreation", lambda: has_mount("data-writer","data-claim","/data") and proof("data-writer","/data/proof.txt","hello-cka")),
    ("Dynamic claim mounted", lambda: volume("dynamic-claim","1Gi") and has_mount("dynamic-reader","dynamic-claim","/data")),
    ("Access modes and Filesystem", lambda: volume("mode-claim","200Mi") and "ReadWriteOnce" in path(obj("pvc","mode-claim"),"spec","accessModes",default=[]) and path(obj("pvc","mode-claim"),"spec","volumeMode") in (None,"Filesystem")),
    ("Retain: Released, re-bound, data kept", lambda: path(obj("pv","cka-d04-local-pv",None),"spec","persistentVolumeReclaimPolicy") == "Retain" and file_contains("day04-reclaim.txt", "Released") and proof("data-writer","/data/proof.txt","hello-cka")),
  ],
  5: [
    ("Control-plane discovery notes", lambda: file_contains("day05-cluster.txt","cka-14d")),
    ("Redacted kubeadm join command", lambda: file_contains("day05-join.txt", "kubeadm", "join") and not re.search(r"--token\s+[a-z0-9]{6}\.[a-z0-9]{16}", (ROOT / "answers/day05-join.txt").read_text())),
    ("Four static Pod summary", lambda: file_contains("day05-static-pods.txt", "kube-apiserver", "kube-controller-manager", "kube-scheduler", "etcd")),
    ("etcd snapshot validated [MANUAL]", None),
    ("VM kubeadm and restore [MANUAL]", None),
  ],
  6: [
    ("All worker nodes schedulable; app 3/3", lambda: all_nodes_ready() and ready("deploy","maintenance-app",3) and rescheduled("maintenance-app","maintenance-app")),
    ("Namespace pod-reader Role+RoleBinding", lambda: role_ok("auditor","list","delete","pods") and bool(obj("role","pod-reader")) and bool(obj("rolebinding","auditor-binding"))),
    ("Cluster node-reader RoleBinding", lambda: bool(obj("clusterrole","cka-d06-node-reader",None)) and bool(obj("clusterrolebinding","cka-d06-node-reader",None)) and bool(obj("sa","node-auditor")) and can("node-auditor","list","nodes",None) and not can("node-auditor","patch","nodes",None)),
    ("Helm chart deployed at 3 replicas", lambda: ready("deploy","mini-web",3) and bool(cmd("helm","-n",NS,"status","cka-d06-web")[0])),
    ("Kustomize overlay deployed", lambda: ready("deploy","overlay-web",2) and image("deploy","overlay-web") == "nginx:1.27"),
  ],
  7: [
    ("CrashLoopBackOff repaired", lambda: ready("pod","broken-app") and path(obj("pod","broken-app"),"status","containerStatuses",0,"restartCount",default=999) <= 2),
    ("Bad image repaired", lambda: ready("deploy","broken-image",1) and image("deploy","broken-image") == "nginx:1.27"),
    ("Pending CPU request reduced", lambda: ready("pod","pending-app") and path(obj("pod","pending-app"),"spec","containers",0,"resources","requests","cpu") == "100m"),
    ("Service selector repaired", lambda: svc("backend-svc",{"app":"backend"},80,80) and endpoints("backend-svc")),
    ("Probe corrected", lambda: ready("deploy","broken-probe",2) and probe("broken-probe","readinessProbe",80)),
  ],
  8: [
    ("Service targetPort repaired", lambda: svc("upstream-svc",{"app":"upstream"},80,80) and endpoints("upstream-svc")),
    ("DNS evidence", lambda: file_contains("day08-dns.txt","dns-backend-svc") and ready("deploy","dns-backend",1)),
    ("Pinned Pod on restored worker", lambda: ready("pod","pinned-app") and all_nodes_ready()),
    ("kubelet stop/restore exercise [MANUAL]", None),
    ("API server break/restore exercise [MANUAL]", None),
  ],
  9: [
    ("RollingUpdate Deployment 4/4", lambda: ready("deploy","payments",4) and image("deploy","payments") == "nginx:1.27" and path(obj("deploy","payments"),"spec","strategy","rollingUpdate","maxUnavailable") in (1,"1")),
    ("RBAC viewer config-reader", lambda: role_ok("viewer","list","delete","configmaps") and can("viewer","get","configmaps") and not can("viewer","get","secrets") and bool(obj("rolebinding","viewer-config"))),
    ("Database allow-only NetworkPolicy", lambda: policies("db-allow-api",{"app":"db"},{"role":"api"}) and traffic("role-client","db") and traffic("random-client","db",False)),
    ("2Gi claim mounted", lambda: volume("payments-data","2Gi") and has_mount("payments-writer","payments-data","/var/lib/data")),
    ("Service selector fixed", lambda: svc("bad-svc",{"app":"api"},80,80) and endpoints("bad-svc")),
  ],
  10: [
    ("Cluster admin snapshot/evidence [MANUAL]", None),
    ("Endpoints, image and policy", lambda: svc("backend-svc",{"app":"backend"},80,80) and endpoints("backend-svc") and ready("deploy","bad-image") and svc("bad-image-svc",{"app":"bad-image"},80,80) and policies("trusted-only",{"app":"backend"},{"role":"trusted"}) and traffic("trusted-client","backend-svc") and traffic("untrusted-client","backend-svc",False)),
    ("Workload with probe and ConfigMap", lambda: ready("deploy","mock-web",3) and image("deploy","mock-web") == "nginx:1.27" and probe("mock-web","readinessProbe",80) and env_source("deploy","mock-web","MODE","configmap","mock-config")),
    ("Role read-only and nodes ready", lambda: role_ok("mock-viewer","list","delete","pods") and bool(obj("role","mock-reader")) and all_nodes_ready() and file_contains("day10-maintenance.txt")),
    ("PVC storage and proof", lambda: volume("mock-data","1Gi") and has_mount("mock-writer","mock-data","/data") and proof("mock-writer","/data/proof.txt","mock-10")),
  ],
  11: [
    ("OOMKilled repaired with 512Mi limit", lambda: ready("pod","memory-hog") and path(obj("pod","memory-hog"),"spec","containers",0,"resources","limits","memory") == "512Mi"),
    ("Readiness corrected", lambda: ready("deploy","probe-failure",2) and probe("probe-failure","readinessProbe",80)),
    ("Service targetPort fixed", lambda: svc("web-svc",{"app":"web"},80,80) and endpoints("web-svc")),
    ("Fixed kubeconfig copy", lambda: learner_kubeconfig_works("day11-kubeconfig.yaml")),
    ("Scheduler fault drill [MANUAL]", None),
  ],
  12: [
    ("Admin snapshot and drain evidence [MANUAL]", None),
    ("Image/selector repaired + nodes healthy", lambda: ready("deploy","faulty-image") and image("deploy","faulty-image") == "nginx:1.27" and svc("payments-svc",{"app":"payments"},80,80) and endpoints("payments-svc") and all_nodes_ready()),
    ("NodePort and network policy", lambda: svc("payments-nodeport",{"app":"payments"},80,80,30080) and policies("payments-allow",{"app":"payments"},{"role":"allowed"}) and traffic("allowed-client","payments-svc") and traffic("net-client","payments-svc",False)),
    ("DaemonSet CronJob and ConfigMap", lambda: bool(obj("ds","log-agent")) and bool(obj("cronjob","daily-job")) and path(obj("cronjob","daily-job"),"spec","schedule") == "*/5 * * * *" and path(obj("cm","runtime-settings"),"data","MODE") == "test"),
    ("Backup claim mounted", lambda: volume("backup-claim","1Gi") and has_mount("backup-pod","backup-claim","/backup")),
  ],
  13: [
    ("Pods+Deployments sprint", lambda: all(ready("pod",n) for n in ("alpha","beta")) and ready("deploy","rapid-a",2) and ready("deploy","rapid-b",3)),
    ("Gateway service and policy", lambda: svc("gateway-svc",{"app":"gateway"},80,80) and endpoints("gateway-svc") and policies("gateway-allow",{"app":"gateway"},{"role":"tester"})),
    ("500Mi storage mounted", lambda: volume("speed-data","500Mi") and has_mount("speed-writer","speed-data","/data")),
    ("Read-only ConfigMap RBAC", lambda: role_ok("speed-auditor","list","delete","configmaps") and bool(obj("rolebinding","speed-binding"))),
    ("Broken rollout repaired", lambda: ready("deploy","broken-rollout") and image("deploy","broken-rollout") == "nginx:1.27"),
  ],
  14: [
    ("Cluster snapshot [MANUAL]", None),
    ("Billing, orders and logs", lambda: ready("deploy","billing") and image("deploy","billing") == "nginx:1.27" and svc("orders-svc",{"app":"orders"},80,80) and endpoints("orders-svc") and file_contains("day14-troubleshooting.txt")),
    ("Billing service and orders policy", lambda: svc("billing-svc",{"app":"billing"},8080,80) and endpoints("billing-svc") and policies("orders-allow",{"app":"orders"},{"role":"trusted"}) and traffic("trusted-client","orders-svc") and traffic("untrusted-client","orders-svc",False)),
    ("Final-web 3 replicas with Secret+probe", lambda: ready("deploy","final-web",3) and image("deploy","final-web") == "nginx:1.27" and env_source("deploy","final-web","TOKEN","secret","final-secret") and probe("final-web","readinessProbe",80)),
    ("Final proof stored", lambda: volume("final-claim","1Gi") and has_mount("final-writer","final-claim","/data") and proof("final-writer","/data/proof.txt","cka-final")),
  ],
}

POINTS = {10:[25,20,15,25,15],12:[25,30,20,15,10],14:[25,30,20,15,10]}
print(f"CKA Practice Day {DAY:02d} — {NS} (read-only checks)")
passed = failed = manual = earned = 0
for index,(label,fn) in enumerate(TASKS[DAY],start=1):
    pts = POINTS.get(DAY,[0]*5)[index-1]
    if fn is None:
        manual += 1
        print(f"  [MANUAL] {DAY:02d}.{index} {label}" + (f" ({pts} pts ungraded)" if pts else ""))
        continue
    try:
        result = bool(fn())
    except Exception as exc:
        print(f"  [WARN] checker exception: {exc}")
        result = False
    if result:
        passed += 1
        earned += pts
        print(f"  [PASS]   {DAY:02d}.{index} {label}" + (f" (+{pts})" if pts else ""))
    else:
        failed += 1
        print(f"  [FAIL]   {DAY:02d}.{index} {label}")
print(f"Summary: {passed} passed, {failed} failed, {manual} manual")
if DAY in POINTS:
    print(f"Auto-verified minimum: {earned}/100. Manually score the {manual} admin task(s) before claiming a full mock score.")
if failed:
    sys.exit(1)
