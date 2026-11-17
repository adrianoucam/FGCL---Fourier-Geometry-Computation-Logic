"""Optional PyTorch adapters. No architecture/checkpoint assumptions."""
import numpy as np

def torch_probability_predictor(model,classes,device='cpu',image_size=224,normalize=True):
    import torch
    from PIL import Image
    from torchvision.transforms import functional as F
    model=model.to(device).eval()
    def predict(x):
        im=Image.fromarray((np.clip(x,0,1)*255).astype('uint8'))
        t=F.to_tensor(F.resize(im,[image_size,image_size]))
        if normalize:t=F.normalize(t,[.485,.456,.406],[.229,.224,.225])
        with torch.inference_mode():
            result=model(t.unsqueeze(0).to(device))
            logits=result.logits if hasattr(result,'logits') else result
            if isinstance(logits,(tuple,list)):logits=logits[0]
            if logits.ndim!=2 or logits.shape[1]!=len(classes):raise ValueError('model logits shape and classes mismatch')
            return torch.softmax(logits,dim=1)[0].detach().cpu().numpy()
    return predict

def convnext_tiny(num_classes,pretrained=False):
    """Factory only. No download by default; checkpoints must match architecture."""
    from torchvision.models import convnext_tiny,ConvNeXt_Tiny_Weights
    import torch
    model=convnext_tiny(weights=ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None)
    model.classifier[2]=torch.nn.Linear(model.classifier[2].in_features,num_classes)
    return model

def load_state_dict_strict(model,path):
    import torch
    state=torch.load(path,map_location='cpu',weights_only=True)
    if isinstance(state,dict) and 'state_dict' in state:state=state['state_dict']
    if isinstance(state,dict) and 'model_state_dict' in state:state=state['model_state_dict']
    model.load_state_dict(state,strict=True)
    return model
