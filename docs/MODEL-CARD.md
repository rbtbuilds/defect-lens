# Defect Lens model card

Two CPU baselines inspect a controlled tabletop plate. The default aligned median difference model needs no network. The optional ResNet18 IMAGENET1K_V1 layer2 comparator normalizes ImageNet RGB channels without a 224 crop, keeps 256-square geometry and uses a seeded bank of at most 4,096 unit vectors. All revisions freeze validation calibration and file hashes; held-out test images never participate in preparation.

Original procedural fixtures are MIT licensed. Pretrained checkpoint origin: https://download.pytorch.org/models/resnet18-f37072fd.pth . The upstream filename checksum prefix is checked at download and the full SHA256 is recorded and checked in each model manifest. Torchvision code and pretrained training data have separate terms; this repository's MIT license does not relicense weights or ImageNet data. See https://github.com/pytorch/vision and https://www.image-net.org/ .

Current evidence: difference pipeline tests executed on original procedural images. Actual pretrained preparation and integration have run: layer2 yields 1,024 vectors with 128 channels, finite varied scores, verified checkpoint SHA256 and child exit before lease release. Held-out comparison is pending. No owned capture set has been supplied. No owned-photo metrics, industrial defect accuracy or customer impact is claimed.

The frozen decision cost is five missed defects to one false reject. Blur, clipping, framing and ECC alignment are demonstration heuristics and always force review. Human corrections preserve the original result and never become training labels automatically. Uncontrolled lighting, viewpoint, background, material or object changes invalidate this narrow demonstration.

Owned-photo gate: [capture recipe](CAPTURE-GUIDE.md) and [explicit no-run status](../reports/owned-capture-status.md). The validator checks declared rights, exclusive groups, human annotations, timestamps and mask coordinate provenance; it cannot establish photographic authenticity or consent. Its synthetic tests are software evidence only.
