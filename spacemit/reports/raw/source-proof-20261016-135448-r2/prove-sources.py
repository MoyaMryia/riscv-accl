#!/usr/bin/env python3
"""只读核验编译器来源、官方张量来源和重建结果。"""

import argparse
import hashlib
import importlib.util
import io
import json
import math
import struct
import subprocess
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEB_ORIGIN = "https://archive.spacemit.com/bianbu/pool/universe/g/gcc-14/"
DEB_PACKAGES = (
    ("gcc-14-riscv64-linux-gnu_14.2.0-4ubuntu2~24.04bb2_riscv64.deb", 29512878,
     "f4b8e008cbfc905d6d994c8a4968b4483d99acd4aa85fca343cff05306026d02", "gcc"),
    ("g++-14-riscv64-linux-gnu_14.2.0-4ubuntu2~24.04bb2_riscv64.deb", 16590580,
     "1809d9acc79cf617bb66206156fa004dff165d614f56879a6a17caf51242dd40", "g++"),
)
HF_ORIGIN = "https://hf-mirror.com/Qwen/Qwen3.5-4B/resolve/"
INPUT_SHA256 = {
    "model_lock": "13c19ea464d028091859ae6ee6d64592cbc6d64f8fe2ccbce3c5cd7b3229aab1",
    "extractor": "78ee9ad37747aecda9b5076c17113bbe672810a1c1b81298d52d7b4b711f7205",
    "assembler": "da10cd6faca26f7cb62c947e7a4a8f1546519b77a5c40e8326ee9541b44de408",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ranged_get(url, start, end, total):
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 206:
            raise ValueError(f"range response status is not 206: {response.status}")
        expected_header = f"bytes {start}-{end}/{total}"
        if response.headers.get("Content-Range") != expected_header:
            raise ValueError("range response Content-Range does not match request and source size")
        data = response.read(end - start + 2)
    if len(data) != end - start + 1:
        raise ValueError("range response length does not match request")
    return data


def read_hash(stream):
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def verify_compilers(root, compiler_root):
    results = {}
    for filename, expected_size, expected_sha, compiler in DEB_PACKAGES:
        url = DEB_ORIGIN + filename
        print(f"Download and check {filename}", flush=True)
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=120) as response:
            package_path = root / filename
            digest = hashlib.sha256()
            size = 0
            with package_path.open("xb") as target:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    digest.update(chunk)
                    target.write(chunk)
        if size != expected_size or digest.hexdigest() != expected_sha:
            raise ValueError(f"package size or SHA-256 mismatch: {filename}")
        print(f"Read {compiler} from package archive", flush=True)
        unpacked = subprocess.run(
            ["dpkg-deb", "--fsys-tarfile", str(package_path)],
            stdout=subprocess.PIPE, check=True
        ).stdout
        archive = tarfile.open(fileobj=io.BytesIO(unpacked), mode="r:*")
        member_name = f"./usr/bin/riscv64-linux-gnu-{compiler}-14"
        match = None
        for member in archive:
            if member.name in (member_name, member_name[2:]):
                if match is not None:
                    raise ValueError(f"duplicate compiler file in package: {member_name}")
                match = archive.extractfile(member)
                if match is None:
                    raise ValueError(f"compiler archive member is not a file: {member_name}")
                _, package_sha = read_hash(match)
        archive.close()
        if match is None:
            raise ValueError(f"compiler file is missing from package: {member_name}")
        installed = Path(compiler_root) / "usr/bin" / f"{compiler}-14"
        installed_sha = sha256_file(installed)
        if package_sha != installed_sha:
            raise ValueError(f"compiler hash mismatch: {installed}")
        results[compiler] = {
            "package": filename, "package_size": size, "package_sha256": expected_sha,
            "archive_path": member_name, "compiler_path": str(installed),
            "compiler_sha256": installed_sha,
        }
        print(f"Passed compiler check: {compiler}", flush=True)
    return results


def load_extractor(path):
    spec = importlib.util.spec_from_file_location("source_proof_extractor", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load extractor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EXPECTED


def extract_tensors(root, lock_path, extractor_path):
    lock = json.loads(Path(lock_path).read_text())
    model = lock["models"]["4B"]
    revision = model["official_revision"]
    repo = model["official_repo"]
    shards = model["safetensors"]
    sizes = {item["rfilename"]: item["size"] for item in shards}
    expected = load_extractor(extractor_path)
    print("Read official safetensors headers", flush=True)
    headers = {}
    for shard, total in sizes.items():
        first = ranged_get(HF_ORIGIN + revision + "/" + shard, 0, 7, total)
        header_length = struct.unpack("<Q", first)[0]
        if header_length > total - 8:
            raise ValueError(f"invalid safetensors header size: {shard}")
        raw = ranged_get(HF_ORIGIN + revision + "/" + shard, 8, 7 + header_length, total)
        headers[shard] = (json.loads(raw), 8 + header_length)

    locations = {}
    for shard, (header, data_start) in headers.items():
        for name in expected:
            if name in header:
                if name in locations:
                    raise ValueError(f"duplicate official tensor: {name}")
                info = header[name]
                shape = info["shape"]
                start, end = info["data_offsets"]
                if (info["dtype"] != "BF16" or not shape or
                        any(type(dimension) is not int or dimension <= 0 for dimension in shape) or
                        type(start) is not int or type(end) is not int or start < 0 or end < start or
                        math.prod(shape) * 2 != end - start or data_start + end > sizes[shard]):
                    raise ValueError(f"invalid BF16 tensor metadata: {name}")
                locations[name] = (shard, header[name], data_start)
    absent = set(expected) - set(locations)
    if absent:
        raise ValueError(f"official source is missing MTP tensors: {sorted(absent)}")

    tensor_dir = root / "mtp-tensors"
    tensor_dir.mkdir()
    metadata = {}
    range_records = {}
    for shard in sizes:
        selected = [(name, info, data_start) for name, (source_shard, info, data_start)
                    in locations.items() if source_shard == shard]
        if not selected:
            continue
        data_start = selected[0][2]
        low = min(info["data_offsets"][0] for _, info, _ in selected)
        high = max(info["data_offsets"][1] for _, info, _ in selected)
        absolute_start, absolute_end = data_start + low, data_start + high - 1
        print(f"Read MTP tensor range from {shard}", flush=True)
        payload = ranged_get(HF_ORIGIN + revision + "/" + shard,
                             absolute_start, absolute_end, sizes[shard])
        range_records[shard] = {"start": absolute_start, "end": absolute_end,
                                "bytes": len(payload)}
        for name, info, _ in selected:
            start, end = info["data_offsets"]
            blob = payload[start - low:end - low]
            target = tensor_dir / (name + ".bin")
            with target.open("xb") as stream:
                stream.write(blob)
            metadata[name] = {
                "dtype": "BF16", "shape": info["shape"], "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(), "file": str(target),
                "url": HF_ORIGIN + revision + "/" + shard,
                "range": {"start": absolute_start, "end": absolute_end},
            }
    with (tensor_dir / "meta.json").open("x") as stream:
        json.dump(metadata, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return {"revision": revision, "repo": repo, "shards": sizes,
            "ranges": range_records, "tensors": metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--model-lock", required=True, type=Path)
    parser.add_argument("--extractor", required=True, type=Path)
    parser.add_argument("--assembler", required=True, type=Path)
    parser.add_argument("--base-model", required=True, type=Path)
    parser.add_argument("--reference-model", required=True, type=Path)
    parser.add_argument("--compiler-root", required=True, type=Path)
    args = parser.parse_args()
    inputs = {}
    for name in (*INPUT_SHA256, "base_model", "reference_model"):
        path = getattr(args, name).resolve(strict=True)
        if not path.is_file():
            parser.error(f"input is not a file: {path}")
        digest = sha256_file(path)
        if name in INPUT_SHA256 and digest != INPUT_SHA256[name]:
            parser.error(f"input identity differs: {name}: {path}")
        inputs[name] = {"path": str(path), "sha256": digest, "bytes": path.stat().st_size}
    root = args.root
    root.mkdir(parents=True, exist_ok=False)

    print("Start compiler source proof", flush=True)
    compiler_result = verify_compilers(root, args.compiler_root)
    with (root / "compiler-result.json").open("x") as stream:
        json.dump(compiler_result, stream, indent=2, sort_keys=True)
        stream.write("\n")

    print("Start official tensor source proof", flush=True)
    tensor_result = extract_tensors(root, args.model_lock, args.extractor)

    output = root / "reproduced-4B-MTP.gguf"
    print("Run the assembler", flush=True)
    subprocess.run(["python3", str(args.assembler), str(args.base_model),
                    str(output), str(root / "mtp-tensors")], check=True)
    reproduced_sha = sha256_file(output)
    reference_sha = inputs["reference_model"]["sha256"]
    if reproduced_sha != reference_sha:
        raise ValueError("reproduced GGUF SHA-256 does not match reference model")
    print("Passed reproduced model hash comparison", flush=True)

    proof = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "compiler": compiler_result,
        "official_tensors": tensor_result,
        "reproduced_model": {"path": output.name, "bytes": output.stat().st_size,
                             "sha256": reproduced_sha},
        "reference_model": {"path": str(args.reference_model), "bytes": args.reference_model.stat().st_size,
                            "sha256": reference_sha},
        "model_hash_match": True,
    }
    with (root / "proof.json").open("x") as stream:
        json.dump(proof, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("Source proof completed", flush=True)


if __name__ == "__main__":
    main()
