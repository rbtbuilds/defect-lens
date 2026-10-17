# Third-party materials

The [MIT licence](LICENSE) covers original application code, documentation and
procedural fixtures. It does not relicense the following materials.

## VisA photographs and annotations

VisA is by Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang and Onkar Dabeer,
described in [SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection
and Segmentation](https://arxiv.org/abs/2207.14315), 2022.

The [official repository](https://github.com/amazon-science/spot-diff) releases its
dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This permits
attributed reuse, including commercial use. Verified primary terms are the
`LICENSE-DATASET` and README at revision
`2a692ab575001cbde74d402d897a7286086c6199`. This is a dataset grant, separate from
the upstream code licence.

The development study downloads a small subset from the official public S3
archive. The acquisition evidence preserves the original licence, source split
CSV and hashes. Images are resized to 256 square, masks use nearest-neighbor
resizing and positive values become binary defects. This changes geometry and
annotation representation, not the source labels. Source photographs and masks
are not redistributed in this repository. Reports contain source paths,
hashes and derived measurements. No endorsement by the authors is implied.

Published metadata lacks physical object/session identities. Attribution and
permission to reuse photographs do not establish specimen independence or
validate this application's plate domain. See [the protocol](docs/PHOTO-PROTOCOL.md).

## Pretrained weights

The optional comparator uses the torchvision ResNet18 IMAGENET1K_V1 checkpoint
from [PyTorch](https://download.pytorch.org/models/resnet18-f37072fd.pth).
Torchvision's code terms and ImageNet's data terms remain independent of MIT.
The checkpoint is downloaded locally, identified by SHA256 and never uploaded.
See [the model card](docs/MODEL-CARD.md) and
[torchvision](https://github.com/pytorch/vision).
