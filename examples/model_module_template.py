"""Edit to reproduce the architecture used for YOUR checkpoint; do not assume this template matches it."""
from fgcl.adapters import convnext_tiny

def build_model(num_classes):
    return convnext_tiny(num_classes,pretrained=False)
